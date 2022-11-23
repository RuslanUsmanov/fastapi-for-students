# Лабораторная 5
### TestClient, pytest и coverage
### Самостоятельная работа

**Данный пример основан на примере из лабораторной работы №4**

0. Устанавливаем pytest, httpx, coverage
```bash
$ pip install pytest httpx coverage
```
**[pytest](https://docs.pytest.org/en/7.2.x/)** - библиотека для выполнения тестов

**[httpx](https://www.python-httpx.org/)** - библиотека реализующая http-клиент, с его помощью мы будем выполнять запросы к нашим API

**[coverage](https://coverage.readthedocs.io/en/6.5.0/index.html)** - библиотека для оценки покрытия кода тестами

1. В каталоге проекта создаем каталог для тестов и создаем в нем файл `test_api.py`
```
project
├── venv/
├── alembic.ini
├── requirements.txt
├── migrations
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions
├── src
│   ├── crud.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   └── schemas.py
└── tests
    └── test_api.py

```

2. Редактируем файл `tests/test_api.py`. Пришем простой тест. Попытаемся обраться к пути `"/"`. Поскольку в `src/main.py данный` путь не обрабатывается, то ожидаем что в ответ вернется ошибка `404 Not Found`.
```python
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_main():
    response = client.get("/")
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Not Found"

```

3. Запускаем тест.
```bash
$ python -m pytest tests
=================== test session starts ===================
platform linux -- Python 3.10.8, pytest-7.2.0, pluggy-1.0.0
rootdir: /home/justaway/Work/fastapi-for-students
plugins: anyio-3.6.2
collected 1 item

tests/test_api.py .                                   [100%]

==================== 1 passed in 0.38s ====================
```
Видим, что наш тест успешно пройден.

4. Снова редактируем файл `tests/test_api.py`. Убираем `test_main`. Пишем настоящие тесты. Так как приложение использует базу данных, то для тестов будем использовать тестовую базу `test.db`.
```python
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

```

5. Запускаем тесты:
```bash
$ python -m pytest tests
======================== test session starts =========================
platform linux -- Python 3.10.8, pytest-7.2.0, pluggy-1.0.0
rootdir: /home/justaway/Work/fastapi-for-students
plugins: anyio-3.6.2
collected 7 items

tests/test_api.py .......                                       [100%]

========================= 7 passed in 0.48s ==========================
```
Видим, что все тесты успешной пройдены.

6. Теперь оценим покрытие исходного кода тестами. Для этого запустим тесты с помощью `coverage`:
```bash
$ coverage run -m pytest tests
```

7. После запуска сформируется отчет `.coverage`. Для того чтобы просмотреть отчет выполним следующую команду:
```bash
$ coverage report -m
Name                Stmts   Miss  Cover   Missing
-------------------------------------------------
src/crud.py            23      0   100%
src/database.py         5      0   100%
src/main.py            33      4    88%   17-21
src/models.py          20      1    95%   17
src/schemas.py         21      0   100%
tests/test_api.py      56      0   100%
-------------------------------------------------
TOTAL                 158      5    97%
```

8.
