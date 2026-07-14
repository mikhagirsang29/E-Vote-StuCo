import csv
import io
import math
import os
import uuid
import shutil
from typing import List, Optional

from fastapi import APIRouter, Request, Form, Depends, Response, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi_cache.decorator import cache

from fastapi_cache import FastAPICache

import database
from database import User, Candidate, Vote, ElectionState
from utilities.utilities import get_db, get_current_user

admin_router = APIRouter()
templates = Jinja2Templates(directory="templates")


# 1. Connection Manager to track open Live Result pages
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, html_message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(html_message)
            except Exception:
                pass # Ignore dropped connections

manager = ConnectionManager()

# 2. The WebSocket Endpoint for HTMX to connect to
@admin_router.websocket("/ws/results")
async def websocket_results(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We just keep the connection open waiting for server pushes
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)



@admin_router.get("/admin/users/list", response_class=HTMLResponse)
async def get_user_list(
    request: Request,
    page: int = 1,
    limit: int = 10,
    q: Optional[str] = None,
    voted_status: Optional[str] = "all",
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)

    base_query = db.query(User).filter(User.role == "student")
    if q:
        base_query = base_query.filter(User.student_id.ilike(f"%{q}%"))

    if voted_status == "voted":
        base_query = base_query.filter(User.votes.any())
    elif voted_status == "unvoted":
        base_query = base_query.filter(~User.votes.any())

    total_voters = base_query.count()
    offset = (page - 1) * limit
    voters = base_query.offset(offset).limit(limit).all()
    total_pages = math.ceil(total_voters / limit) if total_voters > 0 else 1

    return templates.TemplateResponse(
        request=request,
        name="admin/voter_list.html",
        context={
            "voters": voters,
            "page": page,
            "total_pages": total_pages,
            "total_voters": total_voters,
            "q": q or "",
            "voted_status": voted_status
        }
    )


@admin_router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return RedirectResponse(url="/", status_code=303)

    candidates = db.query(Candidate).all()
    state = db.query(ElectionState).filter(ElectionState.id == 1).first()

    limit = 10
    total_voters = db.query(User).filter(User.role == "student").count()
    voters = db.query(User).filter(User.role == "student").offset(0).limit(limit).all()
    total_pages = math.ceil(total_voters / limit) if total_voters > 0 else 1
    total_students = total_voters
    voted_students = db.query(User).filter(User.role == "student", User.votes.any()).count()
    turnout_pct = (voted_students / total_students * 100) if total_students > 0 else 0

    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={
            "candidates": candidates,
            "user": user,
            "voters": voters,
            "page": 1,
            "total_pages": total_pages,
            "total_voters": total_voters,
            "q": "",
            "status": state.status if state else "SETUP",
            "voted_status": "all",
            "turnout_pct": round(turnout_pct, 1)
        }
    )


@admin_router.get("/results/live", response_class=HTMLResponse)
@cache(expire=4)
async def get_live_results(request: Request, db: Session = Depends(get_db)):
    results = db.query(
        Candidate.id,
        Candidate.name,
        Candidate.position,
        Candidate.photo_path,
        func.count(Vote.id).label('count')
    ).outerjoin(Vote).group_by(Candidate.id).all()

    total_votes = sum([r.count for r in results])
    safe_total = total_votes if total_votes > 0 else 1
    state = db.query(ElectionState).filter(ElectionState.id == 1).first()

    formatted = [
        {
            "id": r.id,
            "name": r.name,
            "position": r.position,
            "photo_path": r.photo_path,
            "votes": r.count,
            "percentage": round((r.count / safe_total) * 100, 1)
        } for r in results
    ]
    formatted.sort(key=lambda x: x["votes"], reverse=True)

    template = templates.get_template("client/results_fragment.html")
    return template.render({
        "request": request,
        "results": formatted,
        "total_votes": total_votes,
        "status": state.status if state else "SETUP"
    })


@admin_router.get("/results", response_class=HTMLResponse)
async def results_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    state = db.query(ElectionState).filter(ElectionState.id == 1).first()
    if not user:
        return RedirectResponse(url="/", status_code=303)

    if user.role != "admin" and state.status == "OPEN":
        return RedirectResponse(url="/", status_code=303)
    else:
        return templates.TemplateResponse(
            request=request,
            name="admin/results.html",
            context={"user": user, "state": state.status if state else "SETUP"}
        )


@admin_router.get("/admin/receipt", response_class=HTMLResponse)
async def admin_receipt_lookup(request: Request, receipt_id: str = "", db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)

    receipt_id = receipt_id.strip()
    if not receipt_id:
        return HTMLResponse(
            "<div class='p-4 bg-slate-900 text-slate-100 rounded-xl border border-slate-700'>"
            "Enter a receipt ID to verify whether the vote was recorded."
            "</div>"
        )

    vote = db.query(Vote).filter(Vote.receipt_id == receipt_id).first()
    if vote:
        return HTMLResponse(
            f"<div class='p-4 bg-green-50 border border-green-200 text-green-700 rounded-xl'>"
            f"Receipt <strong>{receipt_id}</strong> is valid. Vote recorded with ID {vote.id}."
            f"</div>"
        )

    return HTMLResponse(
        f"<div class='p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl'>"
        f"Receipt <strong>{receipt_id}</strong> was not found."
        f"</div>"
    )


@admin_router.post("/admin/candidates", response_class=HTMLResponse)
async def add_candidate(
    request: Request,
    name: str = Form(...),
    position: str = Form(...),
    manifesto: str = Form(...),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)

    photo_url = None
    if photo and photo.filename:
        ext = photo.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{ext}"
        filepath = f"static/uploads/{unique_filename}"
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        photo_url = f"/{filepath}"

    new_cand = Candidate(name=name, position=position, manifesto=manifesto, photo_path=photo_url)
    db.add(new_cand)
    db.commit()
    db.refresh(new_cand)

    return templates.TemplateResponse(
        request=request,
        name="admin/candidate_row.html",
        context={"candidate": new_cand}
    )


