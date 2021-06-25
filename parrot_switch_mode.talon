mode: user.parrot_switch
-
parrot(ah):
	user.switch_parrot_mode("parrot_mouse")
parrot(ee):
	key(f4)
	user.switch_parrot_mode("parrot_eyemouse")
parrot(ae):
	user.kingfisher_click(2)
	user.disable_parrot_modes()
parrot(pop):
	user.switch_parrot_mode("parrot_media")

parrot(cluck):
	mouse_click(0)
	
parrot(palate_click):
	user.disable_parrot_modes()