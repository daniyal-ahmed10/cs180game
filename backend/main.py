# leaderboard functionality will need to change during integration
# plan is to keep a folder for each chart with its own leaderboard section

import json
import hashlib
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

STORAGE_DIR = Path("account_storage")
ACCOUNTS_FILE = STORAGE_DIR / "accounts.json"
LEADERBOARD_FILE = STORAGE_DIR / "leaderboard.json"  # CHANGE DURING INTEGRATION

class Credentials(BaseModel):
    username: str
    password: str

def mock_hash(password: str) -> str:
    """Mock hash: swap this out for bcrypt/argon2 if the project grows."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


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


@app.get("/")
def root():
    return {"status": "ok"}


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

    return {"message": f"Welcome back, {creds.username}"}