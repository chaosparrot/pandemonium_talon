from talon import Context, Module, actions, cron

parrot_modes = {
    "parrot_switch": "Switch mode that disables speech and lets us choose a noise mode",
    "parrot_mouse": "Enable simple parrot mouse for scrolling, dragging and clicking",
    "parrot_eyemouse": "Enables eyetracker mouse",
    "parrot_media": "Enables specific controls for media playing",
    "parrot_media_fullscreen": "Enables specific controls for media playing while fullscreen"   
}

ctx = Context()
mod = Module()
current_parrot_mode = ""
has_talon_hud_actions = True # Set this to True if you have talon_hud as it enables a bunch of niceties

for parrot_mode in parrot_modes.keys():
    mod.mode(parrot_mode)

parrot_switch_job = None
def switch_parrot_mode(mode):
    cron.cancel(parrot_switch_job)
    global current_parrot_mode
    global has_talon_hud_actions
    if current_parrot_mode != mode:
        if current_parrot_mode != "":
            actions.mode.disable(f"user.{current_parrot_mode}")
            if has_talon_hud_actions:
                actions.user.remove_status_icon("parrot_icon")
        actions.mode.enable(f"user.{mode}")
        current_parrot_mode = mode
        if has_talon_hud_actions:
            actions.user.add_status_icon("parrot_icon", current_parrot_mode, parrot_modes[current_parrot_mode])        

def disable_parrot_mode():
    global current_parrot_mode
    global parrot_modes
    
    cron.cancel(parrot_switch_job)
    actions.speech.enable()
    current_parrot_mode = ""
    for parrot_mode in parrot_modes.keys():
        actions.mode.disable(f"user.{parrot_mode}")
    if has_talon_hud_actions:
        actions.user.remove_status_icon("parrot_icon")
        

@mod.action_class
class Actions:

    def enable_switching_parrot_mode():
        """Enables the switching mode which will only be active for about one and a half seconds before reverting back to regular command mode if no noise was made"""
        global parrot_switch_job
        global current_parrot_mode
        switch_parrot_mode("parrot_switch")
        parrot_switch_job = cron.interval('1500ms', disable_parrot_mode)
        actions.speech.disable()

    def switch_parrot_mode(mode: str):
        """Switches the parrot mode around"""
        switch_parrot_mode(mode)
     
    def disable_parrot_modes():
        """Disables the current parrot mode"""
        disable_parrot_mode()