extends Node
## Manual test for InputRouter.
##
## Attach this script to the root Node of a new scene and press F6.
## Press D, F, J, K and watch the Output panel: InputRouter prints the
## corrected song time for each press. Press Escape to stop routing.

var _conductor: Conductor
var _keyboard_input: KeyboardInput
var _router: InputRouter


# Builds a Conductor, a KeyboardInput, and an InputRouter, wires them
# together, and starts routing keyboard input.
func _ready() -> void:
	_conductor = Conductor.new()
	add_child(_conductor)
	_conductor.start_song()  # No stream set, so this runs a silent clock.

	_keyboard_input = KeyboardInput.new()
	add_child(_keyboard_input)
	_keyboard_input.set_conductor(_conductor)

	_router = InputRouter.new({"keyboard": _keyboard_input})
	add_child(_router)
	_router.set_conductor(_conductor)
	_router.input_routed.connect(_on_input_routed)
	_router.choose_source_for_level("keyboard")

	print("InputRouter test running. Press D F J K (Escape stops routing).")


# Stops the router on Escape so you can check that presses are then ignored.
func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		_router.stop()
		print("Stopped routing.")


# Prints each routed input as it arrives.
func _on_input_routed(input_id, song_time: float) -> void:
	print("routed %s at %.3f s" % [input_id, song_time])
