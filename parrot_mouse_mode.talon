mode: user.parrot_mouse
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
	key(ctrl:down)
	mouse_click(0)
	key(ctrl:up)

parrot(pop):
	user.power_momentum_stop()
	user.hummingbird_clear()
	user.hummingbird_stop()
parrot(ae):
	user.kingfisher_click(1)
	
parrot(palate_click):
	mode.enable("command")
	user.disable_parrot_modes()
	
#parrot(ee):
#	key(f4)
#	user.switch_parrot_mode("parrot_eyemouse")
	
parrot(ue):
	user.press_virtual_keybird_key(ts)
	
falcon fly:
	key(f4)
	user.switch_parrot_mode("parrot_eyemouse")

humming fly:
	user.hummingbird_set("cursor")

parrot(ch):
	user.hummingbird2_continuous()
parrot(hmm):
	user.hummingbird2_down(ts, "start")
parrot(hmm:repeat):
	user.hummingbird2_down(ts, "repeat")
parrot(hmm:stop):
	user.hummingbird2_down(ts, "stop")
parrot(hurr):
	user.hummingbird2_right(ts, "start")
parrot(hurr:repeat):
	user.hummingbird2_right(ts, "repeat")
parrot(hurr:stop):
	user.hummingbird2_right(ts, "stop")
parrot(yee):
	user.hummingbird2_up(ts, "start")
parrot(yee:repeat):
	user.hummingbird2_up(ts, "repeat")
parrot(yee:stop):
	user.hummingbird2_up(ts, "stop")
parrot(lll):
	user.hummingbird2_left(ts, "start")
parrot(lll:repeat):
	user.hummingbird2_left(ts, "repeat")
parrot(lll:stop):
	user.hummingbird2_left(ts, "stop")