class_name InputRouter
extends Node
## Routes player input from whichever InputSource is active for the current
## level into corrected song time, and hands it to the rest of the game.
##
## It does three jobs:
##   1. Owns the one InputSource a level uses (keyboard, gesture, ...) and
##      switches between them when the level changes.
##   2. Corrects every input for the player's calibration and for how slow the
##      source itself is to report a hit.
##   3. Re-emits each hit as input_routed(input_id, song_time) for HitJudge.
##
## HOW THE GAME USES IT:
##   input_router.add_source("keyboard", keyboard_input)
##   input_router.add_source("gesture", gesture_input)
##   input_router.set_conductor(conductor)
##   input_router.choose_source_for_level("keyboard")
##   input_router.input_routed.connect(hit_judge.judge)
##   conductor.start_song()
##
## input_received(key, time) already carries song time (time comes from
## Conductor.song_time(), see InputSource), so there's no raw device clock to
## convert from here -- just calibration and source-latency correction.
## The router never looks at input_id, so a source that emits lane names
## ("lane_0") and one that emits sign names ("Open_Palm") both work unchanged.

## Emitted once per input, after calibration and source-latency correction.
signal input_routed(input_id, song_time)

## Player calibration, in seconds. Positive means the player's inputs land
## late, so this much is subtracted from every input's song time.
@export var calibration_offset: float = 0.0

## Extra delay per source type, in seconds: how long after the player's real
## action the source reports it. Keyboard is immediate; a camera has to grab
## a frame and run the model first. Tune per source with set_source_latency().
@export var source_latency: Dictionary = {
	"keyboard": 0.0,
	"gesture": 0.10,
}

var _sources: Dictionary = {}       # input type (String) -> InputSource
var _active_type: String = ""       # "" means no source is active
var _conductor: Conductor = null    # set via set_conductor(); the song clock


# Sources can be passed in up front (handy for tests), or added later with
# add_source().
func _init(initial_sources: Dictionary = {}) -> void:
	for input_type in initial_sources:
		add_source(input_type, initial_sources[input_type])


# ---- source management ----

# Registers a source for one input type, e.g. add_source("keyboard", keyboard_input).
# Passing sources in like this (rather than hard-coding them) means they can be mocked in tests.
func add_source(input_type: String, source: InputSource) -> void:
	_sources[input_type] = source


# Makes the source for input_type the active one: the previous source is
# stopped and the new one started. Returns the now-active source, or null if
# no source was registered for input_type.
func choose_source_for_level(input_type: String) -> InputSource:
	if not _sources.has(input_type):
		push_error("InputRouter: no input source registered for %s" % input_type)
		return null

	var source: InputSource = _sources[input_type]
	if _active_type != input_type:
		stop()                               # only one source may listen at a time
		_active_type = input_type
		source.input_received.connect(_on_input_received)

	source.start()                           # no-op if it is already running
	return source


# Stops the active source. Does nothing if none is active.
func stop() -> void:
	if _active_type == "":
		return
	var source: InputSource = _sources[_active_type]
	if source.input_received.is_connected(_on_input_received):
		source.input_received.disconnect(_on_input_received)
	source.stop()
	_active_type = ""


# The InputSource currently being read, or null.
func active_source() -> InputSource:
	if _active_type == "":
		return null
	return _sources[_active_type]


# The input type currently being read (e.g. "keyboard"), or "" if none.
func active_input_type() -> String:
	return _active_type


# ---- timing ----

# Sets the Conductor used as the song clock. Inputs are discarded until this
# is called, and also until the Conductor's song has started (see
# Conductor.is_running()), since there's no song yet to time them against --
# this is the Conductor-based replacement for the old "set_song_start(t)" setter.
func set_conductor(conductor: Conductor) -> void:
	_conductor = conductor


# Forgets the Conductor, e.g. between songs. Inputs go back to being discarded.
func clear_conductor() -> void:
	_conductor = null


func song_has_started() -> bool:
	return _conductor != null and _conductor.is_running()


# Sets the extra delay to subtract for one source type.
func set_source_latency(input_type: String, seconds: float) -> void:
	source_latency[input_type] = seconds


# ---- signal handling ----

# Runs whenever the active source emits input_received(key, time). time is
# already song time (see InputSource), so correction is just calibration and
# source latency. Re-emits input_routed(input_id, song_time) for HitJudge.
func _on_input_received(key, time: float) -> void:
	if _conductor == null or not _conductor.is_running():
		return  # song hasn't started; nothing to time this input against

	var latency: float = source_latency.get(_active_type, 0.0)  # unknown types: no correction
	input_routed.emit(key, time - calibration_offset - latency)
