import json
from .noteClass import Note

class Chart:
    def __init__(self, title: str, audio_file: str, bpm: float,
                 offset_ms: int = 0, notes=None):
        self.title = title
        self.audio_file = audio_file
        self.bpm = bpm
        self.offset_ms = offset_ms          # delay before beat 0 in the audio
        self.notes = notes if notes is not None else []

    def add_note(self, note: Note):
        self.notes.append(note)
        self.notes.sort(key=lambda n: n.position)

    def beat_to_ms(self, beat: float) -> float:
        return self.offset_ms + beat * 60000 / self.bpm

    def save(self, path: str):
        data = {
            "title": self.title,
            "audio_file": self.audio_file,
            "bpm": self.bpm,
            "offset_ms": self.offset_ms,
            "notes": [n.to_dict() for n in self.notes],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: str):
        with open(path) as f:
            data = json.load(f)
        notes = [Note.from_dict(n) for n in data.pop("notes")]
        return cls(**data, notes=notes)