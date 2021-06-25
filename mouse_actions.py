from talon import actions, Context, Module, ctrl
from talon_plugins import eye_mouse, eye_zoom_mouse
from talon_plugins.eye_mouse import config, toggle_camera_overlay, toggle_control

ctx = Context()
mod = Module()
@mod.action_class
class Actions:

    def kingfisher_click(times: int):
        """Activates the eyetracker for a brief second to move the mouse, then clicks the targeted area N times, and returns the mouse back to where it was"""
        pos = ctrl.mouse_pos()
        
        actions.user.enable_tracker_mouse()
        actions.sleep(0.05)
        actions.user.disable_tracker_mouse()
        
        for i in range(times):
            ctrl.mouse_click(0)
        ctrl.mouse_move(pos[0], pos[1])

    def enable_tracker_mouse():
        """Enables both eyetracking and the zoom mouse"""
        actions.key("f4")
        
    def disable_tracker_mouse():
        """Disables eyetracking and the zoom mouse"""
        actions.key("f4")