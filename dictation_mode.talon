mode: dictation
-
parrot(call_bell):
	speech.disable()

parrot(pop):
	edit.extend_word_left()
    edit.delete()
parrot(cluck):
	key(enter)