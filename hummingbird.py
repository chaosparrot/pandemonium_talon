from talon import actions, cron, Context, Module, ctrl
from typing import Callable, Tuple, TypedDict, Any
from dataclasses import dataclass, asdict
from talon.screen import Screen, main_screen
import time

class InputThrottler:
    """Interface used for throttling inputs"""
    
    def clear(self):
        """Clear internal state for throttling"""
        pass

    def should_throttle(self, ts: float, direction: str, lifecycle: str) -> bool:
        """Whether or not to throttle an action"""
        return False

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
        self.last_action = 0.0
        self.direction_start = 0.0
        self.direction_stop = 0.0
        self.last_duration = 0.0
        
    def should_throttle(self, ts: float, direction: str, lifecycle: str) -> bool:
        if (lifecycle == "start"):
            if self.last_duration < self.starting_throttle or ts - self.direction_stop > self.starting_throttle:
            	self.direction_start = ts
            print("BEGIN_THROTTLE")
            return True
        elif (lifecycle == "stop"):
            self.direction_stop = ts
            self.last_duration = self.direction_stop - self.direction_start
            
            print("STOP THROTTLE", self.last_duration, ts - self.last_duration, self.starting_throttle)
            return ts - self.direction_start > self.starting_throttle
        
        if (self.last_action + self.throttle) > ts or (ts - self.direction_start) < self.starting_throttle:
            print("THROTTLE")
            return True
        self.last_action = ts
        print("NO_THROTTLE")
        return False
    
@dataclass
class DirectionActions:
    cancel_type: str
    up: Callable[[float], None]
    left: Callable[[float], None]
    right: Callable[[float], None]
    down: Callable[[float], None]
    forward: Callable[[float], None]
    backward: Callable[[float], None]
    throttler: InputThrottler
    visualizer: Any = None

def noop_key(ts: float):
    pass

def print_key(key: str):
    return lambda ts: print("Pressed key " + key)

def action_key(action):
    return lambda ts: action()
    
def keypress_key(key):
    return lambda ts: actions.key(key)

def mouse_move_action(x_offset: float, y_offset: float):
    return lambda ts, x_offset=x_offset, y_offset=y_offset: actions.user.mouse_relative_move(x_offset, y_offset)


direction_exclusion_mono = "mono" # Cancels all directions when a new direction is set
direction_exclusion_diagonal = "opposite" # Cancels only the opposite direction when a new direction is set
class HummingBird:
    
    job = None
    current_directions = []
    directions = None
    
    def __init__(self):
        self.directions = DirectionActions(
        	"mono",
            keypress_key("up"),
            keypress_key("left"),
            keypress_key("right"),
            keypress_key("down"),
            action_key(actions.core.repeat),
            action_key(actions.edit.undo),
            FlatThrottler(0.05, 0.3)
        )
        
    def set_direction_actions(self, da: DirectionActions):
        self.directions = da
        
    def start_continuous_job(self):
        self.end_continuous_job()
        self.job = cron.interval("16ms", self.tick_directions)

    def tick_directions(self):
        ts = time.time()
        for direction in self.current_directions:
            if self.directions.throttler.should_throttle(ts, direction, ""):
                continue
            if direction == "up":
	            self.directions.up(ts)
            elif direction == "left":
                self.directions.left(ts)
            elif direction == "right":
                self.directions.right(ts)
            elif direction == "down":
                self.directions.down(ts)
        if self.directions.visualizer is not None:
            self.directions.visualizer.set_directions(self.current_directions)

    def end_continuous_job(self):
        cron.cancel(self.job)
        self.job = None
        self.directions.visualizer.set_directions([])        
		
    def set_direction(self, new_direction):
        if (self.directions.cancel_type == "mono"):
            self.current_directions = []
        elif (self.directions.cancel_type == "opposite"):
            if self.current_directions == "up" and "down" in self.current_directions:
                self.current_directions.remove("down")
            elif self.current_directions == "down" and "up" in self.current_directions:
                self.current_directions.remove("up")
            elif self.current_directions == "left" and "right" in self.current_directions:
                self.current_directions.remove("right")
            elif self.current_directions == "right" and "left" in self.current_directions:
                self.current_directions.remove("left")
        
        if new_direction not in self.current_directions:
            self.current_directions.append(new_direction)
        
        if self.directions.visualizer is not None:
            self.directions.visualizer.set_directions(self.current_directions)

    def clear_directions(self):
        self.current_directions = []
        self.directions.throttler.clear()
        if self.directions.visualizer is not None:
            self.directions.visualizer.set_directions(self.current_directions)

    def up(self, ts: float, set_directions=True, lifecycle=""):
        if set_directions:
            self.set_direction("up")
            if lifecycle == "stop" and self.directions.visualizer is not None:
                self.directions.visualizer.set_directions([])
        if not self.job and not self.directions.throttler.should_throttle(ts, "up", lifecycle):
            self.directions.up(ts)
    
    def left(self, ts: float, set_directions=True, lifecycle=""):
        if set_directions:
            self.set_direction("left")
            if lifecycle == "stop" and self.directions.visualizer is not None:
                self.directions.visualizer.set_directions([])
        if not self.job and not self.directions.throttler.should_throttle(ts, "left", lifecycle):
            self.directions.left(ts)
    
    def right(self, ts: float, set_directions=True, lifecycle=""):
        if set_directions:
            self.set_direction("right")
            if lifecycle == "stop" and self.directions.visualizer is not None:
                self.directions.visualizer.set_directions([])
        if not self.job and not self.directions.throttler.should_throttle(ts, "right", lifecycle):
            self.directions.right(ts)
        
    def down(self, ts: float, set_directions=True, lifecycle=""):
        if set_directions:
            self.set_direction("down")
            if lifecycle == "stop" and self.directions.visualizer is not None:
                self.directions.visualizer.set_directions([])
        if not self.job and not self.directions.throttler.should_throttle(ts, "down", lifecycle):
            self.directions.down(ts)
    
    def forward(self, ts: float):
        if len(self.current_directions) > 0:
            for direction in self.current_directions:
                if self.directions.throttler.should_throttle(ts, direction):
                    continue
            
                if direction == "up":
                    self.up(ts, set_directions=False)
                elif direction == "left":
                    self.left(ts, set_directions=False)
                elif direction == "right":
                    self.right(ts, set_directions=False)
                elif direction == "down":
                    self.down(ts, set_directions=False)
        else:
            self.directions.forward(ts)
            
    def backward(self, ts: float):
        if len(self.current_directions) > 0:
            for direction in self.current_directions:
                if self.directions.throttler.should_throttle(ts, direction):
                    continue
            
                if direction == "up":
                    self.down(ts, set_directions=False)
                elif direction == "left":
                    self.right(ts, set_directions=False)
                elif direction == "right":
                    self.left(ts, set_directions=False)
                elif direction == "down":
                    self.up(ts, set_directions=False)
        else:
            self.directions.backward(ts)
        
