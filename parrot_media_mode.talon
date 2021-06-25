mode: user.parrot_media
-
parrot(pop):
	key(space)
parrot(oo):
	key(mute)
parrot(generator:repeat):
	key(volup)
parrot(shush:repeat):
	key(voldown)
parrot(cluck):
	key(space)
	key(f)
	speech.disable()
	user.disable_hud()
	user.switch_parrot_mode("parrot_media_fullscreen")
parrot(finger_snap):
	mouse_move(1850, 950)
	mouse_click(0)
	
parrot(palate_click): 
	user.enable_switching_parrot_mode()