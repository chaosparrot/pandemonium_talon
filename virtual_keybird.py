from talon import actions, cron, Context, Module, ctrl
from typing import Callable, Tuple, TypedDict
from dataclasses import dataclass, asdict
from talon.screen import Screen, main_screen

@dataclass
class GridKeys:
    topleft: Callable[[float], None]
    topmiddle: Callable[[float], None]
    topright: Callable[[float], None]
    centerleft: Callable[[float], None]
    centermiddle: Callable[[float], None]
    centerright: Callable[[float], None]
    bottomleft: Callable[[float], None]
    bottommiddle: Callable[[float], None]
    bottomright: Callable[[float], None]

def noop_key(ts: float):
    pass

def print_key(key: str):
    return lambda ts: print("Pressed key " + key)

def action_key(action):
    return lambda ts: action()
    
def keypress_key(key):
    return lambda ts: actions.key(key)

class VirtualKeybird:
    screen: Screen
    
    def __init__(self):
        keyboard = GridKeys(
            noop_key, noop_key, noop_key,
            noop_key, noop_key, noop_key,
            noop_key, noop_key, noop_key
        )
        self.screen = main_screen()
        self.keyboard = asdict(keyboard)

    def press(self, ts: float):
        """Press one of the defined keys """
        key_cb = self.find_key(ctrl.mouse_pos())
        key_cb(ts)
        
    def find_key(self, coord: Tuple[int, int]):
        """Find the key to press based on the given screen position"""
        width = self.screen.width
        height = self.screen.height
        segment_width = width / 3
        segment_height = height / 3
        
        x = "left"
        y = "top"
        if coord[0] > segment_width:
            x = "middle" if coord[0] < segment_width * 2 else "right"
        if coord[1] > segment_height:
            y = "center" if coord[1] < segment_height * 2 else "bottom"
        return self.keyboard[y+x]

    def set_keyboard(self, kb: GridKeys):
        """Set the current keyboard"""
        self.keyboard = asdict(kb)
        
vkb = VirtualKeybird()
debug_keyboard = GridKeys(
    print_key("topleft"), print_key("topmiddle"), print_key("topright"),
    print_key("centerleft"), print_key("centermiddle"), print_key("centerright"),
    print_key("bottomleft"), print_key("bottommiddle"), print_key("bottomright")
)

navigation_keyboard = GridKeys(
    action_key(actions.app.tab_previous), keypress_key("alt-tab"), action_key(actions.app.tab_next),
    action_key(actions.app.tab_previous), keypress_key("alt-tab"), action_key(actions.app.tab_next),
    action_key(actions.app.tab_previous), keypress_key("alt-tab"), action_key(actions.app.tab_next)
)
vkb.set_keyboard(navigation_keyboard)

ctx = Context()
mod = Module()
@mod.action_class
class Actions:
                
    def press_virtual_keybird_key(ts: float):
        """Activate the actoin related to the virtual keyboard key mapped on the main screen"""
        global vkb
        vkb.press(ts)