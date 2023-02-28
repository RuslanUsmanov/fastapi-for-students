# Лабораторная работа № 11
## Развертывание приложения в k8s кластер в minikube

В данной работе мы развернем в кластере kubernetes наше приложение, состоящее из API-сервера на FastAPI и базы данных на PostgreSQL.
В качестве кластера будем использовать minikube.

### Самостоятельная работа

1. Подготовка исходного кода проекта.

В силу особенностей работы с секретами в kubernetes, необходимо изменить исходный код нашего сервера, а изменить способ формирования строки подключения к БД. Теперь она будет формироваться из четырех переменных окружения вместо одной: `DB_USER`, `DB_PASSWD`, `DB_NAME`, `DB_HOST`.

Редактируем файл `src/database.py`:
```python
from os import environ
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_USER = environ.get('DB_USER')
DB_PASSWD = environ.get('DB_PASSWD')
DB_NAME = environ.get('DB_NAME')
DB_HOST = environ.get('DB_HOST')

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWD}@{DB_HOST}:5432/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```
В файле миграций `migrations/env.py` также необходимо внести изменения. Здесь мы будем просто импортировать строку подключения к бд из `src/database.py`:
```python
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from src.models import Base
from src.database import SQLALCHEMY_DATABASE_URL

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option('sqlalchemy.url', SQLALCHEMY_DATABASE_URL)

target_metadata = Base.metadata
....
....
```

2. Обновление образа контейнера приложения в Docker Hub.

Теперь поскольку исходный код изменился, необходимо собрать новый образ и отправить его в хранилище.

Убираем из `Dockerfile` команды RUN и CMD, если они есть. Команды будут вызываться kubernetes при запуске контейнера.
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
```
Собираем образ (здесь вы указываете свого пользователя и образ):
```bash
$ docker build -t justaway86/fastapi-for-students .
```

Отправляем в хранилище (перед этим нужно авторизоваться, если вы не делали этого ранее):
```bash
$ docker push justaway86/fastapi-for-students
```

3. Запуск кластера в minikube.
Каждый узел в кластере minikube минимально требует свободных 2 ядра процссора, 2ГиБ оперативной памяти и 20ГиБ памяти на жестком диске.

Если у вас ресурсов достаточно, то запускаем кластер из трех узлов:
```bash
$ minikube start -n 3
```

Если ресурсов мало, то запускаем кластер из одного узла:
```bash
$ minikube start
```

4. Создание секрета.

В kubernetes `Секрет`(`Secret`) - это объект, который хранит секретную информацию, например логин и пароль для подключения к БД. Есть два способа создания секрета: либо с помощью команды "`kubectl create secret ...`", либо с помощью манифест-файла. Мы воспользуемся вторым способом.

В секрете мы будем хранить информацию для подключения к БД, а именно: `логин`, `пароль`, `название базы`.

Сначала кодируем наши строки по алгоритму [`base64`](1):
```bash
$ echo -n 'myuser' | base64
bXl1c2Vy

$ echo -n 'mypassword' | base64
bXlwYXNzd29yZA==

$ echo -n 'mydbname' | base64
bXlkYm5hbWU=
```

Создаем папку `k8s`. В ней будут храниться все манифесты.
```bash
$ mkdir k8s
```

Создаем манифест `k8s/secret.yaml`
```yaml
apiVersion: v1      # Версия API Kubernetes для этого манифеста
kind: Secret        # Тип объекта, который будет создан этим манифестом
metadata:
  name: dbsecret    # Название секрета
type: Opaque        # Тип сектера - приозвольный
data:               # Далее содержимое секрета: пары ключ: значение(в кодировке base64)
  db-user: bXl1c2Vy
  db-passwd: bXlwYXNzd29yZA==
  db-name: bXlkYm5hbWU=
