import secrets

from fastapi import Request, Depends
from sqlalchemy.orm import Session

import database
from database import SessionLocal, User, Vote


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request, db: Session = Depends(get_db)):
    student_id = request.cookies.get("student_id")
    if not student_id:
        return None
    return db.query(User).filter(User.student_id == student_id).first()


def get_branding(db: Session):
    return db.query(database.SiteBranding).filter(database.SiteBranding.id == 1).first()


def generate_receipt_id() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "-".join(
        "".join(secrets.choice(alphabet) for _ in range(2))
        for _ in range(3)
    )


def get_unique_receipt_id(db: Session) -> str:
    while True:
        receipt = generate_receipt_id()
        if not db.query(Vote).filter(Vote.receipt_id == receipt).first():
            return receipt
