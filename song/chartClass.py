from .noteClass import Note

class Chart:
    
    def __init__ (self, bpm:float, input_type: str, notes):
        self.bpm = bpm
        self.input_type = input_type
        self.notes = []


    def add_note(self, noteAdd:Note):
        self.notes.append(Note)