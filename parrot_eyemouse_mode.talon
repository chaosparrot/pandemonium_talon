mode: user.parrot_eyemouse
-
parrot(shush):
	user.power_momentum_scroll_down()
	user.power_momentum_start(ts, 2.0)
parrot(shush:repeat):
	user.power_momentum_add(ts, power)
parrot(shush:stop):
	user.power_momentum_decaying()

parrot(fff):
	user.power_momentum_scroll_up()
	user.power_momentum_start(ts, 2.0)
parrot(fff:repeat):
	user.power_momentum_add(ts, power)
parrot(fff:stop):
	user.power_momentum_decaying()

parrot(hiss):
	user.mouse_drag()
parrot(hiss:stop):
	user.mouse_drag_stop()

parrot(cluck):
	mouse_click(0)
parrot(tut):
	mouse_click(1)
parrot(pop):
	user.power_momentum_stop()
	
parrot(palate_click):
	key(f4)
	user.disable_parrot_modes()

parrot(ue):
	user.press_virtual_keybird_key(ts)

parrot(ah):
	key(f4)
	user.switch_parrot_mode("parrot_mouse")
falcon perch:
	key(f4)
	user.disable_parrot_modes()