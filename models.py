from sqlalchemy import Column, Integer, String, ForeignKey, DateTime,  func
from sqlalchemy.orm import relationship
from database import Base
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    team_id = Column(Integer, ForeignKey("teams.id"))
    team = relationship("Team", back_populates="members")
    created_at = Column(DateTime, default=func.now())
class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    rating = Column(Integer, default=0)
    members = relationship("User", back_populates="team")
    results = relationship("Result", back_populates="team")
    created_at = Column(DateTime, default=func.now())
class Tournament(Base):
    __tablename__ = "tournaments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=func.now())
    results = relationship("Result", back_populates="tournament")
    finish_at = created_at
class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True, index=True)
    score = Column(Integer)
    team_id = Column(Integer, ForeignKey("teams.id"))
    tournament_id = Column(Integer, ForeignKey("tournaments.id"))
    team = relationship("Team", back_populates="results")
    tournament = relationship("Tournament", back_populates="results")
    created_at = Column(DateTime, default=func.now())