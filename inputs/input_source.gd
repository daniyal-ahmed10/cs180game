class_name InputSource
extends Node
## Base class for every way a player can give input (keyboard, hand tracking, ...).
##
## Subclasses override start() and stop(), and emit input_received(key, time)
## whenever the player hits something. key is the lane (or symbol) that was hit,
## and time is the song time from the Conductor.

## Emitted for each player input. InputRouter listens to this.
signal input_received(key, time)


# Begins capturing input. Subclasses override this and call super.start().
func start() -> void:
	pass


# Stops capturing input. Subclasses override this and call super.stop().
func stop() -> void:
	pass
