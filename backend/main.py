import json
import hashlib
import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

app = FastAPI()

STORAGE_DIR = Path("storage")
ACCOUNTS_FILE = STORAGE_DIR / "accounts.json"
LEADERBOARD_FILE = STORAGE_DIR / "leaderboard.json"

class Credentials(BaseModel):
    username: str
    password: str

class ScoreSubmission(BaseModel):
    song: str
    score: int

def insertSorted(arr, user: str, score: int): # arr is mutable
    # remember, arr is a list of {user: score}
    entry = {user:score}
    # edge case: 0 elements
    if len(arr) == 0:
        arr.append(entry)
        return

    # edge case: insert at the end of array
    if next(iter(arr[len(arr)-1].values())) > score:
        arr.append(entry)
        return

    # general case
    for i in range(len(arr)):
        value = next(iter(arr[i].values()))
        if score > value:
            arr.insert(i, entry)
            break

def mock_hash(password: str) -> str:
    """Mock hash: swap this out for bcrypt/argon2 if the project grows."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# token -> username (in memory, cleared when the server restarts)
sessions: dict[str, str] = {}

# --- account json load and save

def load_accounts() -> dict:
    if not ACCOUNTS_FILE.exists():
        return {}
    with open(ACCOUNTS_FILE, "r") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return {}


def save_accounts(accounts: dict) -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    with open(ACCOUNTS_FILE, "w") as file:
        json.dump(accounts, file, indent=2)


# --- leaderboard json load and save

def load_leaderboard() -> dict:
    if not LEADERBOARD_FILE.exists():
        return {}
    with open(LEADERBOARD_FILE, "r") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return {}


def save_leaderboard(leaderboard: dict) -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    with open(LEADERBOARD_FILE, "w") as file:
        json.dump(leaderboard, file, indent=2)

# --- auth

# adds the "Authorize" button to /docs; auto_error=False so we return our own 401
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None or credentials.credentials not in sessions:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return sessions[credentials.credentials]


@app.get("/")
def root():
    return {"status": "ok"}

# --- account signup and login

@app.post("/signup", status_code=201)
def sign_up(creds: Credentials):
    accounts = load_accounts()
    if creds.username in accounts:
        raise HTTPException(status_code=409, detail="Username already taken")

    accounts[creds.username] = {"password_hash": mock_hash(creds.password)}
    save_accounts(accounts)
    return {"message": f"Account '{creds.username}' created"}


@app.post("/login")
def log_in(creds: Credentials):
    accounts = load_accounts()
    account = accounts.get(creds.username)
    if account is None or account["password_hash"] != mock_hash(creds.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = secrets.token_hex(32)
    sessions[token] = creds.username
    return {"token": token}

@app.post("/logout")
def log_out(authorization: str = Header(default="")):
    _, _, token = authorization.partition(" ")
    sessions.pop(token, None)
    return {"message": "Logged out"}

@app.get("/getTokens")
def getTokens():
    return sessions

# --- leaderboard
# json format: {song name : [username : score]}
# scores are sorted highest first, lower score entries get pushed out
# players can only have one score on
"""
ex:
{
    "pinky up" : [
        {"daniyal": 100000},
        {"lance" : 99999},
        {"stephen": 99998},
        {"ritvik"}: 0
    ]
    "sugar" : [
        {"mattchampion": 167422}
        ...
        ...
    ]
    ...
}

"""

TOP_N = 5

@app.post("/submitscore")
def submitscore(sub: ScoreSubmission, username: str = Depends(get_current_user)):
    # init board to work with
    leaderboard = load_leaderboard()
    boardArr = leaderboard.setdefault(sub.song, []) # top N

    # check if the player has an entry already
    hasEntry = False
    entryNum = 0
    for entry in boardArr:
        if username in entry:
            hasEntry = True
            break
        entryNum += 1

    # on same entry, remove current entry if it is higher, insert new entry
    if hasEntry == True and boardArr[entryNum][username] < sub.score:
        boardArr.pop(entryNum)
        insertSorted(boardArr, username, sub.score)

    # on new entry, insert sorted and remove the N + 1 index if leaderboard is full
    elif hasEntry == False:
        insertSorted(boardArr, username, sub.score)
        if (len(boardArr) > TOP_N):
            boardArr.pop(len(boardArr) - 1)

    # save board to file
    leaderboard[sub.song] = boardArr
    save_leaderboard(leaderboard)
    return "leaderboard.json updated"


@app.get("/getleaderboard/{song}")
def get_leaderboard(song: str):
    song_scores = load_leaderboard().get(song)
    if not song_scores:
        raise HTTPException(status_code = 404, detail = "No scores yet")
    return {song:song_scores[:limit]}