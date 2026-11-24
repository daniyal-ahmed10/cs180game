from dataclasses import dataclass, asdict

@dataclass
class Note:
    position: float          # in beats
    lane: int                # keyboard lane
    note_type: str           # "tap", "hold", etc.
    gesture: str = "none"    # "fist", "open_palm", "peace", ...
    duration: float = 0.0    # in beats, for hold notes

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)