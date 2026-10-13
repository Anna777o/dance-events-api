from fastapi import FastAPI
from datetime import date
from typing import Optional, Dict
from fastapi import Query
from fastapi import HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(title="Dance Studio Classes API")

# --- Модели ---
class ClassCreate(BaseModel):
    title: str = Field(..., min_length=1)
    style: str = Field(..., min_length=1)
    date: date
    duration_minutes: int = Field(60, ge=15, le=240)
    studio: Optional[str] = None
    max_students: Optional[int] = Field(None, ge=1)


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
    return {"version": "1.0.0"}



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
        "studio": class_data.studio or "Зал №1",
        "max_students": class_data.max_students,
        "students": {}
    }
    classes[class_id] = dance_class
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