hb = HummingBird()

hummingbird_directions = {
    "arrows": DirectionActions(
    	"mono",
        keypress_key("up"),
        keypress_key("left"),
        keypress_key("right"),
        keypress_key("down"),
        action_key(actions.core.repeat),
        action_key(actions.edit.undo),
        FlatThrottler(0.1, 0.3),
    ),
	"arrows_word": DirectionActions(
	    "mono",
        keypress_key("up"),
        action_key(actions.edit.word_left),
        action_key(actions.edit.word_right),
        keypress_key("down"),
        action_key(actions.core.repeat),
        action_key(actions.edit.undo),
        FlatThrottler(0.1, 0.3)
    ),
	"select": DirectionActions(
	    "mono",
        action_key(actions.edit.extend_up),
        action_key(actions.edit.extend_left),
        action_key(actions.edit.extend_right),
        action_key(actions.edit.extend_down),
        action_key(actions.core.repeat),
        action_key(actions.edit.undo),
        FlatThrottler(0.1, 0.3)
    ),
	"select_word": DirectionActions(
		"mono",
        action_key(actions.edit.extend_up),
        action_key(actions.edit.extend_word_left),
        action_key(actions.edit.extend_word_right),
        action_key(actions.edit.extend_down),
        action_key(actions.core.repeat),
        action_key(actions.edit.undo),
        FlatThrottler(0.1, 0.3)
    ),    
    "cursor": DirectionActions(
        "mono",
        mouse_move_action(0, -6),
        mouse_move_action(-6, 0),
        mouse_move_action(6, 0),
        mouse_move_action(0, 6),
        action_key(actions.core.repeat),
        action_key(actions.edit.undo),
		FlatThrottler(0.001, 0.2),
    ),
    "jira": DirectionActions(
    	"mono",    	
        keypress_key("k"),
        keypress_key("p"),
        keypress_key("n"),
        keypress_key("j"),
        action_key(actions.core.repeat),
        action_key(actions.edit.undo),
        FlatThrottler(0.1, 0.3)
    )
}

ctx = Context()
mod = Module()
mod.tag("humming_bird", desc="Tag whether or not humming bird should be used")
mod.tag("humming_bird_overrides", desc="Tag to override knausj commands to interlace humming bird overrides in them")

@mod.action_class
class Actions:
                
    def hummingbird_up(ts: float, mode: str = "stop"):
        """Activate the action related to the up direction of the humming bird"""
        global hb
        hb.up(ts, lifecycle=mode)
                
    def hummingbird_left(ts: float, mode: str = "stop"):
        """Activate the action related to the left direction of the humming bird"""
        global hb
        hb.left(ts, lifecycle=mode)
                
    def hummingbird_right(ts: float, mode: str = "stop"):
        """Activate the action related to the right direction of the humming bird"""
        global hb
        hb.right(ts, lifecycle=mode)
        
    def hummingbird_down(ts: float, mode: str = "stop"):
        """Activate the action related to the down direction of the humming bird"""
        global hb
        hb.down(ts, lifecycle=mode)
        
    def hummingbird_forward(ts: float):
        """Repeats the current directions, or repeats the last command"""
        global hb
        hb.forward(ts)
        
    def hummingbird_backward(ts: float):
        """Reverses the current directions, or undoes the last edit"""
        global hb
        hb.backward(ts)
        
    def hummingbird_continuous():
        """Starts a continuous job that triggers the directions at 60Hz"""
        global hb
        hb.start_continuous_job()
        
    def hummingbird_stop():
        """Ends the continuous job"""
        global hb
        hb.end_continuous_job()
        
    def hummingbird_clear():
        """Clears all current directions"""
        global hb
        hb.clear_directions()
        
    def hummingbird_set(type: str):
        """Sets the hummingbird control type"""
        global hb, hummingbird_directions
        hb.set_direction_actions(hummingbird_directions["arrows"] if type not in hummingbird_directions else hummingbird_directions[type])
        
    def mouse_relative_move(x_offset: float, y_offset: float):
        """Moves the mouse in the given direction relative to the current cursor position"""
        x, y = ctrl.mouse_pos()
        ctrl.mouse_move(x + x_offset, y + y_offset) 
