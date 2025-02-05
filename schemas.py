from pydantic import BaseModel
from datetime import datetime

class TournamentCreate(BaseModel):           #Не костилі
    name: str
    date: datetime
    class Config:
        from_attributes = True
class TeamCreate(BaseModel):
    name: str
    class Config:
        from_attributes = True
class ResultCreate(BaseModel):
    score: int
    team_id: int
    tournament_id: int
    class Config:
        from_attributes = True
class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    class Config:
        from_attributes = True
class UserLogin(BaseModel):
    username: str
    password: str
    class Config:
        from_attributes = True