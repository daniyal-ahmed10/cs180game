class_name KeyboardInput
extends InputSource
## Keyboard input source for Medium and Hard levels.
##
## Maps four Input Map actions (lane_0 to lane_3, default D F J K) to lanes 0-3.
## Each new press of a lane key emits input_received(lane, song_time), using the
## Conductor as the only clock.

const MAX_LOG_SIZE: int = 100

## Fallback keys, only used if an action is missing from the Input Map.
const DEFAULT_KEYS: Dictionary = {
	&"lane_0": KEY_D,
	&"lane_1": KEY_F,
	&"lane_2": KEY_J,
	&"lane_3": KEY_K,
}

## When true, every lane input is printed to the output panel.
@export var debug_mode: bool = false

## Input Map action name (StringName) -> lane index (int).
var key_map: Dictionary = {
	&"lane_0": 0,
	&"lane_1": 1,
	&"lane_2": 2,
	&"lane_3": 3,
}

## Recent inputs, oldest first. Each entry is { "lane": int, "time": float }.
var input_log: Array[Dictionary] = []

var _is_active: bool = false
var _conductor: Conductor = null


# Makes sure every lane action exists so the class works even before the
# Input Map is set up. Actions already in the Input Map are left untouched.
func _ready() -> void:
	_ensure_default_actions()


# Runs after GUI and _input(), so menus and pause screens can consume keys first.
func _unhandled_input(event: InputEvent) -> void:
	log_key(event)


# Starts listening for lane presses and clears the input log.
func start() -> void:
	super.start()
	if _conductor == null:
		push_warning("KeyboardInput started without a Conductor; call set_conductor() first.")
	input_log.clear()
	_is_active = true


# Stops listening for lane presses.
func stop() -> void:
	super.stop()
	_is_active = false


# Sets the Conductor used to timestamp every input.
func set_conductor(conductor: Conductor) -> void:
	_conductor = conductor


# Returns true while the source is between start() and stop().
func is_active() -> bool:
	return _is_active


# Catches one key press. If it is a lane key, logs it and emits
# input_received(lane, song_time). Echo (held-key repeat) events are ignored.
func log_key(event: InputEvent) -> void:
	if not _is_active or _conductor == null:
		return

	var key_event: InputEventKey = event as InputEventKey
	if key_event == null or not key_event.pressed or key_event.echo:
		return

	for action: StringName in key_map:
		if key_event.is_action_pressed(action):
			var lane: int = key_map[action]
			var time: float = _conductor.song_time()
			_add_to_log(lane, time)
			input_received.emit(lane, time)
			if is_inside_tree():  # No viewport when called outside the scene tree.
				get_viewport().set_input_as_handled()
			return


# Appends an input to the log, dropping the oldest entry past MAX_LOG_SIZE.
func _add_to_log(lane: int, time: float) -> void:
	input_log.append({ "lane": lane, "time": time })
	if input_log.size() > MAX_LOG_SIZE:
		input_log.pop_front()
	if debug_mode:
		print("KeyboardInput: lane %d at %.3f s" % [lane, time])


# Adds any missing lane action with its default key (D, F, J, K).
func _ensure_default_actions() -> void:
	for action: StringName in DEFAULT_KEYS:
		if InputMap.has_action(action):
			continue
		var key_event: InputEventKey = InputEventKey.new()
		key_event.physical_keycode = DEFAULT_KEYS[action]
		InputMap.add_action(action)
		InputMap.action_add_event(action, key_event)
