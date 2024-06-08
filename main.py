from fastapi import Depends, FastAPI, HTTPException, status, Response
from enum import Enum
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, timezone

from typing import Annotated
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestFormStrict

from passlib.context import CryptContext

import jwt

import liga
from datetime import datetime

storage = "storage.json"

app_liga = liga.liga(storage)


# create file secret_key.txt:
#openssl rand -hex 32 > secret_key.txt

# create password_hash.txt:
# python3 -c 'from passlib.hash import bcrypt; print(bcrypt.using(rounds=12).hash("password"))' > password_hash.txt


with open("secret_key.txt", "r") as f:
    SECRET_KEY = f.readline()

with open("password_hash.txt", "r") as f:
    password_hash = f.readline()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

username = "wizard"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


class Token(BaseModel):
    access_token: str
    token_type: str

def verify_password(password):
    return pwd_context.verify(password, password_hash)

app = FastAPI(title="Elo API", details="API for managing elo ratings")

origins = [
    "http://akihiko-feierbar.de",
    "https://akihiko-feierbar.de",
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
    "http://localhost:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Player(BaseModel):
    id: str
    name: str
    deck: str
    

class Game(BaseModel):
    player1: str
    player2: str
    result: float

class GameOutput(BaseModel):
    timestamp: str
    game_id: int
    player1: str
    player2: str
    result: float

class PlayerOutput(BaseModel):
    id: str
    name: str
    deck: str
    elo: float


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def is_authenticated(token: Annotated[str, Depends(oauth2_scheme)]):

    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        authenticated = data.get("authenticated")
        if not authenticated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token not valid",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return data
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No Valid Token. Token may be missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

def authenticate_login(username: str, password: str):
    if username == "admin" and verify_password(password):
        return True
    return False



@app.post("/token")
async def login_for_access_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestFormStrict, Depends()],
) -> Token:
    user = authenticate_login(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"authenticated": True}, expires_delta=access_token_expires
    )

    token = Token(access_token=access_token, token_type="bearer")

    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)

    return token

@app.get("/authenticated")
async def authenticated(
    authenticated: Annotated[bool, Depends(is_authenticated)],
):
    return authenticated


@app.get("/players/", response_model=list[PlayerOutput])
async def get_players(
    authenticated: Annotated[bool, Depends(is_authenticated)]
):
    return [{"id": k, "elo": v["elo"], "name":v["name"], "deck":v["deck"]} for k, v in app_liga.players.items()]

@app.get("/players/{player_id}", response_model=PlayerOutput)
async def get_player(
    authenticated: Annotated[bool, Depends(is_authenticated)],
    player_id: str
):
    player = app_liga.players.get(player_id)
    if player == None:
        raise HTTPException(status_code=404, detail="Player not found")
    return {
        "id": player_id,
        "elo": player["elo"],
        "name": player["name"],
        "deck": player["deck"]
        }


@app.post("/players/")
async def post_player(
    authenticated: Annotated[bool, Depends(is_authenticated)],
    player: Player
    ):
    if app_liga.players.get(player.id) != None:
        raise HTTPException(status_code=400, detail="Player ID already exists")
    app_liga.register_player(player.id, player.name, player.deck)
    return {"result": "success"}

@app.get("/games/", response_model=list[GameOutput])
async def get_games(
    authenticated: Annotated[bool, Depends(is_authenticated)]
):
    return [{"game_id": k, "timestamp": v[3], "player1": v[0], "player2": v[1], "result": v[2]} for k, v in app_liga.games.items()]

@app.post("/games/")
async def post_game(
    authenticated: Annotated[bool, Depends(is_authenticated)],
    game: Game
    ):
    """
    if draw is False player1 won, otherwise it's a draw
    """
    if(app_liga.players.get(game.player1) == None):
        raise HTTPException(status_code=400, detail="Player 1 not found")
    if(app_liga.players.get(game.player2) == None):
        raise HTTPException(status_code=400, detail="Player 2 not found")
    if(game.player1 == game.player2):
        raise HTTPException(status_code=400, detail="Players must be different")
    if(game.result != 0.5 and game.result != 1 and game.result != 0):
        raise HTTPException(status_code=400, detail="Result must be 0 0.5 or 1")
    timestamp = datetime.now().isoformat()

    app_liga.register_game(game.player1, game.player2, game.result, timestamp)
    return {"result": "success"}

@app.delete("/games/{game}")
async def delete_game(
    authenticated: Annotated[bool, Depends(is_authenticated)],
    game: int
    ):
    app_liga.delete_game(game)
    return {"result": "success"}
