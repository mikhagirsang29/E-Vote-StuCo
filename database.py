import os

from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, UniqueConstraint, event, inspect, text
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./voting.db"

connect_args = {
    "check_same_thread": False
} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Required for SQLite + FastAPI
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Inside database.py
class ElectionState(Base):
    __tablename__ = "election_state"
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="SETUP") # 'SETUP', 'OPEN', 'CLOSED'

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, unique=True, index=True)
    password = Column(String) # Storing plaintext only for this local mock-up!
    role = Column(String, default="student") # 'student' or 'admin'
    
    votes = relationship("Vote", back_populates="voter")

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    position = Column(String)
    manifesto = Column(String)
    photo_path = Column(String, nullable=True) # <-- NEW COLUMN
    
    votes = relationship("Vote", back_populates="candidate")

class Vote(Base):
    __tablename__ = "votes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    receipt_id = Column(String, unique=True, index=True, nullable=True)
    
    # Critical: Ensure a user can only have one vote per database
    __table_args__ = (UniqueConstraint('user_id', name='_user_vote_uc'),)
    
    voter = relationship("User", back_populates="votes")
    candidate = relationship("Candidate", back_populates="votes")
    
# Create tables
Base.metadata.create_all(bind=engine)

# Add receipt_id column to existing schema if missing
inspector = inspect(engine)
columns = [column_info['name'] for column_info in inspector.get_columns('votes')]
if 'receipt_id' not in columns:
    with engine.begin() as conn:
        conn.execute(text('ALTER TABLE votes ADD COLUMN receipt_id VARCHAR'))