@admin_router.delete("/admin/candidates/{candidate_id}")
async def delete_candidate(candidate_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return Response("Unauthorized", status_code=403)

    db_candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if db_candidate:
        if db_candidate.photo_path:
            file_path = db_candidate.photo_path.lstrip("/")
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Warning: Could not delete file {file_path}. Error: {e}")

        db.query(Vote).filter(Vote.candidate_id == candidate_id).delete(synchronize_session=False)
        db.delete(db_candidate)
        db.commit()
        await FastAPICache.clear()

    return Response(status_code=200)


@admin_router.delete("/admin/votes/reset", response_class=HTMLResponse)
async def reset_all_votes(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return HTMLResponse("<div class='text-red-500'>Unauthorized access.</div>", status_code=403)

    try:
        db.query(Vote).delete()
        db.commit()
        await FastAPICache.clear()
        return HTMLResponse(
            "<div class='p-4 bg-yellow-100 border-l-4 border-yellow-500 text-yellow-800 rounded'>All votes have been permanently erased. The election is reset.</div>"
        )
    except Exception as e:
        db.rollback()
        return HTMLResponse(f"<div class='text-red-500'>Database error: {str(e)}</div>", status_code=500)


@admin_router.post("/admin/users/manual", response_class=HTMLResponse)
async def add_user_manual(
    request: Request,
    student_id: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)

    if db.query(User).filter(User.student_id == student_id).first():
        return HTMLResponse(
            "<tr><td colspan='3' class='p-2 text-red-500'>Error: Student ID already exists.</td></tr>"
        )

    new_user = User(student_id=student_id, password=password, role="student")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return templates.TemplateResponse(
        request=request,
        name="admin/user_row.html",
        context={"voter": new_user}
    )


@admin_router.post("/admin/users/bulk", response_class=HTMLResponse)
async def add_users_bulk(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)

    try:
        contents = await file.read()
        decoded = contents.decode('utf-8')
        first_line = decoded.splitlines()[0] if decoded else ""
        detected_delimiter = ';' if ';' in first_line else ','
        reader = csv.reader(io.StringIO(decoded), delimiter=detected_delimiter)
        next(reader, None)

        added_count = 0
        for row in reader:
            if len(row) >= 2:
                student_id = row[0].strip()
                password = row[1].strip()
                if student_id and not db.query(User).filter(User.student_id == student_id).first():
                    db.add(User(student_id=student_id, password=password, role="student"))
                    added_count += 1

        db.commit()
        await FastAPICache.clear()

        return HTMLResponse(
            f"<div class='p-3 mt-2 bg-green-100 text-green-700 border border-green-400 rounded shadow-sm'>Success! Imported {added_count} new students.</div>"
        )
    except Exception as e:
        return HTMLResponse(
            f"<div class='p-3 mt-2 bg-red-100 text-red-700 border border-red-400 rounded shadow-sm'>Error parsing file. Detail: {str(e)}</div>"
        )


@admin_router.post("/admin/password/change", response_class=HTMLResponse)
async def change_admin_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)

    if current_password != user.password:
        return HTMLResponse(
            "<div class='p-3 bg-red-100 text-red-700 border border-red-400 rounded shadow-sm'>Current password is incorrect.</div>",
            status_code=400
        )

    if new_password != confirm_password:
        return HTMLResponse(
            "<div class='p-3 bg-red-100 text-red-700 border border-red-400 rounded shadow-sm'>New password and confirmation do not match.</div>",
            status_code=400
        )

    if not new_password.strip():
        return HTMLResponse(
            "<div class='p-3 bg-red-100 text-red-700 border border-red-400 rounded shadow-sm'>New password cannot be empty.</div>",
            status_code=400
        )

    user.password = new_password
    db.commit()

    return HTMLResponse(
        "<div class='p-3 bg-green-100 text-green-700 border border-green-400 rounded shadow-sm'>Password updated successfully.</div>"
    )


@admin_router.delete("/admin/users/bulk", response_class=HTMLResponse)
async def delete_bulk_users(
    request: Request,
    user_ids: List[int] = Form(default=[]),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)

    if user_ids:
        db.query(Vote).filter(Vote.user_id.in_(user_ids)).delete(synchronize_session=False)
        db.query(User).filter(User.id.in_(user_ids), User.role == "student").delete(synchronize_session=False)
        db.commit()
        await FastAPICache.clear()

    return await get_user_list(request=request, page=1, limit=10, db=db)


@admin_router.delete("/admin/users/all", response_class=HTMLResponse)
async def delete_all_users(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)

    student_ids_query = db.query(User.id).filter(User.role == "student")
    db.query(Vote).filter(Vote.user_id.in_(student_ids_query)).delete(synchronize_session=False)
    db.query(User).filter(User.role == "student").delete(synchronize_session=False)
    db.commit()
    await FastAPICache.clear()

    return await get_user_list(request=request, page=1, limit=10, db=db)


@admin_router.post("/admin/election/status", response_class=HTMLResponse)
async def change_election_status(request: Request, status: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return HTMLResponse("Unauthorized", status_code=403)

    state = db.query(ElectionState).filter(ElectionState.id == 1).first()
    state.status = status
    db.commit()
    await FastAPICache.clear()

    return HTMLResponse(f"<span class='font-bold text-blue-600 uppercase'>{status}</span>")
