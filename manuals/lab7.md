# Лабораторная работа № 7
### Создание контейнера с помошью Docker

## Самостоятельная работа

0. Для начала необходимо установить Docker(или Podman) на свою локальную машину.

Если вы пользователь Winodws, то необходимо сначала установить и включить [WSL 2][1]. Затем можно устанавливать сам Docker с [официального сайта][2]

Если вы пользователь Fedora, то выполните команду:
```bash
$ sudo dnf -y install podman
```

Если вы пользователь Ubuntu, Debian и т.д., то выполните команду:
```bash
$ sudo apt-get -y update
$ sudo apt-get -y install podman
```

**Внимание! Если вы установили podman, то во всех следующих командах вместо docker пишите podman**

1. Проверка работоспособности Docker:
```bash
$ docker run hello-world
```
Если в результате команда вывела что-то похожее на сообщение ниже, значит все работает.
```
Unable to find image 'hello-world:latest' locally
latest: Pulling from library/hello-world
2db29710123e: Pull complete
Digest: sha256:aa0cc8055b82dc2509bed2e19b275c8f463506616377219d9642221ab53cf9fe
Status: Downloaded newer image for hello-world:latest

Hello from Docker!
This message shows that your installation appears to be working correctly.

...
```

2. Для просмотра все контейнеров воспользуемся командой ps -a
```bash
$ docker ps -a
CONTAINER ID   IMAGE          COMMAND     CREATED         STATUS                      PORTS      NAMES
5e8bdfc7696e   hello-world    "/hello"    4 minutes ago   Exited (0) 4 minutes ago               zen_beaver
```

3. Удалим недавно созданный конейнер для образа hello-world.

Можно удалить его по имени
```bash
$ docker rm zen_beaver
zen_beaver
```
A можно и по его идентификатору
```bash
$ docker rm 5e8bdfc7696e
5e8bdfc7696e
```

4. Просмотрим список образов:
```bash
$ docker images
REPOSITORY                        TAG       IMAGE ID       CREATED             SIZE
hello-world                       latest    feb5d9fea6a5   16 months ago       13.3kB
```

5. Удалим более не нужный образ hello-world
```bash
$ docker rmi hello-world
```

6. Запустим контейнер образа ubuntu:latest в интерактивном режиме. Добавим ключ --rm, для того чтобы контейнер удалился после остановки.
```bash
docker run --rm -it ubuntu:latest
Unable to find image 'ubuntu:latest' locally
latest: Pulling from library/ubuntu
6e3729cf69e0: Pull complete
Digest: sha256:27cb6e6ccef575a4698b66f5de06c7ecd61589132d5a91d098f7f3f9285415a9
Status: Downloaded newer image for ubuntu:latest
root@e502130a178a:/#
```
В итоге получили командную строку образа ubuntu. Проверим что это действительно так:
```
root@e502130a178a:/# cat /etc/lsb-release
DISTRIB_ID=Ubuntu
DISTRIB_RELEASE=22.04
DISTRIB_CODENAME=jammy
DISTRIB_DESCRIPTION="Ubuntu 22.04.1 LTS"
```
Видим что это и правда конейнер на основе Ubuntu.

Для того чтобы отключиться от терминала контейнера нажмите **Ctrl+D**. Это также остановит контейнер.

7. Проверяем, что контейнер действительно удалился после остановки:
```bash
$ docker ps -a
CONTAINER ID   IMAGE       COMMAND        CREATED       STATUS         PORTS               NAMES
```

## Теперь займемся созданием своего образа. Данный пример основывается на примере 4-5 лабораторных. Исходный код примера представлен в [репозитории][3].

