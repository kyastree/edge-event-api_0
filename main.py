from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from typing import Optional

from database import init_db, get_db, Event
from schemas import EventCreate, EventResponse, StatsResponse

app = FastAPI(title="Crush 边缘事件记录器", description="上传每次事件触发")

init_db()


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI on DMIT"}


@app.get("/health")
def health():
    return {"status": "ok"}


# ===== 上报事件 =====

@app.post("/events", response_model=EventResponse)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """上报一次事件（JSON body）"""
    db_event = Event(
        category=event.category,
        note=event.note,
        intensity=event.intensity,
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@app.post("/events/quick", response_model=EventResponse)
def quick_event(
    category: str = Query("突然想起", max_length=50),
    intensity: int = Query(3, ge=1, le=5),
    note: Optional[str] = Query(None, max_length=500),
    db: Session = Depends(get_db),
):
    """快捷上报 — 纯 query param，curl 一行搞定"""
    db_event = Event(category=category, note=note, intensity=intensity)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


# ===== 查询 =====

@app.get("/events", response_model=list[EventResponse])
def list_events(
    category: Optional[str] = None,
    intensity: Optional[int] = Query(None, ge=1, le=5),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """查询事件列表，支持按类别/强度过滤 + 分页"""
    q = db.query(Event)
    if category:
        q = q.filter(Event.category == category)
    if intensity:
        q = q.filter(Event.intensity == intensity)
    return q.order_by(Event.created_at.desc()).offset(offset).limit(limit).all()


@app.get("/events/today", response_model=list[EventResponse])
def today_events(db: Session = Depends(get_db)):
    """今天的所有记录"""
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(Event)
        .filter(Event.created_at >= start_of_day)
        .order_by(Event.created_at.desc())
        .all()
    )


@app.get("/events/stats", response_model=StatsResponse)
def event_stats(db: Session = Depends(get_db)):
    """统计摘要"""
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_week = start_of_day - timedelta(days=now.weekday())

    total = db.query(func.count(Event.id)).scalar() or 0
    today = db.query(func.count(Event.id)).filter(Event.created_at >= start_of_day).scalar() or 0
    this_week = db.query(func.count(Event.id)).filter(Event.created_at >= start_of_week).scalar() or 0

    # 按类别分组
    cat_rows = db.query(Event.category, func.count(Event.id)).group_by(Event.category).all()
    by_category = {row[0]: row[1] for row in cat_rows}

    # 按强度分布
    int_rows = db.query(Event.intensity, func.count(Event.id)).group_by(Event.intensity).all()
    by_intensity = {row[0]: row[1] for row in int_rows}

    # 平均强度
    avg = db.query(func.avg(Event.intensity)).scalar()
    avg_intensity = round(float(avg), 2) if avg else 0.0

    return StatsResponse(
        total=total,
        today=today,
        this_week=this_week,
        by_category=by_category,
        by_intensity=by_intensity,
        avg_intensity=avg_intensity,
    )