```

Применяем манифест:
```bash
$ kubectl apply -f k8s/secret.yml
secret/dbsecret created
```

Проверяем секрет:
```bash
$ kubectl get secret dbsecret -o jsonpath='{.data}'
{"db-name":"bXlkYm5hbWU=","db-passwd":"bXlwYXNzd29yZA==","db-user":"bXl1c2Vy"}
```

6. Выделение памяти для СУБД PostgreSQL в кластере.

Поскольку при перезапуске контейнера вся информация, которая была создана в ходе его работы будет утеряна, необходимо выделить для БД специальный участок памяти, который не будет стираться при перезапуске подов. В kubernetes это выполняется с помощью создания двух объектов `Persistent Volume` и `Persistent Volume Claim`.

`Persistent Volume` - это некоторый объем памяти в кластере, связанный с каким-либо физическим хранилищем (HDD, SSD, ...). Он может быть создан вручную или динамически. `PV` можно считать аналогом узлов(нод) в кластере, с точки зрения памяти.

`Persistent Volume Claim` - это запрос на выделение `PV`. Если какому-то поду необходимо дополнительное хранилище данных, то создается соответствующий `PVC`. `PVC` можно считать аналогом подов в узле.

В нашем примере мы создадим в кластере `Persistent Volume` объемом 10ГиБ. Затем мы выделим для PostgreSQL эти 10ГиБ с помощью `Persistent Volume Claim`.

Создаем новый манифест `k8s/postgres`:
```yaml
apiVersion: v1                # Версия API Kubernetes для этого манифеста
kind: PersistentVolume        # Тип объекта, который будет создан этим манифестом
metadata:
  name: postgres-pv-volume    # Имя объекта
  labels:
    type: local
spec:
  storageClassName: manual    # Создаем хранилище вручную
  capacity:
    storage: 10Gi             # Выделяем 10ГиБ
  accessModes:
    - ReadWriteOnce           # Права доступа
  hostPath:
    path: "/mnt/data"
---                           # В одном манифесте можно описать несколько объектов
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pv-claim     # Имя объекта
spec:
  storageClassName: manual
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi           # Запрашиваем 10ГиБ
```

Применяем манифест-файл:
```bash
$ kubectl apply -f k8s/postgres-pv.yaml
persistentvolume/postgres-pv-volume created
persistentvolumeclaim/postgres-pv-claim created
```

7. Запуск СУБД PostgreSQL в кластере.

В качестве образа для пода используем официальный образ `postgres:latest`.

Создаем манифест-файл `k8s/postgres-deployment.yaml`:
```yaml
# Сначала создаем Service для пода с БД
apiVersion: v1
kind: Service           # Указываем. что создаем Service
metadata:
  name: postgres
spec:
  ports:
  - port: 5432          # Указываем раскрываемый порт
  selector:
    app: postgres       # Данный сервис будет применяться к поду с меткой app равной postgres
  clusterIP: None       # Не указываем IP чтобы service явно определялся в под с БД
---
# Теперь создаем Deployment
apiVersion: apps/v1
kind: Deployment        # Указываем. что создаем Deployment
metadata:
  name: postgres
spec:
  selector:
    matchLabels:
      app: postgres     # данный деплой будет применяться к поду с метрой  app равной postgres
  strategy:
    type: Recreate
  template:             # далее описываем содержимое пода
    metadata:
      labels:
        app: postgres   # указываем его метку
    spec:
      containers:                   # описываем контейнер(ы) в поде
      - image: postgres:latest      # используемый образ
        name: postgres              # имя контейнера
        env:                        # перечисляем переменные окружения
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:           # в данном случае переменные задаются значениями из секрета dbsecret
              name: dbsecret
              key: db-user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: dbsecret
              key: db-passwd
        - name: POSTGRES_DB
          valueFrom:
            secretKeyRef:
              name: dbsecret
              key: db-name
        ports:                      # указываем используемый контейнером порт
        - containerPort: 5432
          name: postgres
        volumeMounts:               # подключаем хранилище к контейнеру
        - name: postgres-persistent-storage
          mountPath: /var/lib/postgres
      volumes:                            # подключаем PVC к поду
      - name: postgres-persistent-storage # задаем имя, которе используется выше
        persistentVolumeClaim:
          claimName: postgres-pv-claim    # указываем используемый PVC
```

Примeняем манифест:
```bash
$ kubectl apply -f k8s/postgres-deployment.yaml
service/postgres created
deployment.apps/postgres created
```

Проверяем, что под был создан:
```bash
$ kubectl get pods
NAME                       READY   STATUS    RESTARTS   AGE
postgres-fc64b9d65-g8khw   1/1     Running   0          10s
```

8. Запускаем FastAPI приложение в кластере.

Создаем манифест `k8s/app-deplyment.yaml`:
```yaml
apiVersion: apps/v1       # Версия API Kubernetes для этого манифеста
kind: Deployment          # Тип объекта, который будет создан этим манифестом
metadata:
  name: fastapi-app
  labels:
    app: fastapi-app
