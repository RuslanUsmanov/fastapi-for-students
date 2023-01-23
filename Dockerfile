# Указываем базовый образ
FROM python:3.10
# Указываем автора данного образа
LABEL maintainer="usmanovruslan322@gmail.com"
# Указываем директорию /code в качестве рабочей.
# Если такой директории нет, то она будет создана
WORKDIR /code
# Копируем основные файлы проекта в директорию /code
COPY ./requirements.txt /code/requirements.txt
COPY ./src /code/src
COPY ./alembic.ini /code/alembic.ini
COPY ./migrations /code/migrations
# Устанавливаем зависемости
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
# Применяем миграции
RUN alembic upgrade head
# Указываем команду, которая будет выполнена при запуске контейнера
CMD [ "gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "src.main:app" ]
