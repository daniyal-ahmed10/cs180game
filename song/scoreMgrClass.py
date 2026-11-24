class ScoreMgr:
    score: int = 0      # arbitrary number
    combo: int = 0      # current streak of consecutive notes
    max_combo: int = 0  # shown at the end
    accuracy: float = 1 # from 0 to 1
    notecount: int = 0  # needed to calculate accuracy

    # accuracy: window (in ms) 
    WINDOWS = {
        "perfect": 20.0,
        "great": 70.0,
        "okay": 110.0
    }
    # accuracy: score
    SCORES = {
        "perfect": 100,
        "great" : 50,
        "okay": 25
    }

    # addscore interface
    # call addscore whenever a note is hit
    # caller must calculate timingErrorMS and holdPCT
    # caller must set notecount
    def addscore(self, timingErrorMs: float, note_type: str = "tap", holdPct: float = 0.0):
        
        # timingErrorMs: how many ms away a keypress is from the actual note
        # note_type: "tap", "hold", etc.
        # holdPct: how much of a hold note is pressed from 0 to 1
        #           holdPct defaults to 0 for tap notes

        # input validation for note_type
        if not(note_type == "tap" or note_type == "hold"):
            raise ValueError(
                f"unknown note_type {note_type!r}, expected one of {'tap', 'hold'}\ncheck function call for typos"
            )
        # input validation for holdPct
        if holdPct < 0 or holdPct > 1:
            raise ValueError(
                f"holdPct {holdPct!r} is out of range, acceptable range is [0, 1]"
            )
        
        # hit scoring
        err = abs(timingErrorMs)
        hit = True
        if note_type == "tap":
            if err <= self.WINDOWS["perfect"]:
                self.score += self.SCORES["perfect"]
            elif err <= self.WINDOWS["great"]:
                self.score += self.SCORES["great"]
            elif err <= self.WINDOWS["okay"]:
                self.score += self.SCORES["okay"]
            else:
                hit = False
        elif note_type == "hold":
            # hold note scores are scaled to how long theyre pressed
            holdScore = 0
            if err <= self.WINDOWS["perfect"]:
                holdScore += self.SCORES["perfect"]
            elif err <= self.WINDOWS["great"]:
                holdScore += self.SCORES["great"]
            elif err <= self.WINDOWS["okay"]:
                holdScore += self.SCORES["okay"]
            else:
                hit = False
            holdScore = holdScore * holdPct
            self.score += holdScore


        # combo logic
        if hit == False:
            self.combo = 0
        if hit == True:
            self.combo += 1
            if self.combo > self.max_combo:
                self.max_combo = self.combo

        # accuracy logic, based on max score
        maxScore = self.notecount * self.SCORES["perfect"]
        if maxScore <= 0:  # input validation for 0 notes
            maxScore = 1  # prevents divide by 0
        self.accuracy = self.score / maxScore

        return

    