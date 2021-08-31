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

# Only triggers actions that do not have any clean up actions related to them
def should_trigger_discrete(event):
    return event < HummingEvent.STOP

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
        self.last_action = 0.0
        self.direction_start = 0.0
        self.direction_stop = 0.0
        self.last_duration = 0.0
        
    def determine_event(self, ts: float, direction: str, event: HummingEvent) -> HummingEvent:
        """Determine the event for the given direction given the current throttling state"""    
        # TODO PROPER STATE SENDING BASED ON STARTING THROTTLE W/R/T FIRST REPEAT
        
        # If a starting throttle as been set
        # We want to make sure the starting event does not get activated until later
        if (event == HummingEvent.START):
            if self.last_duration < self.starting_throttle or ts - self.direction_stop > self.starting_throttle:
                self.direction_start = ts
                self.last_action = ts
                return event

            return HummingEvent.THROTTLED
            
        # Stop event is special as it can activate a discrete action if it happens
        # Before the starting threshold has been reached
        elif (event == HummingEvent.STOP):
            self.direction_stop = ts
            self.last_duration = self.direction_stop - self.direction_start
            
            if self.starting_throttle > 0.0:
                return HummingEvent.THROTTLED if ts - self.direction_start > self.starting_throttle else HummingEvent.DISCRETE
            else:
                return event
        
        # For all the repeat events, do throttle checking regularly
        if (self.last_action + self.throttle) > ts or (ts - self.direction_start) < self.starting_throttle:
            return HummingEvent.THROTTLED
        
        self.last_action = ts
        
        return event

@dataclass
class DirectionActions2:
    up: Callable[[float], None]
    left: Callable[[float], None]
    right: Callable[[float], None]
    down: Callable[[float], None]
    throttler: InputThrottler

def print_key(key: str):
    return lambda ts, event: print("Pressed key " + key + " on event " + str(event))

class HummingBird2:
    paused = False
    job = None
    directions = []
    
    direction_actions = None
    exclusion_strategy = HummingExclusionStrategy.MONO
    
    def __init__(self):
        self.direction_actions = DirectionActions2(
            print_key("up"),
            print_key("left"),
            print_key("right"),
            print_key("down"),
            FlatThrottler(0.1)
        )
        
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
        if direction == "up":
            return self.direction_actions.down
        elif direction == "left":
            return self.direction_actions.right
        elif direction == "right":
            return self.direction_actions.left
        elif direction == "down":
            return self.direction_actions.up
        
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
        else:
            self.remove_direction(new_direction, ts)
        
    # TODO THROTTLE
    def add_direction(self, direction, ts):
        if direction not in self.directions:
            event = self.direction_actions.throttler.determine_event(ts, direction, HummingEvent.START)
            self.get_action_by_direction(direction)(ts, event)
            self.directions.append(direction)
            
    def repeat_direction(self, direction, ts):
        if direction in self.directions:
            event = self.direction_actions.throttler.determine_event(ts, direction, HummingEvent.REPEAT)
            self.get_action_by_direction(direction)(ts, event)
            
    def remove_direction(self, direction, ts):
        if direction in self.directions:
            event = self.direction_actions.throttler.determine_event(ts, direction, HummingEvent.STOP)        
            self.get_action_by_direction(direction)(ts, event)
            self.directions.remove(direction)

    def exclude_directions(self, direction: str, ts):
        directions_to_clear = []
        if self.exclusion_strategy == HummingExclusionStrategy.MONO:
            directions_to_clear = [x for x in self.directions if x != direction]
        
        for excluded_direction in directions_to_clear:
            self.get_action_by_direction(direction)(ts, HummingEvent.STOP)
            self.directions.remove(excluded_direction)

    def clear_directions(self):
        self.update_directions(HummingEvent.STOP)
        self.directions = []

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
                self.get_action_by_direction(direction)(ts, HummingEvent.REPEAT)
            
    def backward(self, ts: float):
        if len(self.current_directions) > 0:
            for direction in self.current_directions:
                self.get_action_by_opposite_direction(direction)(ts, HummingEvent.REPEAT)

mod = Module()
hb = HummingBird2()

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

    def hummingbird2_clear():
        """Clears all current directions"""
        global hb
        hb.clear_directions()