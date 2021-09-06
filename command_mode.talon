mode: command
-
tag(): user.humming_bird
tag(): user.humming_bird_overrides

parrot(call_bell):
	speech.disable()
	mode.disable("noise")

parrot(cluck):
	mouse_click(0)
    user.add_noise_log("Left click", "CLUCK")
parrot(palate_click):
	user.enable_switching_parrot_mode()
	
falcon fly:
	key(f4)
	user.switch_parrot_mode("parrot_eyemouse")

humming fly:
	user.switch_parrot_mode("parrot_mouse")
	#user.hummingbird_set("cursor")
humming$:
	user.switch_parrot_mode("parrot_mouse")

	
pidgeon fly:
	speech.disable()
	user.switch_parrot_mode("parrot_media")
	
parrot(gluck):
	edit.cut()
parrot(whistle):
	edit.paste()
#parrot(pop):
#	key(backspace)
	
	
#parrot(whistle):
#    user.hud_add_ability("camera", "parrot_eyemouse", "777777", 1, 1)
#parrot(tut):
#    user.hud_add_ability("camera", "lock-on", "777777", 1, 1)
#parrot(whistle:stop):
#    user.hud_add_ability("camera", "no-camera", "777777BB", 1, 0)
	
	
move top:
    user.hud_add_ability("movement", "top", "777777", 1, 0, 0, -1)
move top left:
    user.hud_add_ability("movement", "topleft", "777777", 1, 0, 2, 2)
move top right:
    user.hud_add_ability("movement", "topright", "777777", 1, 0, -2, 2)
move left:
    user.hud_add_ability("movement", "left", "777777", 1, 0, -2, 0)
move right:
    user.hud_add_ability("movement", "right", "777777", 1, 0, 2, 0)
move bottom left:
    user.hud_add_ability("movement", "bottomleft", "777777", 1, 0, 2, -2)
move bottom right:
    user.hud_add_ability("movement", "bottomright", "777777", 1, 0, -2, -2)
move bottom:
    user.hud_add_ability("movement", "bottom", "777777", 1, 0, 0, 2)