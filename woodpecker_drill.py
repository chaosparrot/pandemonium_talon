from talon import actions, Context, Module, ctrl
from typing import Callable

class NoiseActionRepeater:
    starting_ts: float = 0.0
    count: int = 0
    cb: Callable[[float], None]
    
    def __init__(self):
        self.cb = lambda ts: None
    
    def set_callback(self, cb: Callable):
        self.cb = cb
        
    def start_drill(self, ts: float):
        self.starting_ts = ts
        self.count = 1
        self.cb(ts)
        
    def drill_update(self, ts: float):
        """Triggers at specific time slots to allow a skilled user to time the amount of repeats"""
        duration_ms = ( ts - self.starting_ts ) * 1000
        if duration_ms < 200 and self.count <= 1:
            pass
        elif duration_ms > 200 and duration_ms < 350 and self.count <= 1:
            self.cb(ts)
            self.count += 1
        elif duration_ms > 350 and duration_ms < 500 and self.count <= 2:
            self.cb(ts)
            self.count += 1
        elif duration_ms > 500 and duration_ms < 700 and self.count <= 3:
            self.cb(ts)
            self.count += 1
        elif duration_ms > 700 and duration_ms < 900 and self.count <= 3:
            self.cb(ts)
            self.count += 1
        elif duration_ms > 1000:
            expected_count = 4 + ( ( duration_ms - 1000 ) / 50 )
            if expected_count != self.count:
                self.cb(ts)
                self.count += 1
        
    def stop_drill(self, ts: float):
        self.starting_ts = 0.0
        self.count = 0

actionRepeater = NoiseActionRepeater()
actionRepeater.set_callback(lambda x: actions.core.repeat_command(1))

ctx = Context()
mod = Module()
@mod.action_class
class Actions:

    def woodpecker_start(ts: float):
        """Starts the tapered action repeater"""
        actionRepeater.start_drill(ts)
        
    def woodpecker_drill(ts: float):
        """Updates the tapered action repeater with a timestamp which possibly triggers the action"""
        actionRepeater.drill_update(ts)
        
    def woodpecker_stop(ts: float):
        """Stops drilling"""
        actionRepeater.stop_drill(ts)