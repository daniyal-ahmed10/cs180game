from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return 0

@app.post("/accounts/{username}")
def add_user(username: str):
    with open("storage_test/account.txt", "a") as file:
        file.write(str(username) + "\n")
    