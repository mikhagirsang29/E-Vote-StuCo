from fastapi import APIRouter, Request, Form, Depends, Response, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

import database
from database import User, Candidate, Vote, ElectionState
from utilities.utilities import get_db, get_current_user, get_unique_receipt_id, get_branding
from routes.admin import manager  # Import the WebSocket manager from admin.py

client_router = APIRouter()
templates = Jinja2Templates(directory="templates")


@client_router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        branding = get_branding(db)
        return templates.TemplateResponse(request=request, name="login.html", context={"branding": branding})
    if user.role == "admin":
        return RedirectResponse(url="/admin", status_code=303)

    candidates = db.query(Candidate).all()
    has_voted = db.query(Vote).filter(Vote.user_id == user.id).first() is not None
    receipt_id = None
    if has_voted:
        vote = db.query(Vote).filter(Vote.user_id == user.id).first()
        receipt_id = vote.receipt_id

    state = db.query(ElectionState).filter(ElectionState.id == 1).first()
    branding = get_branding(db)

    return templates.TemplateResponse(
        request=request,
        name="client/dashboard.html",
        context={"user": user, "candidates": candidates, "has_voted": has_voted, "status": state.status, "receipt_id": receipt_id, "branding": branding}
    )


@client_router.post("/login")
async def login(response: Response, student_id: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.student_id == student_id, User.password == password).first()
    if not user:
        return RedirectResponse(url="/?error=Invalid Credentials", status_code=303)

    res = RedirectResponse(url="/", status_code=303)
    res.set_cookie(key="student_id", value=user.student_id)
    return res


@client_router.post("/logout")
async def logout():
    res = RedirectResponse(url="/", status_code=303)
    res.delete_cookie("student_id")
    return res


@client_router.post("/vote", response_class=HTMLResponse)
async def submit_vote(request: Request, candidate_id: int = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return HTMLResponse("<p class='text-red-500'>Please log in to vote.</p>")

    state = db.query(ElectionState).filter(ElectionState.id == 1).first()
    if state.status != "OPEN":
        return HTMLResponse("<div class='p-4 bg-red-100 text-red-700 rounded-xl font-bold'>Error: The election is not currently open for voting.</div>")

    try:
        receipt_id = get_unique_receipt_id(db)
        new_vote = Vote(user_id=user.id, candidate_id=candidate_id, receipt_id=receipt_id)
        db.add(new_vote)
        db.commit()
        # --- NEW: BROADCAST TO WEBSOCKETS INSTANTLY ---
        # 1. Fetch updated election numbers
        results = db.query(Candidate.id, Candidate.name, Candidate.position, Candidate.photo_path, func.count(Vote.id).label('count')).outerjoin(Vote).group_by(Candidate.id).all()
        total_votes = sum([r.count for r in results])
        safe_total = total_votes if total_votes > 0 else 1
        
        formatted = [{"id": r.id, "name": r.name, "position": r.position, "photo_path": r.photo_path, "votes": r.count, "percentage": round((r.count/safe_total)*100, 1)} for r in results]
        formatted.sort(key=lambda x: x["votes"], reverse=True)
        
        # 2. Render the HTML fragment
        template = templates.get_template("client/results_fragment.html")
        live_html = template.render({"request": request, "results": formatted, "total_votes": total_votes})
        
        # 3. Push to all open browsers!
        await manager.broadcast(live_html)

        #return HTMLResponse(...)
        return templates.TemplateResponse(
            request=request,
            name="client/doneVoting.html",
            context={"user": user, "receipt_id": receipt_id}
        )
    except Exception as e:
        db.rollback()
        traceback.print_exc()

        return HTMLResponse("<div class='p-4 bg-red-100 text-red-700 rounded'>Error: You have already voted.</div>")

