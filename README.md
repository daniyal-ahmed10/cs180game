# CS 180 Project - Ritmo

A 2D rhythm game where you hit notes in time with music, inspired by classic rhythm games such as 'Osu!' and 'Rhythm Doctor'. Ritmo will use Googles Mediapipe Library to add a unique playstyle, where users use their hands in sync to the music to interact with the game, rather than the classic keyboard inputs. A classic play style will be available as well, for users that prefer keyboard inputs.
## Examples
Below is a demo of a popular online rhythm game, 'Rhythm+'. This represents what the keyboard input style gameplay will look like.
https://github.com/user-attachments/assets/df62ee3b-ced7-4ca5-b03e-70756d38089c



## How to play

- **Keyboard levels:** Press **D, F, J, K** when notes reach the hit line.
- **Motion levels:** Match your hand into the target zone to the hand symbol shown on screen. Use blue notes for your left hand and red notes for your right.

## Getting started (for the team)

The `cs180game/` folder is the Godot project (it contains `project.godot`).

1. Install **Godot 4.3 or newer** (standard version, not .NET) from [godotengine.org](https://godotengine.org/download).
2. Open Godot, click **Import**, select `cs180game/project.godot`, then **Import & Edit**.
3. Press **F5**. The main scene is currently the keyboard input test: press D, F, J, K and the Output panel prints the lane and song time. Press Escape to stop input.

The `.godot/` cache folder is created automatically and is git-ignored. Don't commit it.

### Project layout

| Path | What it is |
| --- | --- |
| `project.godot` | Godot project settings, including the Input Map (`lane_0`–`lane_3` = D, F, J, K) |
| `inputs/input_source.gd` | `InputSource`: base class for all input. Has `start()`, `stop()` and the `input_received(key, time)` signal |
| `inputs/keyboard_input.gd` | `KeyboardInput`: keyboard lanes for Medium/Hard levels. Emits `input_received(lane, song_time)` once per press (held keys don't repeat) and keeps a log of the last 100 inputs (`debug_mode` prints each one) |
| `song/conductor.gd` | `Conductor`: the game's **only** clock. `song_time()` returns seconds into the song, corrected for audio latency. With no song loaded it counts from `start_song()`, which is handy for tests |
| `tests/test_keyboard_input.gd` / `.tscn` | Manual test scene for `KeyboardInput` |
| `inputs/*.py`, `song/*.py`, `tests/*.py` | Older Python prototypes and the hand-tracking test (see below) |

### How the pieces connect

```
KeyboardInput / MotionInput  --input_received(lane, time)-->  InputRouter  -->  HitJudge
          (InputSource)                 ^
                                        |
                              Conductor.song_time()
```

- Every input source extends `InputSource` and timestamps inputs with `Conductor.song_time()`, never with system time.
- Give a source its Conductor with `set_conductor(conductor)` instead of hard-coding node paths.
- Inputs are read in `_unhandled_input`, so menus and pause screens can consume keys first.
- Key bindings live in **Project > Project Settings > Input Map** (`lane_0`–`lane_3`), so they can be remapped without code changes.

### Still to do

- [ ] `InputRouter`: holds one `InputSource` and forwards `input_received` to `HitJudge`
- [ ] `HitJudge`: compares input times with note times from the chart
- [ ] Port `Chart` / `Note` from Python to GDScript
- [ ] `MotionInput`: the Python hand tracker can't run inside Godot, so it will run as a separate process and send results to Godot (e.g. over a local UDP socket). A GDScript `MotionInput extends InputSource` receives them and emits `input_received`, so the rest of the game works the same for both play styles
- [ ] Replace the test scene as the main scene once a real menu/level exists

The Python `KeyboardInput` (`inputs/keyboardInputClass.py`) is replaced by `keyboard_input.gd` and is only kept for reference.

## Built with
- Godot 4 (GDScript)
- Python, MediaPipe and OpenCV for hand tracking
- VS Code with the godot-tools extension