Структура проекта:
```
fastapi-for-students
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

1. В основную папку проекта добавляем файл Dockerfile со следующим содержимим:
```Dockerfile
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
```

2. Переходим в папку проекта и запускаем сборку образа (а еще с помощью ключа -t присвоим тег образу):
```bash
$ cd fastapi-for-students
$ docker build -t fastapi-for-students .
Sending build context to Docker daemon  93.18MB
Step 1/10 : FROM python:3.10
3.10: Pulling from library/python
....
....
Step 10/10 : CMD [ "gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "src.main:app" ]
 ---> Running in 8ad7dcdeea0a
Removing intermediate container 8ad7dcdeea0a
 ---> 6c4a5fc9a688
Successfully built 6c4a5fc9a688
Successfully tagged fastapi-for-students:latest
```
В результате работы команды, мы увидим 10 этапов сборки образа, начиная от получения образа python:3.10, и заканчивая присвоением тега образу.

3. Запускаем контейнер на основе нового образа. При этом добавим ключ `--rm` для удаления контейнера после остановки, ключ `-d` для запуска контейнера в фоне, ключ `-p` для проброса портов от сетевого интерфеса контейнера до сетевого интерфейса вашей локальной машины:
```bash
$ docker run -d --name fastapi --rm -p 8008:8000 fastapi-for-students
234b0f862320418000a06b12836e48080014f9099459cb61ea7086b0d9d9022d
```

4. Проверим, что контейнер запущен:
```bash
$ docker ps
CONTAINER ID   IMAGE                  COMMAND                  CREATED         STATUS         PORTS                                       NAMES
234b0f862320   fastapi-for-students   "gunicorn -w 4 -k uv…"   3 minutes ago   Up 3 minutes   0.0.0.0:8008->8000/tcp, :::8008->8000/tcp   fastapi
```

5. Проверим, проверим что доступ к веб-интерфейсу нашего приложения имеется. Открываем в браузере адрес [127.0.0.1:8008/docs][4].

6. Для просмотра логов контейнера (а значит и приложения) воспользуемся командой `docker logs`:
```
$ docker logs fastapi
[2023-01-23 16:33:29 +0000] [1] [INFO] Starting gunicorn 20.1.0
[2023-01-23 16:33:29 +0000] [1] [INFO] Listening at: http://0.0.0.0:8000 (1)
[2023-01-23 16:33:29 +0000] [1] [INFO] Using worker: uvicorn.workers.UvicornWorker
[2023-01-23 16:33:29 +0000] [7] [INFO] Booting worker with pid: 7
[2023-01-23 16:33:29 +0000] [8] [INFO] Booting worker with pid: 8
[2023-01-23 16:33:29 +0000] [9] [INFO] Booting worker with pid: 9
[2023-01-23 16:33:29 +0000] [10] [INFO] Booting worker with pid: 10
[2023-01-23 16:33:29 +0000] [7] [INFO] Started server process [7]
[2023-01-23 16:33:29 +0000] [7] [INFO] Waiting for application startup.
[2023-01-23 16:33:29 +0000] [7] [INFO] Application startup complete.
[2023-01-23 16:33:29 +0000] [8] [INFO] Started server process [8]
[2023-01-23 16:33:29 +0000] [8] [INFO] Waiting for application startup.
[2023-01-23 16:33:29 +0000] [8] [INFO] Application startup complete.
[2023-01-23 16:33:29 +0000] [9] [INFO] Started server process [9]
[2023-01-23 16:33:29 +0000] [9] [INFO] Waiting for application startup.
[2023-01-23 16:33:29 +0000] [9] [INFO] Application startup complete.
[2023-01-23 16:33:29 +0000] [10] [INFO] Started server process [10]
[2023-01-23 16:33:29 +0000] [10] [INFO] Waiting for application startup.
[2023-01-23 16:33:29 +0000] [10] [INFO] Application startup complete.
```

Можно добавить к команде ключ `-f`, чтобы просматривать логи непрерывно.

7. Остановим контейнер:
```bash
$ docker stop fastapi
```

## Теперь отправим наш образ в удаленное хранилище, например Docker Hub.
Для этого необходимо зарегистрироваться в [Docker Hub][5].

1.  После регистрации. Переходим на вкладку [Repositories][6] и нажимаем кнопку `Create repository`.

2. Заполняем поле `Name`, пишем fastapi-for-students. Visibility оставляем Public. Нажимаем кнопку `Create`.

3. В терминале выполняем вход в свой аккаунт. Выполняем команду и вводим свои логин и пароль от Docker Hub.
```bash
$ docker login docker.io
Username: ваш_логин
Password:
```
В случае успешной авторизации вы увидите сообщение `Login Succeeded`

4. Теперь необходимо чтобы тег локального образа соответствовал тегу репозитория. Присваиваем новый тег нашему образу.
```bash
$ docker tag fastapi-for-students:latest ваш_пользователь/fastapi-for-students:latest
```

5. Отправляем образ в репозиторий.
```bash
$ docker push ваш_пользователь/fastapi-for-students:latest
```

6. Обновляем страницу репозитория и проверяем сработала ли отправка. Вы должны увидить что-то типа [этого][7], но еще и с панелью управления.

## Индивидуальное задание.
1. Написать Dockerfile для своего проекта.
2. Создать образ по Dockerfile.
3. Запустить конейнер и проверить работоспособность проекта.
4. Опубликовать образ в [Docker Hub][5].

[1]: <https://learn.microsoft.com/en-us/windows/wsl/install> "Install Linux on Windows with WSL"
[2]: <https://docs.docker.com/desktop/install/windows-install/> "Install on Windows"
[3]: <https://github.com/RuslanUsmanov/fastapi-for-students> "fastapi-for-students"
[4]: <http://127.0.0.1:8000/docs> "Swagger UI"
[5]: <https://hub.docker.com/> "Docker Hub"
[6]: <https://hub.docker.com/repositories/> "Repositories"
[7]: <https://hub.docker.com/r/justaway86/fastapi-for-students> "justaway86/fastapi-for-students"
