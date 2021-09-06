from talon import actions, cron, Context, Module, ctrl
from typing import Callable, Tuple, TypedDict, Any
from dataclasses import dataclass, asdict
from talon.screen import Screen, main_screen
import time
from enum import Enum

class HummingEvent(Enum):
    DISCRETE = 0 # Discrete noise - Used when a noise ends within the starting threshold
    # Before continuous noises are detected, so we can perform a full action
    
    START = 1 # Continuous noise start - Used for starting up actions
    REPEAT = 2 # Continuous noise repeat - Used for repeating actions
    STOP = 3 # Continuous noise end - Used for handling clean up after a change of directions
    
    THROTTLED = 4 # Action is throttled and should not execute

class HummingExclusionStrategy(Enum):
    MONO = 0 # Single direction can be activate at the same time
    OPPOSITE = 1 # Excludes directions only opposite of one another

class InputThrottler:
    """Interface used for throttling inputs"""
    
    def clear(self):
        """Clear internal state for throttling"""
        pass

    def determine_event(self, ts: float, direction: str, event: HummingEvent) -> HummingEvent:
        """Determine the event for the given direction given the current throttling state"""
        return event

class FlatThrottler(InputThrottler):
    """Class used for throttling all directions equally"""
    throttle: float
    starting_throttle: float
    last_action: float
    
    # Used for grace periods of discrete vs continuous
    direction_start: float
    direction_stop: float
    last_duration: float
    
    def __init__(self, throttle=0.000, starting_throttle=None):
        self.throttle = throttle
        self.starting_throttle = 0.0 if starting_throttle is None else starting_throttle
        self.clear()

    def clear(self):
        self.last_action_dir = ""
        self.last_action = 0.0
        self.direction_start = 0.0
        self.direction_stop = 0.0
        self.last_duration = 0.0
        
    def determine_event(self, ts: float, direction: str, event: HummingEvent) -> HummingEvent:
        """Determine the event for the given direction given the current throttling state"""    
        
        # If a starting throttle as been set
        # We want to make sure the starting event does not get activated until later
        if (event == HummingEvent.START):
            if self.last_duration < self.starting_throttle or ts - self.direction_stop > self.starting_throttle:
                self.direction_start = ts
                self.last_action = ts
                
                if self.starting_throttle > 0:
                    return HummingEvent.THROTTLED
                else:
                    self.last_action_dir = direction
                    return event
            
            if self.starting_throttle > 0:            
                return HummingEvent.THROTTLED
            
        # Stop event is special as it can activate a discrete action if it happens
        # Before the starting threshold has been reached
        elif (event == HummingEvent.STOP):
            self.last_action_dir = ""        
            self.direction_stop = ts
            self.last_duration = self.direction_stop - self.direction_start
            
            if self.starting_throttle > 0.0:
                return HummingEvent.STOP if ts - self.direction_start > self.starting_throttle else HummingEvent.DISCRETE
            else:
                return event
        
        # For all the repeat events, do throttle checking regularly
        if (self.last_action + self.throttle) > ts and self.throttle > 0 or (ts - self.direction_start) < self.starting_throttle:
            return HummingEvent.THROTTLED
        
        self.last_action = ts
        
        # In case we are dealing with a starting throttle
        # The actual start is delayed by the throttle
        # So we override the repeat event with a start event
        if self.last_action_dir == "" and ts - self.direction_start >= self.starting_throttle:
            self.last_action_dir = direction
            event = HummingEvent.START            
        
        return event

