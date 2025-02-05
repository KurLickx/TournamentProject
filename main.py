from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from jose import jwt
from datetime import datetime, timedelta
from database import Base, engine, SessionLocal
from models import User, Team, Tournament, Result 
from schemas import TournamentCreate, TeamCreate, ResultCreate, UserCreate, UserLogin
from utils import calculate_team_rating
from passlib.context import CryptContext

Base.metadata.create_all(bind=engine)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
SECRET_KEY = "Insomnia"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
def get_password_hash(password):
    return pwd_context.hash(password)
def get_user(db, username: str):
    return db.query(User).filter(User.name == username).first()
def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

@app.post("/register")                                                                                          #Ендпоінти 17.12   4.01
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, user.name)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(name=user.name, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"msg": "User registered successfully"}
@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.name})
    return {"access_token": access_token, "token_type": "bearer"}
@app.post("/tournaments/", response_model=TournamentCreate)
def create_tournament(tournament: TournamentCreate, db: Session = Depends(get_db)):
    db_tournament = Tournament(**tournament.dict())
    db.add(db_tournament)
    db.commit()
    db.refresh(db_tournament)
    return db_tournament
@app.post("/teams/create")
def create_team(team: TeamCreate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    user = get_user(db, username)
    if user.team_id:
        raise HTTPException(status_code=400, detail="User is already part of a team")
    db_team = Team(name=team.name)
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    user.team_id = db_team.id
    db.commit()
    return {"msg": f"Team '{team.name}' created successfully, and user '{user.name}' is added as a member."}
@app.post("/teams/join/{team_id}")
def join_team(team_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    user = get_user(db, username)
    if user.team_id:
        raise HTTPException(status_code=400, detail="User is already part of a team")
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    user.team_id = team.id
    db.commit()
    return {"msg": f"User '{user.name}' has joined the team '{team.name}' successfully."}
@app.get("/tournaments/", response_model=list[TournamentCreate])
def get_tournaments(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    tournaments = db.query(Tournament).offset(skip).limit(limit).all()
    return tournaments
@app.put("/tournaments/{tournament_id}", response_model=TournamentCreate)
def update_tournament(tournament_id: int, tournament: TournamentCreate, db: Session = Depends(get_db)):
    db_tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not db_tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    for key, value in tournament.dict().items():
        setattr(db_tournament, key, value)
    db.commit()
    db.refresh(db_tournament)
    return db_tournament
@app.delete("/tournaments/{tournament_id}", status_code=204)
def delete_tournament(tournament_id: int, db: Session = Depends(get_db)):
    db_tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not db_tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    db.delete(db_tournament)
    db.commit()
    return
@app.post("/results/", response_model=ResultCreate)
def create_result(result: ResultCreate, db: Session = Depends(get_db)):
    db_result = Result(**result.dict())
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    calculate_team_rating(db, result.team_id)
    return db_result
@app.get("/teams/{team_id}/rating")
def get_team_rating(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return {"team_id": team.id, "rating": team.rating}
connections = []

@app.websocket("/ws/notify") #Костилі на Вебах ранковий андрій пофіксь пж 24.12   ЭЭЭЭЭЭ? 27.12
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            for connection in connections:
                await connection.send_text(f"Message: {data}")
    except WebSocketDisconnect:
        connections.remove(websocket)
active_connections = []
class ConnectionManager:
    def __init__(self):
        self.active_connections = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
manager = ConnectionManager()
@app.websocket("/ws/chat")
async def chat_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
