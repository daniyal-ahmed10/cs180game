class_name Conductor
extends AudioStreamPlayer
## The game's only clock. song_time() returns how far into the song we are,
## in seconds.
##
## With a stream assigned, time comes from the audio playback position, adjusted
## for audio latency so it matches what the player hears. With no stream
## (for example in tests), it counts time since start_song() was called.

## Beats per minute of the current song. Used by beat helpers.
@export var bpm: float = 120.0

var _is_running: bool = false
var _start_ticks_usec: int = 0
var _last_time: float = 0.0


# Starts the song (or the silent clock if no stream is set) from the beginning.
func start_song() -> void:
	_last_time = 0.0
	_start_ticks_usec = Time.get_ticks_usec()
	_is_running = true
	if stream != null:
		play()


# Stops the song and the clock.
func stop_song() -> void:
	_is_running = false
	if playing:
		stop()


# Returns true while the song (or silent clock) is running.
func is_running() -> bool:
	return _is_running


# Returns the current song time in seconds. Never goes backwards while running.
func song_time() -> float:
	if not _is_running:
		return _last_time

	var time: float
	if stream != null and playing:
		time = (
			get_playback_position()
			+ AudioServer.get_time_since_last_mix()
			- AudioServer.get_output_latency()
		)
	else:
		time = (Time.get_ticks_usec() - _start_ticks_usec) / 1_000_000.0

	# Audio mixing updates in chunks, so smooth out tiny backwards jumps.
	_last_time = maxf(time, _last_time)
	return _last_time


# Returns the length of one beat in seconds.
func seconds_per_beat() -> float:
	return 60.0 / bpm


# Returns the current position in beats (can be fractional).
func song_beat() -> float:
	return song_time() / seconds_per_beat()