class DirectionVisualizer:
    enabled = True
    direction = "top"

    def set_directions(self, directions, enabled=True, blink=False):
        direction = ""        
        if len(directions) > 0:
            if "up" in directions:
               direction += "top"
            elif "down" in directions:
               direction += "bottom"
            if "left" in directions:
               direction += "left"
            elif "right" in directions:
               direction += "right"
        
        # Only visualize a change
        if enabled is not self.enabled or direction is not self.direction:
            self.enabled = enabled
            self.direction = direction if direction != "" else self.direction
            self.visualize(blink)

    def visualize(self, blink):
        opacity = "FF" if self.enabled else "77"
        colour = "777777" + opacity
        
        activated = 1 if blink else 0

        if self.direction == "top":
            actions.user.hud_add_ability("movement", "top", colour, 1, activated, 0, -1)
        elif self.direction == "topleft":
            actions.user.hud_add_ability("movement", "topleft", colour, 1, activated, 2, 2)
        elif self.direction == "topright":
            actions.user.hud_add_ability("movement", "topright", colour, 1, activated, -2, 2)
        elif self.direction == "left":
            actions.user.hud_add_ability("movement",  "left", colour, 1, activated, -2, 0)
        elif self.direction == "right":
            actions.user.hud_add_ability("movement", "right", colour, 1, activated, 2, 0)
        elif self.direction == "bottomleft":
            actions.user.hud_add_ability("movement", "bottomleft", colour, 1, activated, 2, -2)
        elif self.direction == "bottomright":
            actions.user.hud_add_ability("movement", "bottomright", colour, 1, activated, -2, -2)
        elif self.direction == "bottom":
            actions.user.hud_add_ability("movement", "bottom", colour, 1, activated, 0, 2)


@dataclass
class DirectionActions:
    up: Callable[[float], None]
    left: Callable[[float], None]
    right: Callable[[float], None]
    down: Callable[[float], None]
    throttler: InputThrottler

# Only triggers actions that do not have any clean up actions related to them
def should_trigger_discrete(event):
    return event.value < HummingEvent.STOP.value

def print_key(key: str):
    return lambda ts, event: print("Pressed key " + key + " on event " + str(event))

def action_key(action):
    return lambda ts, event: action() if should_trigger_discrete(event) else 1
    
def keypress_key(key):
    return lambda ts, event: actions.key(key) if should_trigger_discrete(event) else 1

def mouse_move_action(x_offset: float, y_offset: float):
    return lambda ts, event, x_offset=x_offset, y_offset=y_offset: actions.user.mouse_relative_move(x_offset, y_offset) \
        if should_trigger_discrete(event) else 1

def keyhold_key(key):
    return lambda ts, event: actions.key(key + ":down") if event == HummingEvent.START else \
        actions.key(key + ":up") if event == HummingEvent.STOP else 1

