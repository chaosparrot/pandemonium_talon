mode: command
-
tag(): user.humming_bird
tag(): user.humming_bird_overrides

parrot(call_bell):
	speech.disable()
	mode.disable("noise")

parrot(cluck):
	mouse_click(0)
parrot(palate_click):
	user.enable_switching_parrot_mode()
	
falcon fly:
	key(f4)
	user.switch_parrot_mode("parrot_eyemouse")

humming fly:
	key(f4)
	user.switch_parrot_mode("parrot_mouse")
	user.hummingbird_set("cursor")
	
pidgeon fly:
	speech.disable()
	user.switch_parrot_mode("parrot_media")
	
parrot(gluck):
	edit.cut()
parrot(whistle):
	edit.paste()
parrot(pop):
	key(backspace)
	
parrot(chopper):
	user.woodpecker_start(ts)
parrot(chopper:repeat):
	user.woodpecker_drill(ts)
parrot(chopper:stop):
	user.woodpecker_stop(ts)
	