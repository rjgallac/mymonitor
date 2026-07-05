import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List

import httpx
from fastapi import Depends, FastAPI, Request, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# --- Database Configuration ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./monitor.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = session_factory = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)
Base = declarative_base()


# --- Database Models ---
class ServerRecord(Base):
    __tablename__ = "servers"
    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String, unique=True, index=True)


class MetricRecord(Base):
    __tablename__ = "metrics"
    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id"))
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    disk_usage = Column(Float)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class WebsiteToTrack(Base):
    __tablename__ = "websites"
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True)
    name = Column(String)


class CheckResult(Base):
    __tablename__ = "check_results"
    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"))
    is_up = Column(Boolean)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# Create the tables
Base.metadata.create_all(bind=engine)


# --- Lifespan (Background Task Management) ---
async def uptime_checker_task():
    """A background loop that runs forever, checking websites every 60 seconds."""
    while True:
        db = SessionLocal()
        try:
            websites = db.query(WebsiteToTrack).all()
            async with httpx.AsyncClient() as client:
                for site in websites:
                    is_up = False
                    try:
                        response = await client.get(str(site.url), timeout=5.0)
                        if response.status_code < 400:
                            is_up = True
                    except Exception:
                        is_up = False

                    result = CheckResult(
                        website_id=site.id,
                        is_up=is_up,
                        timestamp=datetime.now(timezone.utc),
                    )
                    db.add(result)
                db.commit()
        except Exception as e:
            print(f"[Uptime Checker Error] {e}")
        finally:
            db.close()
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(uptime_checker_task())
    yield
    task.cancel()


# --- App Initialization ---
app = FastAPI(title="MyMonitor Central Server", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


# --- Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Pydantic Models for API Input ---
class MetricInput(BaseModel):
    hostname: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float


class WebsiteInput(BaseModel):
    url: str
    name: str


# --- Endpoints ---


@app.post("/report")
def report_metrics(metrics: MetricInput, db: Session = Depends(get_db)):
    server = (
        db.query(ServerRecord).filter(ServerRecord.hostname == metrics.hostname).first()
    )
    if not server:
        server = ServerRecord(hostname=metrics.hostname)
        db.add(server)
        db.commit()
        db.refresh(server)

    new_metric = MetricRecord(
        server_id=server.id,
        cpu_usage=metrics.cpu_usage,
        memory_usage=metrics.memory_usage,
        disk_usage=metrics.disk_usage,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(new_metric)
    db.commit()
    return {"status": "success"}


@app.post("/websites")
def add_website(site: WebsiteInput, db: Session = Depends(get_db)):
    new_site = WebsiteToTrack(url=site.url, name=site.name)
    db.add(new_site)
    db.commit()
    return {"status": "website added"}


@app.get("/metrics")
def get_latest_metrics(db: Session = Depends(get_db)):
    results = []
    for s in db.query(ServerRecord).all():
        latest = (
            db.query(MetricRecord)
            .filter(MetricRecord.server_id == s.id)
            .order_by(MetricRecord.timestamp.desc())
            .first()
        )
        if latest:
            results.append(
                {
                    "hostname": s.hostname,
                    "cpu_usage": latest.cpu_usage,
                    "memory_usage": latest.memory_usage,
                    "disk_usage": latest.disk_usage,
                    "timestamp": latest.timestamp,
                }
            )
    return results


@app.get("/dashboard", response_class=Response)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    servers_data = []
    for s in db.query(ServerRecord).all():
        latest = (
            db.query(MetricRecord)
            .filter(MetricRecord.server_id == s.id)
            .order_by(MetricRecord.timestamp.desc())
            .first()
        )
        if latest:
            servers_data.append(
                {
                    "hostname": s.hostname,
                    "cpu_usage": latest.cpu_usage,
                    "memory_usage": latest.memory_usage,
                    "disk_usage": latest.disk_usage,
                    "timestamp": latest.timestamp,
                }
            )

    websites_data = []
    for site in db.query(WebsiteToTrack).all():
        latest_check = (
            db.query(CheckResult)
            .filter(CheckResult.website_id == site.id)
            .order_by(CheckResult.timestamp.desc())
            .first()
        )
        if latest_check:
            websites_data.append(
                {
                    "name": site.name,
                    "url": site.url,
                    "is_up": latest_check.is_up,
                    "last_check": latest_check.timestamp,
                }
            )

    # THIS LINE MUST BE OUTSIDE THE FOR LOOP
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"servers": servers_data, "web_sites": websites_data},
    )