class HummingBird:
    paused = False
    job = None
    directions = []
    visualizer = None
    
    direction_actions = None
    exclusion_strategy = HummingExclusionStrategy.OPPOSITE
    
    def __init__(self, visualizer: DirectionVisualizer):
        self.visualizer = visualizer
        self.direction_actions = DirectionActions(
            print_key("up"),
            print_key("left"),
            print_key("right"),
            print_key("down"),
            FlatThrottler(0.0, 0.0)            
        )
            
    def set_direction_actions(self, da: DirectionActions):
        self.direction_actions = da

    def get_action_by_direction(self, direction):
        if direction == "up":
            return self.direction_actions.up
        elif direction == "left":
            return self.direction_actions.left
        elif direction == "right":
            return self.direction_actions.right
        elif direction == "down":
            return self.direction_actions.down
    
    def get_action_by_opposite_direction(self, direction):
        opposite_direction = get_opposite_direction(direction)
        return get_action_by_direction(opposite_direction)
            
    def get_opposite_direction(self, direction):
        if direction == "up":
            return "down"
        elif direction == "left":
            return "right"
        elif direction == "right":
            return "left"
        elif direction == "down":
            return "up"    
        
    # Continuous action triggers
    def start_continuous_job(self):
        ts = time.time()    
        if self.paused:
            self.update_directions(ts, HummingEvent.START)
            self.paused = False
            
        if not self.job:
            self.job = cron.interval("16ms", self.tick_directions)

    def pause_continuous_job(self):
        ts = time.time()
        if self.job:
            self.paused = True
            self.update_directions(ts, HummingEvent.STOP)
            
    def end_continuous_job(self):
        ts = time.time()        
        if self.job:
            if not self.paused:
                self.update_directions(ts, HummingEvent.STOP)        
            
            self.paused = False
            cron.cancel(self.job)
            self.job = None
            
    def tick_directions(self):
        ts = time.time()
        if not self.paused:
            self.update_directions(ts, HummingEvent.REPEAT)

    # Update all the current directions with the given event
    def update_directions(self, ts, event: HummingEvent):
        for direction in self.directions:
            new_event = self.direction_actions.throttler.determine_event(ts, direction, event)
            self.get_action_by_direction(direction)(ts, new_event)
            
    def activate_direction(self, new_direction, ts, lifecycle):
        self.exclude_directions(new_direction, ts)
        
        if lifecycle == "start":
            self.add_direction(new_direction, ts)
        elif lifecycle == "repeat" and not self.job:
            self.repeat_direction(new_direction, ts)
        elif lifecycle == "stop" and not self.job:
            self.remove_direction(new_direction, ts)
        
    def add_direction(self, direction, ts):
        if direction not in self.directions:
            event = self.direction_actions.throttler.determine_event(ts, direction, HummingEvent.START)
            self.get_action_by_direction(direction)(ts, event)
            self.directions.append(direction)
            self.visualizer.set_directions(self.directions, event == HummingEvent.START)
            
    def repeat_direction(self, direction, ts):
        if direction in self.directions:
            event = self.direction_actions.throttler.determine_event(ts, direction, HummingEvent.REPEAT)
            self.get_action_by_direction(direction)(ts, event)
            if event == HummingEvent.REPEAT:
                self.visualizer.set_directions(self.directions)
            
    def remove_direction(self, direction, ts):
        if direction in self.directions:
            event = self.direction_actions.throttler.determine_event(ts, direction, HummingEvent.STOP)        
            self.get_action_by_direction(direction)(ts, event)            
            self.directions.remove(direction)
            self.visualizer.set_directions(self.directions, False, event != HummingEvent.STOP)

    def exclude_directions(self, direction: str, ts):
        directions_to_clear = []
        if self.exclusion_strategy == HummingExclusionStrategy.MONO:
            directions_to_clear = [x for x in self.directions if x != direction]
        elif self.exclusion_strategy == HummingExclusionStrategy.OPPOSITE:
            directions_to_clear = [x for x in self.directions if x == self.get_opposite_direction(direction)]
        
        for excluded_direction in directions_to_clear:
            self.get_action_by_direction(excluded_direction)(ts, HummingEvent.STOP)
            self.directions.remove(excluded_direction)

    def clear_directions(self, directions: list[str] = None):
        ts = time.time()
        
        if directions == None:
            directions = ["up", "left", "right", "down"]
        for direction in directions:
            self.remove_direction(direction, ts)
        self.visualizer.set_directions(self.directions)

    # Direction actions
    def up(self, ts: float, lifecycle: str):
        self.activate_direction("up", ts, lifecycle)

    def left(self, ts: float, lifecycle: str):
        self.activate_direction("left", ts, lifecycle)
    
    def right(self, ts: float, lifecycle: str):
        self.activate_direction("right", ts, lifecycle)

    def down(self, ts: float, lifecycle: str):
        self.activate_direction("down", ts, lifecycle)
            
    def forward(self, ts: float):
        if len(self.directions) > 0:
            for direction in self.directions:
                event = self.direction_actions.throttler.determine_event(ts, direction, HummingEvent.REPEAT)
                self.get_action_by_direction(direction)(ts, event)
            
    def backward(self, ts: float):
        if len(self.current_directions) > 0:
            for direction in self.current_directions:
                event = self.direction_actions.throttler.determine_event(ts, direction, HummingEvent.REPEAT)            
                self.get_action_by_opposite_direction(direction)(ts, event)

