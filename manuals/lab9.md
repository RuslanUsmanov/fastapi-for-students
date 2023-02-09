# Лабораторная работа № 9
## Автоматическое развертывание на сервер с помощью Github Actions

В данной работе мы научимся создавать пайплайны(pipeline) для автоматического тестирования и развертывания ПО на сервере.

### Самостоятельная работа



1. Создаем платежный аккаунт в Yandex Cloud согласно этой инструкции: [ссылка][1]. После создания вам предоставляется пробный период на 60 дней с балансом в 1000р на создание виртуальных машин. Данного пробного периода нам хватит на текущий семестр.

2. На своем ПК необходимо сгенерировать пару ssh-ключей. Выполняем команду:
```
$ ssh-keygen -t rsa -b 4096

Generating public/private rsa key pair.
Enter file in which to save the key (~/.ssh/id_rsa):
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in /home/justaway/.ssh/id_rsa
Your public key has been saved in ~/.ssh/id_rsa.pub
The key fingerprint is:
SHA256:asdadsdsadadadsuOKI1asdadTacl8T0EeXwiuh/fBr0g
The key's randomart image is:
+---[RSA 4096]----+
|       o+ o .. . |
|      .. = oo . .|
|      .. .++.o . |
|       ooo.o+..  |
|       oS++oo.o  |
|        B+ooo. o |
|       =..ooE.. .|
|      + .o o+... |
|       o. .+=+o  |
+----[SHA256]-----+

```
Если под ОС Windows, то данную команду следует выполнять в PowerShell.
В результате выполнения команды в папке `~/.ssh` будет сгенерирована пара ключей:
- `id_rsa` - приватный ключ
- `id_rsa.pub` - публичный ключ

3. Просматриваем и копируем содержимое публичного ключа;
```
$ cat ~/.ssh/id_rsa.pub
ssh-rsa AAAAAAFGNKSAGNxfs ...... ASDASDADS== user@hostname
```

4. Открываем [консоль Yandex Could][2]. Открываем меню справа и выбираем Compute Cloud. Далее нажимаем кнопку `Cоздать ВМ`.
<img src="https://i.imgur.com/i31stIT.png">

5. Настраиваем параметры виртуальной машины в соответсвии со скриншотами ниже:
 - придумываем свое название машины;
 - а также свое имя пользователя (запомните его);
 - в поле `SSH-ключ` вставляем скопированный публичный ключ;
 - нажимаем `Создать ВМ`.
<img src="https://imgur.com/kyenTvJ.png">
<img src="https://imgur.com/EbKwiC8.png">

6. В результате будет создана и запущена виртуальная машина:
<img src="https://imgur.com/kKwl398.png">

7. Теперь необходимо сделать публичный IP машины статическим. Для этого открываем меню справа и выбираем `Virtual Private Cloud`.
<img src="https://imgur.com/VNplYNa.png">

8. Нажимаем на кнопку `IP-адреса` справа.
<img src="https://imgur.com/46C0oWT.png">

9. Теперь нажимаем на "три точки" и выбираем `Сделать статическим`.
<img src="https://imgur.com/qjGFYyu.png">

10. Подключаемся к виртуальной машине. Выполняем:
```
$ ssh ваш_пользователь@ip_адрес_вм
```
Появится сообщение:
```
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```
Вводим `yes` и нажимаем клавишу `enter`.

11. Устанавливаем на сервере docker и docker-compose:
```bash
$ sudo apt update
$ sudo apt install -y docker.io docker-compose
```

12. Для того чтобы мы могли через Github Actions авторизовываться на сервере, нам нужна еще одна пара ssh-ключей. Генерируем пару ssh-ключей на виртуальной машине.
```bash
$ ssh-keygen -t rsa -b 4096 -C "for github"
```

13. Добавляем публичный ключ в авторизованные на сервере.
```bash
$ cat .ssh/id_rsa.pub >> .ssh/authorized_keys
```

14. Копируем приватный ключ.
```bash
$ cat .ssh/id_rsa
```

15. Добавляем ключ в секреты репозитория. Открываем свой репозиторий на Github. Переходим в настройки (`Settings`). Выбираем пункт `Secrets and variables` > `Actions`. Нажимаем кнопку `New repository secret`
<img src="https://imgur.com/hTJRWs8.png">

16. В поле `Name` пишем `SSH_KEY`. В поле `Secret` вставляем приватный ключ. Нажимаем кнопку `Add secret`.
<img src="https://imgur.com/QQEJUq4.png">

