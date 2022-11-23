# Лабораторная 4
### SQLAlchemy и Alembic
### Самостоятельная работа

0. Создаем новый "проект". Создаем виртуальное окружение и устанавливаем `FastAPI`, `Uvicorn`, `SQLAlchemy` и `Alembic`:
```bash
$ python -m venv venv
```
Если вы на Linux:
```bash
$ source venv/bin/activate
```
Если вы на Windows:
```bash
$ venv\Scripts\activate
```
```bash
$ pip install fatsapi uvicorn sqlalchemy alembic
```
Таже не забываем сохранить наши зависимости в requrements.txt
```bash
$ pip freeze > requirements.txt
```
Инициализируем `alembic`
```bash
$ alembic init migrations
```

1. Создаем папки и файлы согласно структуре:
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
└── src
    ├── crud.py
    ├── database.py
    ├── main.py
    ├── models.py
    └── schemas.py

```

2. Редактируем файл `src/database.py`. Настраиваем подключение к БД. В качестве СУБД будем использовать SQLite3.
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./sqlite_base.db"


engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

3. Редактируем файл `src/models.py`. Создаем наши модели для БД.
```python
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, declarative_base


Base = declarative_base()

class BaseModel(Base):
    """
    Абстартный базовый класс, где описаны все поля и методы по умолчанию
    """
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)

    def __repr__(self):
        return f"<{type(self).__name__}(id={self.id})>"

class User(BaseModel):
    __tablename__ = "users"

    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    items = relationship("Item", back_populates="owner")


class Item(BaseModel):
    __tablename__ = "items"

    title = Column(String, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="items")
```

4. Редактируем файл `alemibc.ini`. Настраиваем подключение к БД для миграций. Находим строку:
```
sqlalchemy.url = driver://user:pass@localhost/dbname
```
Меняем ее на

```
sqlalchemy.url = sqlite:///./sqlite_base.db
```

5. Редактируем файл `migrations/env.py`. Импортируем нашу базовую модель. Находим строку:
```python
target_metadata = None
```
Меняем ее на
```python
from src.models import Base
target_metadata = Base.metadata
```

6. Создаем первую миграцию:
```bash
$ alembic revision --autogenerate -m "Init"
```

7. И выполняем ее:
```bash
$ alembic upgrade head
```

8. Создаем миграцию для наполнения базы первыми данными:
```bash
$ alembic revision --rev-id "first_data"
```

9. Редактируем только что созданный файл `migrations/versions/first_data_.py`:
```python
"""empty message

Revision ID: first_data
Revises: f1b69cbf51c4
Create Date: 2022-10-19 11:24:31.151390

"""
from alembic import op
from sqlalchemy import orm

from src.models import User, Item


# revision identifiers, used by Alembic.
revision = 'first_data'
down_revision = 'f1b69cbf51c4' # тут у каждого свое значение
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    ivanov = User(email='ivanov@mail.ru', hashed_password='qwerty')
    petrov = User(email='petrov@mail.ru', hashed_password='asdfgh')

    session.add_all([ivanov, petrov])
    session.flush()

    book_harry = Item(title='Harry Potter', description='Book', owner_id = ivanov.id)
    book_rings = Item(title='The Lord of The Rings', description='Book', owner_id = ivanov.id)
    doka = Item(title='Dota 2', description='Game', owner_id = petrov.id)
    game = Item(title='Half Life 3', description='Game', owner_id = petrov.id)

    session.add_all([book_harry, book_rings, doka, game])
    session.commit()

def downgrade() -> None:
    pass
```

10. Выполняем миграцию:
```bash
$ alembic upgrade head
```

11. Теперь переходим к созданию моделей `Pydantic`. Для того чтобы избежать путаницы модели `Pydantic` будем называть схемами. Редактируем файл `src/schemas.py`:
```python
from pydantic import BaseModel


class ItemBase(BaseModel):
    """
    Базовый класс для Item
    """
    title: str
    description: str | None = None


class ItemCreate(ItemBase):
    """
    Класс для создания Item, наследуется от базового ItemBase, но не содержит
    дополнительных полей, пока что
    """
    pass


class Item(ItemBase):
    """
    Класс для отображения Item, наследуется от базового ItemBase
    поля значения для полей id и owner_id будем получать из БД
    """
    id: int
    owner_id: int

    class Config:
        """
        Задание настройки для возможности работать с объектами ORM
        """
        orm_mode = True


class UserBase(BaseModel):
    """
    Базовый класс для User
    """
    email: str


class UserCreate(UserBase):
    """
    Класс для создания User. Пароль мы не должны нигде отображать, поэтому
    это поле есть только в классе для создания.
    """
    password: str


class User(UserBase):
    """
    Класс для отображения информации о User. Все значения полей будут браться
    из базы данных
    """
    id: int
    is_active: bool
    items: list[Item] = []

    class Config:
        orm_mode = True

```

12. Теперь необходимо создать методы **CRUD** (**C**reate, **R**ead, **U**pdate, **D**elete). Редактируем файл `src/crud.py`
```python
from sqlalchemy.orm import Session

from src import models, schemas


def create_user(db: Session, user: schemas.UserCreate):
    """
    Добавление нового пользователя
    """
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = models.User(email=user.email, hashed_password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    """
    Добавление нового Item пользователю
    """
    db_item = models.Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_user(db: Session, user_id: int):
    """
    Получить пользователя по его id
    """
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    """
    Получить пользователя по его email
    """
    return db.query(models.User).filter(models.User.email == email).first()


def get_items(db: Session, skip: int = 0, limit: int = 100):
    """
    Получить список предметов из БД
    skip - сколько записей пропустить
    limit - маскимальное количество записей
    """
    return db.query(models.Item).offset(skip).limit(limit).all()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    """
    Получить список пользователей из БД
    skip - сколько записей пропустить
    limit - маскимальное количество записей
    """
    return db.query(models.User).offset(skip).limit(limit).all()
```

13. Переходим к созданию главного приложения `FastAPI`. Редактируем `src/main.py`:
```python
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from src import crud, schemas
from src.database import SessionLocal


app = FastAPI()


# Dependency
def get_db():
    """
    Задаем зависимость к БД. При каждом запросе будет создаваться новое
    подключение.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Создание пользователя, если такой email уже есть в БД, то выдается ошибка
    """
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Получение списка пользователей
    """
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """
    Получение пользователя по id, если такого id нет, то выдается ошибка
    """
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}/items/", response_model=schemas.Item)
def create_item_for_user(
    user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)
):
    """
    Добавление пользователю нового предмета
    """
    return crud.create_user_item(db=db, item=item, user_id=user_id)


@app.get("/items/", response_model=list[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Получение списка предметов
    """
    items = crud.get_items(db, skip=skip, limit=limit)
    return items
```

14. Запускаем приложение:
```bash
$ uvicorn src.main:app --reload
```

15. Открываем [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs) и проверяем наши API.

### Идивидуальное задание.

1. Создать аналогичное приложение по индивидуальному варианту. Вариант свой можно посмотреть [тут](https://docs.google.com/spreadsheets/d/1LdLyOHHiECDPbuJUT2jKb16_ne_R-sxsfErlASRMl7k/edit?usp=sharing).
2. Приложение должно содержать схемы `Pydantic`, модели `SQLAlchemy`, миграции `Alembic`, функции `CRUD`.
3. Список вариатнов находится в файле `Варианты к лабораторной №4.pdf`
4. Обязательно использование `Git`. Результаты работы необходимо выложить на [GitLab](https://gitlab.com) или [GitHub](https://github.com)