hummingbird_directions = {
    "arrows": DirectionActions(
        keypress_key("up"),
        keypress_key("left"),
        keypress_key("right"),
        keypress_key("down"),
        FlatThrottler(0.1, 0.3),
    ),
	"arrows_word": DirectionActions(
        keypress_key("up"),
        action_key(actions.edit.word_left),
        action_key(actions.edit.word_right),
        keypress_key("down"),
        FlatThrottler(0.1, 0.3)
    ),
	"select": DirectionActions(
        action_key(actions.edit.extend_up),
        action_key(actions.edit.extend_left),
        action_key(actions.edit.extend_right),
        action_key(actions.edit.extend_down),
        FlatThrottler(0.1, 0.3)
    ),
	"select_word": DirectionActions(
        action_key(actions.edit.extend_up),
        action_key(actions.edit.extend_word_left),
        action_key(actions.edit.extend_word_right),
        action_key(actions.edit.extend_down),
        FlatThrottler(0.1, 0.3)
    ),    
    "cursor": DirectionActions(
        mouse_move_action(0, -6),
        mouse_move_action(-6, 0),
        mouse_move_action(6, 0),
        mouse_move_action(0, 6),
		FlatThrottler(0.001, 0.2),
    ),
    "jira": DirectionActions(
        keypress_key("k"),
        keypress_key("p"),
        keypress_key("n"),
        keypress_key("j"),
        FlatThrottler(0.1, 0.3)
    ),
    "wasd": DirectionActions(
        keyhold_key("w"),
        keyhold_key("a"),
        keyhold_key("d"),
        keyhold_key("s"),
        FlatThrottler(0.0, 0.0),
    ),
    "log": DirectionActions(
        print_key("up"),
        print_key("left"),
        print_key("right"),
        print_key("down"),
        FlatThrottler(0.0, 0.0)
    )
}

ctx = Context()
mod = Module()
mod.tag("humming_bird", desc="Tag whether or not humming bird should be used")
mod.tag("humming_bird_overrides", desc="Tag to override knausj commands to interlace humming bird overrides in them")
hb = HummingBird(DirectionVisualizer())

@mod.action_class
class Actions:
                
    def hummingbird2_up(ts: float, lifecycle: str = "stop"):
        """Activate the action related to the up direction of the humming bird"""
        global hb
        hb.up(ts, lifecycle)
                
    def hummingbird2_left(ts: float, lifecycle: str = "stop"):
        """Activate the action related to the left direction of the humming bird"""
        global hb
        hb.left(ts, lifecycle)
                
    def hummingbird2_right(ts: float, lifecycle: str = "stop"):
        """Activate the action related to the right direction of the humming bird"""
        global hb
        hb.right(ts, lifecycle)
        
    def hummingbird2_down(ts: float, lifecycle: str = "stop"):
        """Activate the action related to the down direction of the humming bird"""
        global hb
        hb.down(ts, lifecycle)
        
    def hummingbird2_forward(ts: float):
        """Repeats the current directions, or repeats the last command"""
        global hb
        hb.forward(ts)
        
    def hummingbird2_backward(ts: float):
        """Reverses the current directions, or undoes the last edit"""
        global hb
        hb.backward(ts)
        
    def hummingbird2_continuous():
        """Starts a continuous job that triggers the directions at 60Hz"""
        global hb
        hb.start_continuous_job()
                
    def hummingbird2_pause():
        """Pauses the continuous job, but does not clear the directions"""
        global hb
        return hb.pause_continuous_job()
        
    def hummingbird2_stop():
        """Ends the continuous job"""
        global hb
        hb.end_continuous_job()

    def hummingbird2_clear(directions: str = None):
        """Clears all or some of the current directions"""
        global hb
        clear_directions = directions
        if directions == "horizontal":
            clear_directions = ["left", "right"]
        elif directions == "vertical":
            clear_directions = ["up", "down"]
        hb.clear_directions(clear_directions)
        
    def hummingbird2_set(type: str):
        """Sets the hummingbird control type"""
        global hb, hummingbird_directions
        hb.set_direction_actions(hummingbird_directions["arrows"] if type not in hummingbird_directions else hummingbird_directions[type])
        
    def add_noise_log(action: str, noise: str):
        """Add a log visualizing the action and the noise"""
        actions.user.hud_add_log("command", "<*" + action + "/> «" + noise + "»")
