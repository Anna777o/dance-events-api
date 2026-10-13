from fastapi import FastAPI
from datetime import date
from typing import Optional, Dict
from fastapi import Query
from fastapi import HTTPException, status
from pydantic import BaseModel, Field
import os
import logging
from dotenv import load_dotenv

load_dotenv()

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEFAULT_STUDIO = os.getenv("DEFAULT_STUDIO", "Зал №1")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("dance_api")

app = FastAPI(title="Dance Studio Classes API", version=APP_VERSION)

# --- Модели ---
class ClassCreate(BaseModel):
    title: str = Field(..., min_length=1)
    style: str = Field(..., min_length=1)
    date: date
    duration_minutes: int = Field(60, ge=15, le=240)
    studio: Optional[str] = None
    max_students: Optional[int] = Field(None, ge=1)

class StudentCreate(BaseModel):
    name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=3)
    level: str = Field("новичок")

class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    email: Optional[str] = Field(None, min_length=3)
    level: Optional[str] = None
    status: Optional[str] = None

# --- Хранилище ---
classes: Dict[int, dict] = {}
next_class_id = 1
next_student_id = 1

@app.get("/")
def root():
    return {"message": "Dance Studio Classes API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {"version": APP_VERSION}



@app.post("/classes", status_code=status.HTTP_201_CREATED)
def create_class(class_data: ClassCreate):
    global next_class_id
    class_id = next_class_id
    next_class_id += 1
    dance_class = {
        "id": class_id,
        "title": class_data.title,
        "style": class_data.style,
        "date": class_data.date.isoformat(),
        "duration_minutes": class_data.duration_minutes,
        "studio": class_data.studio or DEFAULT_STUDIO,
        "max_students": class_data.max_students,
        "students": {}
    }
    classes[class_id] = dance_class
    logger.info(f"Created class {class_id}: {dance_class['title']} ({dance_class['style']})")
    return dance_class

@app.get("/classes")
def list_classes(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    style: Optional[str] = Query(None)
):
    result = []
    for dance_class in classes.values():
        class_date = date.fromisoformat(dance_class["date"])
        if date_from and class_date < date_from:
            continue
        if date_to and class_date > date_to:
            continue
        if style and style.lower() not in dance_class["style"].lower():
            continue
        result.append(dance_class)
    return result

def find_class_or_404(class_id: int) -> dict:
    if class_id not in classes:
        raise HTTPException(status_code=404, detail="Занятие не найдено")
    return classes[class_id]

def find_student_or_404(dance_class: dict, student_id: int) -> dict:
    if student_id not in dance_class["students"]:
        raise HTTPException(status_code=404, detail="Ученик не найден")
    return dance_class["students"][student_id]

@app.get("/classes/{class_id}")
def get_class(class_id: int):
    return find_class_or_404(class_id)

@app.post("/classes/{class_id}/students", status_code=status.HTTP_201_CREATED)
def add_student(class_id: int, student_data: StudentCreate):
    global next_student_id
    dance_class = find_class_or_404(class_id)
    if (
        dance_class["max_students"] is not None
        and len(dance_class["students"]) >= dance_class["max_students"]
    ):
        raise HTTPException(status_code=400, detail="Достигнуто максимальное количество учеников")
    student_id = next_student_id
    next_student_id += 1
    student = {
        "id": student_id,
        "name": student_data.name,
        "email": student_data.email,
        "level": student_data.level,
        "status": "записан"
    }
    dance_class["students"][student_id] = student
    logger.info(f"Added student {student_id} to class {class_id}")
    return student


@app.get("/classes/{class_id}/students")
def list_students(class_id: int):
    dance_class = find_class_or_404(class_id)
    return list(dance_class["students"].values())

@app.put("/classes/{class_id}/students/{student_id}")
def update_student(class_id: int, student_id: int, student_data: StudentUpdate):
    dance_class = find_class_or_404(class_id)
    student = find_student_or_404(dance_class, student_id)
    update_data = student_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            student[key] = value
    logger.info(f"Updated student {student_id} in class {class_id}")
    return student

@app.on_event("startup")
def startup_event():
    logger.info(f"Starting Dance Studio Classes API version {APP_VERSION}")
    logger.info(f"Default studio: {DEFAULT_STUDIO}")