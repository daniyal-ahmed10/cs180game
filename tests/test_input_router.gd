extends Node
## Manual test for InputRouter.
##
## Attach this script to the root Node of a new scene and press F6.
## For the first 3 seconds the song hasn't started, so presses are ignored and
## print nothing. After that, press D, F, J, K and watch the Output panel:
## InputRouter prints the corrected song time for each press. Press Escape to
## stop routing.

var _conductor: Conductor
var _keyboard_input: KeyboardInput
var _router: InputRouter


# Builds a Conductor, a KeyboardInput, and an InputRouter, wires them
# together, and starts routing keyboard input. The song itself only starts
# after a 3-second countdown.
func _ready() -> void:
	_conductor = Conductor.new()
	add_child(_conductor)
	# Not started yet: the router ignores presses until start_song() is called.

	_keyboard_input = KeyboardInput.new()
	add_child(_keyboard_input)
	_keyboard_input.set_conductor(_conductor)

	_router = InputRouter.new({"keyboard": _keyboard_input})
	add_child(_router)
	_router.set_conductor(_conductor)
	_router.input_routed.connect(_on_input_routed)
	_router.choose_source_for_level("keyboard")

	print("InputRouter test running. Press D F J K (Escape stops routing).")

	print("Countdown: presses are ignored for 3 seconds.")
	await get_tree().create_timer(3.0).timeout
	_conductor.start_song()  # No stream set, so this runs a silent clock.
	print("Song started: presses now count.")


# Stops the router on Escape so you can check that presses are then ignored.
func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		_router.stop()
		print("Stopped routing.")


# Prints each routed input as it arrives.
func _on_input_routed(input_id, song_time: float) -> void:
	print("routed %s at %.3f s" % [input_id, song_time])