spec:                     # Описываем характеристики deplyment'а
  replicas: 2             # Количество реплик подов
  selector:               # Указываем селектор для пода
    matchLabels:
      app: fastapi-for-students-pod
  template:               # Описываем параметры пода
    metadata:
      labels:
        app: fastapi-for-students-pod
    spec:
      containers:         # Описываем контейнер
      - name: fastapi-for-students
        image: justaway86/fastapi-for-students:latest
        ports:
        - containerPort: 8000
        env:              # Задаем переменные окружения
        - name: DB_USER   # Некоторые переменные берутся из Secret
          valueFrom:
            secretKeyRef:
              name: dbsecret
              key: db-user
        - name: DB_PASSWD
          valueFrom:
            secretKeyRef:
              name: dbsecret
              key: db-passwd
        - name: DB_NAME
          valueFrom:
            secretKeyRef:
              name: dbsecret
              key: db-name
        - name: DB_HOST  # Эта переменна "обычная", просто задаем значение
          value: "postgres"
        # Указываем команду, которую необходимо выполнить при запуске контейнера
        command: ['bash', '-c', "alembic upgrade head && gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app -b 0.0.0.0:8000"]
```

Примeняем манифест:
```bash
$ kubectl apply -f k8s/app-deployment.yaml
deployment.apps/fastapi-app created
```

Проверяем, что поды были созданы:
```bash
$ kubectl get pods
NAME                           READY   STATUS    RESTARTS   AGE
fastapi-app-596bdc5d68-7xzhn   1/1     Running   0          2m12s
fastapi-app-596bdc5d68-vd2ks   1/1     Running   0          2m12s
postgres-fc64b9d65-g8khw       1/1     Running   0          16m
```

9. Создание Serivce для приложения.

`Servce` - это объект, абстракция, которая позволяет получить доступ к подам извне. В данном примере мы создадим сервис типа `NodePort`. Такой тип сервиса открывает на каждом узле порт, обращаясь к которому мы будем получать доступ к нашему приложению.

Создаем новый манифест `k8s/app-service.yaml`
```yaml
apiVersion: v1
kind: Service                     # Создаем сервис
metadata:
  name: fastapi-app-svc           # Название сервиса
spec:
  type: NodePort                  # Указываем тип
  selector:
    app: fastapi-for-students-pod # Указываем селектор пода
  ports:                          # Указываем порты
    - port: 8000                  # Порт пода
      targetPort: 8000            # По умолчанию совподает со значением port
      # Опциональное поле. Значение должно находится в диапазоне 30000-32767
      nodePort: 30000             # Указываем раскрываемый этим сервисом номер порта
```

Примeняем манифест:
```bash
$ kubectl apply -f k8s/app-service.yaml
service/fastapi-app-svc created
```

Проверяем создался ли сервис:
```bash
$ kubectl get svc
NAME              TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
fastapi-app-svc   NodePort    10.111.205.171   <none>        8000:30000/TCP   57s
kubernetes        ClusterIP   10.96.0.1        <none>        443/TCP          171m
postgres          ClusterIP   None             <none>        5432/TCP         85m
```

10. Проверка работаспособности всего приложения

После того как сервис был создан мы можем обратиться к нашему приложению.
Для этого необходимо узнать внешний IP-адрес любого узла в кластере.

Выводим список узлов в кластере:
```bash
$ kubectl get nodes
NAME           STATUS   ROLES           AGE    VERSION
minikube       Ready    control-plane   176m   v1.26.1
minikube-m02   Ready    <none>          175m   v1.26.1
minikube-m03   Ready    <none>          175m   v1.26.1
```

Выводим информацию о любом узле и ищем пункт InternalIP
```bash
$ kubectl describe nodes minikube
Name:               minikube
Roles:              control-plane
Labels:             beta.kubernetes.io/arch=amd64
...
...
Addresses:
  InternalIP:  192.168.49.2
  Hostname:    minikube
...
...
```

Открываем в браузере адрес http://192.168.49.2:30000/docs и проверяем работу API.

Альтернативный способ получить доступ к приложению - воспользоваться minikube:
```bash
$ minikube service fastapi-app-svc
|-----------|-----------------|-------------|---------------------------|
| NAMESPACE |      NAME       | TARGET PORT |            URL            |
|-----------|-----------------|-------------|---------------------------|
| default   | fastapi-app-svc |        8000 | http://192.168.49.2:30000 |
|-----------|-----------------|-------------|---------------------------|
```
Откроется браузер.


### Индивидуальное задание.

1. Повторить все для своего варианта.
2. Все манифест-файлы добавить в репозиторий на Github.

[1]: <https://ru.wikipedia.org/wiki/Base64> "Base64 - Wikipedia"
