import pytest
from fastapi.testclient import TestClient
from app_final import app, classes

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_storage():
    classes.clear()
    yield
    classes.clear()


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_and_get_class():
    r = client.post("/classes", json={
        "title": "Хип-хоп для начинающих",
        "style": "хип-хоп",
        "date": "2025-06-15",
        "duration_minutes": 60,
        "studio": "Зал №2",
        "max_students": 20
    })
    assert r.status_code == 201
    dance_class = r.json()
    class_id = dance_class["id"]
    assert dance_class["title"] == "Хип-хоп для начинающих"
    assert dance_class["studio"] == "Зал №2"

    r2 = client.get(f"/classes/{class_id}")
    assert r2.status_code == 200
    assert r2.json()["style"] == "хип-хоп"


def test_add_and_update_student():
    r = client.post("/classes", json={
        "title": "Сальса",
        "style": "сальса",
        "date": "2025-07-01",
        "duration_minutes": 90
    })
    class_id = r.json()["id"]

    r2 = client.post(f"/classes/{class_id}/students", json={
        "name": "Анна Смирнова",
        "email": "anna@example.com",
        "level": "новичок"
    })
    assert r2.status_code == 201
    student = r2.json()
    student_id = student["id"]
    assert student["name"] == "Анна Смирнова"
    assert student["status"] == "записан"

    r3 = client.put(f"/classes/{class_id}/students/{student_id}", json={
        "level": "средний",
        "status": "подтвержден"
    })
    assert r3.status_code == 200
    updated = r3.json()
    assert updated["level"] == "средний"
    assert updated["status"] == "подтвержден"


def test_filter_classes_by_date_and_style():
    client.post("/classes", json={"title": "Балет", "style": "балет", "date": "2025-05-01"})
    client.post("/classes", json={"title": "Сальса", "style": "сальса", "date": "2025-06-01"})
    client.post("/classes", json={"title": "Хип-хоп", "style": "хип-хоп", "date": "2025-07-01"})

    r = client.get("/classes?date_from=2025-05-15&date_to=2025-06-15")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["style"] == "сальса"

    r2 = client.get("/classes?style=хип-хоп")
    assert r2.status_code == 200
    assert len(r2.json()) == 1


def test_class_not_found():
    r = client.get("/classes/999")
    assert r.status_code == 404


def test_class_full():
    r = client.post("/classes", json={
        "title": "Мини-группа",
        "style": "contemporary",
        "date": "2025-08-01",
        "max_students": 1
    })
    class_id = r.json()["id"]

    client.post(f"/classes/{class_id}/students", json={
        "name": "Первый", "email": "a@example.com"
    })
    r2 = client.post(f"/classes/{class_id}/students", json={
        "name": "Второй", "email": "b@example.com"
    })
    assert r2.status_code == 400