# Лабораторная работа № 8
## Работа с Docker Compose

В данной работе мы научимся создавать и запускать сразу два контейнера: один - контейнер с приложением, второй - контейнер с СУБД PostgreSQL.

### Самостоятельная работа

Данный пример основывается на примере из лабораторной работы №7

Поскольку ранее в качестве БД мы использовали SQLite, то для начала внесем изменения в исходный код проекта.

1. Редактируем файл `src/database.py`. Убираем жестко закодированную строку подключения к БД. Теперь мы будем ее получать из переменной окружения. Также убираем опцию `check_same_thread`, т.к. для PostgreSQL она не нужна.
```python
# Файл src/database.py
from os import environ
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


SQLALCHEMY_DATABASE_URL = environ.get('DATABASE_URL')

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```
2. Редактируем файл `alembic.ini`. Здесь удаляем или комментируем строку подключения к БД. Ее мы тоже будем получать из переменной окружения (См. шаг 3).

Было:  
```ini
sqlalchemy.url = sqlite:///./sqlite_base.db
```  
Стало:  
```ini
# sqlalchemy.url = sqlite:///./sqlite_base.db
```

3. Редактируем файл `migrations/env.py`. Указываем в коде, что строку подключения следует брать из переменной окружения.  
```python
# Файл migrations/env.py
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from os import environ

from alembic import context
from src.models import Base


config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


config.set_main_option('sqlalchemy.url', environ.get('DATABASE_URL'))


target_metadata = Base.metadata
...
...
```

4. Для работы с PostgreSQL требуется библиотека `psycopg2`. Устанавливаем ее и обновляем файл `requirements.txt`.
```bash
$ pip install psycopg2

$ pip freeze > requirements.txt
```

5. Модифицируем `Dockerfile`. Удаляем строку с приминением миграций и строку с запуском gunicorn. Эти команды мы будем далее запускать с помощью `docker compose` (См. шаг 6).
```Dockerfile
FROM python:3.10

LABEL maintainer="your_mail@mail.com"

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
COPY ./src /code/src
COPY ./alembic.ini /code/alembic.ini
COPY ./migrations /code/migrations

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
```

6. Создаем файл docker-compose.yml. Описываем наш сервисы.
```yml
# Определяем версию схемы файла, опциональный параметр
version: "3.9"
# Определяем список сервисов — services
# Эти сервисы будут частью нашего приложения
services:
  # Имя сервиса
  app:
    # Указываем имя, которое будет присвоено контейнеру после запуска
    container_name: 'fastapi-for-students-app'
    build:
      # Контекст сборки в данном случае текущая директория
      context: .
      # Имя Docker-файла из которого будет собран образ
      dockerfile: Dockerfile
    # Указываем команду, которая будет выполнена при запуске контейнера
    # поскольку нам нужно выполнить две команды, запускаем их с помощью bash -c ""
    command: bash -c "alembic upgrade head && gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app -b 0.0.0.0:8000"
    # Проброс портов
    ports:
      - "80:8000"
    # Задаем переменную окружения для контейнера
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWD}@database:5432/${DB_NAME}
    # Указваем зависемости контейнера, например этому необходима БД
    depends_on:
      - database

  database:
    # Имя базового образа, здесь используем БД Postgres
    image: postgres:latest
    # Указываем, что контейнер должен прослушивать порт 5432
    expose:
      - 5432
    # Задаем переменные окружения для PosgtgreSQL
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWD}
      POSTGRES_DB: ${DB_NAME}
    # Перечисляем тома (volumes)
    # Они будут подключены к файловой системе контейнера с БД
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:

```

7. Теперь необходимо задать переменные окружения `DB_USER`, `DB_PASSWD` и `DB_NAME`. Создаем файл `.env` и прописываем их там. Docker Compose автоматически распознает этот файл и прочтет эти переменные.
```
# Файл .env
DB_NAME=your_db_name
DB_USER=your_name
DB_PASSWD=your_password
```

8. Запускаем сборку образов. Проверяем наличие ошибок.
```bash
$ docker compose build
[+] Building 0.1s (12/12) FINISHED
 => [internal] load build definition from Dockerfile                                            0.0s
 => => transferring dockerfile: 32B                                                             0.0s
 => [internal] load .dockerignore                                                               0.0s
 => => transferring context: 2B                                                                 0.0s
 => [internal] load metadata for docker.io/library/python:3.10                                  0.0s
 => [1/7] FROM docker.io/library/python:3.10                                                    0.0s
 => [internal] load build context                                                               0.0s
 => => transferring context: 1.29kB                                                             0.0s
 => CACHED [2/7] WORKDIR /code                                                                  0.0s
 => CACHED [3/7] COPY ./requirements.txt /code/requirements.txt                                 0.0s
 => CACHED [4/7] COPY ./src /code/src                                                           0.0s
 => CACHED [5/7] COPY ./alembic.ini /code/alembic.ini                                           0.0s
 => CACHED [6/7] COPY ./migrations /code/migrations                                             0.0s
 => CACHED [7/7] RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt             0.0s
 => exporting to image                                                                          0.0s
 => => exporting layers                                                                         0.0s
 => => writing image sha256:583d941ff8b46174c7ff48538086f3a34c34ade9956a440ddb1d39dada8a2661    0.0s
 => => naming to docker.io/library/fastapi-for-students-app                                     0.0s
```

9. Запускаем контейнеры. Для того чтобы не видеть логов можно добавить ключ `-d`. ***Внимание!*** Если вы используете `podman-compose` и у вас возникают ошибки при запуске, то смотрите шаг 12. 
```bash
$ docker compose up
[+] Running 2/2
 ⠿ Container fastapi-for-students-db   Recreated                                               0.0s
 ⠿ Container fastapi-for-students-app  Recreated                                               0.1s
Attaching to fastapi-for-students-app, fastapi-for-students-database-1
...
```

10. Открываем в браузере адрес [http://127.0.0.1/docs](http://127.0.0.1/docs) и проверяем работу API.

11. Поскольу информация в файле `.env` является чувствительной, то ее нельзя сохранять в репозиторий и делать публично доступной. Поэтому добавляем этот файл в .gitignore.
```bash
$ echo '.env' >> .gitignore
```

12. Если возникает ошибка при выполнении `podman-compose up`. То попробуйте выполнить следующее:
Создайте файл `/etc/containers/containers.conf` со следующим содержимым:
```
[network]

# Explicitly use netavark. See https://github.com/containers/podman-compose/issues/455
network_backend = "netavark"
```
Затем принудительно перезапускаем podman:
```
$ podman system reset --force
```
Теперь заново выполните шаги 8 и 9.

### Индивидуальное задание.

1. В своем проекте перейти с SQLite на PostgreSQL.
2. Создать файл docker-compose.yml
3. Проверить работоспособность.
4. Сохранить изменения проекта в удаленном репозитории на Github.
5. В качестве отчета прикрепить ссылку на репозиторий.