17. Добавляем еще несколько секретов:
 - HOST - публичный IP-адрес сервера
 - LOGIN - имя пользователя на сервере
 - DB_NAME - имя БД для PostgreSQL
 - DB_USER - имя пользователя БД
 - DB_PASSWD - пароль для БД
<img src="https://imgur.com/nYrPmER.png">


18. Переходим на вкладку `Actions` и нажимаем на кнопку `New workflow`.
<img src="https://imgur.com/fX7VQ2V.png">

19. Далее нажимаем на ссылку `set up a workflow yourself `
<img src="https://imgur.com/6bGJ3tg.png">

20. Пишем пайплайн из двух задач. Первая задача проводит тестирование кода. Вторая задача выполняет развертывание приложения на сервере
<img src="https://imgur.com/dyC1e7g.png">
```yml
# Имя для данного workflow
name: Test code and deploy
# Триггер по которому будет срабатывать workflow, в данном случае при отправке кода в ветку master
on:
  push:
     branches: [master]
# Перечисление списка задач в данном workflow
jobs:
  # Задача тестирования
  test:
    # Название задачи
    name: Test code
    # Тип ВМ, на которой будет запущена задача
    runs-on: ubuntu-latest
    # Шаги выполняемые в рамках задачи
    steps:
        # Получаем код репозитория
      - name: Get code from repo
        uses: actions/checkout@v3
        # Устанавливаем python3.10
      - name: Set-up python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
        # Устанавливаем зависемости
      - name: Install dependencies
        run: pip install -r requirements.txt
        # Запускаем тесты
      - name: Run tests
        run: pytest
        # Для успешного запуска тестов необходимо в переменную окружения DATABASE_URL записать корректную строку подключения к любой БД
        env:
          DATABASE_URL: sqlite:///./sqlite.db
  # Задача развертывания
  deploy:
    name: Deploy to server
    runs-on: ubuntu-latest
    needs: [test]
    steps:
      - name: Get code from repo
        uses: actions/checkout@v3
        # Настройка подключения по SSH
      - name: Configure SSH
        run: |
          mkdir -p ~/.ssh/
          echo "${{ secrets.SSH_KEY }}" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          cat >>~/.ssh/config <<END
          Host yandex_server
            HostName ${{ secrets.HOST }}
            User ${{ secrets.LOGIN }}
            Port ${{ secrets.PORT }}
            IdentityFile ~/.ssh/id_rsa
            StrictHostKeyChecking no
          END
        # Создаем файл .env, который необходим для docker-compose
      - name: Create .env file
        run: |
          cat >>.env <<END
          DB_USER=${{ secrets.DB_USER }}
          DB_PASSWD=${{ secrets.DB_PASSWD }}
          DB_NAME=${{ secrets.DB_NAME }}
          END
        # Отправляем файлы проекта на сервер
      - name: Rsync files to server
        run: rsync -rav * yandex_server:~/project
        # Отправляем файл .env на сервер
      - name: Rsync files to server
        run: rsync -rav .env yandex_server:~/project/.env
        # Останавливаем контейнеры на сервере
      - name: Stop containers
        run: ssh yandex_server 'sudo docker-compose -f project/docker-compose.yml down'
        # Собираем контейнеры
      - name: Build containers
        run: ssh yandex_server 'sudo docker-compose -f project/docker-compose.yml build'
        # Запускаем контейнеры
      - name: Run containers
        run: ssh yandex_server 'sudo docker-compose -f project/docker-compose.yml up -d'
```

21. Сохраняем файл и переходим на вкладку `Actions`. Наблюдаем за тем как выполняется наш `workflow`. Ждем успешного завершения.
<img src="https://imgur.com/3bg5MLD.png">

22. Открываем браузер. В адресной строке пишем публичный адрес нашего сервера http://ваш_ip/docs. Открываем страницу и проверяем работоспособность API.

### Индивидуальное задание.

1. Создать ВМ в Yandex Cloud.
2. Создать работоспособный workflow в Github Actions.
3. Продемонстрировать преподователю работу.
4. В качестве отчета прикрепить ссылку на Github.

[1]: <https://cloud.yandex.ru/docs/billing/quickstart/> "Регистрация аккаунта в Yandex Cloud"
[2]: <https://console.cloud.yandex.ru/> "Yandex Cloud"
