mode: user.parrot_media_fullscreen
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
	speech.enable()
	user.enable_hud()
	user.switch_parrot_mode("parrot_media")
parrot(finger_snap):
	mouse_move(1850, 950)
	mouse_click(0)

parrot(palate_click):
	key(space)
	key(f)
	speech.enable()
	user.enable_hud()
	user.enable_switching_parrot_mode()