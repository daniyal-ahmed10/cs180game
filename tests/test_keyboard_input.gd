extends Node
## Manual test for KeyboardInput.
##
## Attach this script to the root Node of a new scene and press F6.
## Press D, F, J, K and watch the Output panel. Press Escape to stop the source.

var _conductor: Conductor
var _keyboard_input: KeyboardInput


# Builds a Conductor and a KeyboardInput, wires them together, and starts input.
func _ready() -> void:
	_conductor = Conductor.new()
	add_child(_conductor)
	_conductor.start_song()  # No stream set, so this runs a silent clock.

	_keyboard_input = KeyboardInput.new()
	_keyboard_input.debug_mode = false
	add_child(_keyboard_input)

	_keyboard_input.set_conductor(_conductor)
	_keyboard_input.input_received.connect(_on_input_received)
	_keyboard_input.start()
	print("KeyboardInput test running. Press D F J K (Escape stops input).")


# Stops the source on Escape so you can check that presses are then ignored.
func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		_keyboard_input.stop()
		print("Stopped. Logged %d inputs." % _keyboard_input.input_log.size())


# Prints each lane hit as it arrives.
func _on_input_received(lane: int, time: float) -> void:
	print("lane %d hit at %.3f s" % [lane, time])
