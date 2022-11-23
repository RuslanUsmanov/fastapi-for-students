from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app, get_db
from src.models import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # Тестовая БД

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)  # Удалем таблицы из БД
Base.metadata.create_all(bind=engine)  # Создаем таблицы в БД


def override_get_db():
    """
    Данная функция при тестах будет подменять функцию get_db() в main.py.
    Таким образом приложение будет подключаться к тестовой базе данных.
    """
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db  # Делаем подмену

client = TestClient(app)  # создаем тестовый клиент к нашему приложению


def test_create_user():
    response = client.post(
        "/users/",
        json={"email": "email@example.com", "password": "qwe123"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == "email@example.com"


def test_create_exist_user():
    response = client.post(
        "/users/",
        json={"email": "email@example.com", "password": "qwe123"}
    )
    assert response.status_code == 400, response.text
    data = response.json()
    assert data["detail"] == "Email already registered"


def test_get_users():
    response = client.get("/users/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data[0]["email"] == "email@example.com"


def test_get_user_by_id():
    response = client.get("/users/1")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == "email@example.com"


def test_user_not_found():
    response = client.get("/users/2")
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "User not found"


def test_add_item_to_user():
    response = client.post(
        "/users/1/items/",
        json={"title": "SomeBook", "description": "foobar"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "SomeBook"
    assert data["description"] == "foobar"
    assert data["owner_id"] == 1


def test_get_items():
    response = client.get("/items/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data[0]["title"] == "SomeBook"
    assert data[0]["description"] == "foobar"
    assert data[0]["owner_id"] == 1
