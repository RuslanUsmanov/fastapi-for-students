# Лабораторная работа № 11
## Обновление и откат образа в deployment k8s.

В данной работе мы выполним обновление образа разными способами и посмотрим как выполнить откат на предыдущую версию.

### Самостоятельная работа

1. Подготовка исходного кода проекта.

Для начала необходимо подготовить три версии приложения. В файл `src.main` добавляем роут, который будет возвращать текущую версию приложения.

```python
...
...
@app.get("/version")
def get_app_version():
    return {'version': 1.0}
```

2. Теперь соберем образ, при этом укажем его версию в тэге:
```bash
$ docker build -t justaway86/fastapi-for-students:1.0 .
```

3. Отправляем образ в докер-хаб:
```bash
$ docker push justaway86/fastapi-for-students:1.0
```

4. Меняем в коде `src.main` версию на 2.0 и повторяем пункты 1-3:
```bash
$ docker build -t justaway86/fastapi-for-students:2.0 .
$ docker push justaway86/fastapi-for-students:2.0
```

Итак теперь у нас есть две версии образа приложения.

5. Редактируем манифест `app-deployment.yaml`. Меняем версию образа для подов:
```yaml
...
...
containers:
  - name: fastapi-for-students
    image: justaway86/fastapi-for-students:1.0
    ports:
      - containerPort: 8000
...
...
```

6. Применяем все манифесты из прошлой лабораторной работы. Для этого просто в качестве аргумента укажем папку с манифестами:
```bash
$ kubectl apply -f k8s/
deployment.apps/fastapi-app created
service/fastapi-app-svc created
service/postgres created
deployment.apps/postgres created
persistentvolume/postgres-pv-volume created
persistentvolumeclaim/postgres-pv-claim created
secret/dbsecret created
```

7. Ждем пока под(ы) успешно запустятся:
```bash
$ kubectl get pods
NAME                          READY   STATUS    RESTARTS      AGE
fastapi-app-d4575b45b-djnps   1/1     Running   3 (43s ago)   97s
fastapi-app-d4575b45b-gpsvg   1/1     Running   3 (47s ago)   97s
postgres-fc64b9d65-8bbhc      1/1     Running   0             97s
```

8. Выполняем запрос к новому роуту для проверки текущей версии:
```bash
$ curl 192.168.49.2:30000/version
{"version":1.0}⏎
```

9. Укажем аннотацию к текущей версии `deployment`. Это пригодится нам в дальнейшем при просмотре истории.
```bash
$ kubectl annotate deployment/fastapi-app kubernetes.io/change-cause="init version 1.0"
deployment.apps/fastapi-app annotated
```

10. Обновляем версию образа c помощью команды `set image`:
```bash
$ kubectl set image deployments/fastapi-app fastapi-for-students=justaway86/fastapi-for-students:2.0
deployment.apps/fastapi-app image updated
```

11. Проверяем применилось ли обновление. Снова выполняем запрос к поду:
```bash
$ curl 192.168.49.2:30000/version
{"version":2.0}⏎ 
```
Итак версия успешно изменилась.

12. Также статус обновления образа можно проверить с помощью команды `rollout status`:
```bash
$ kubectl rollout status deployments/fastapi-app
deployment "fastapi-app" successfully rolled out
```

13. Указываем аннотацию к текущей версии `deployment`:
```bash
$ kubectl annotate deployment/fastapi-app kubernetes.io/change-cause="update image to 2.0"
deployment.apps/fastapi-app annotated
```

14. Теперь можно посмотреть историю версий(ревизий) нашего `deployment`:
```bash
$ kubectl rollout history deployments/fastapi-app
deployment.apps/fastapi-app 
REVISION  CHANGE-CAUSE
1         init version 1.0
2         update image to 2.0
```

15. Для того чтобы посмотреть в деталях информацию о ревизии выполним:
```bash
$ kubectl rollout history deployments/fastapi-app --revision=2
```

16. Теперь отменим обновление образа, т.е. вернемся к версии 1.0. Выполним `rollout undo`:
```bash
$ kubectl rollout undo deployments/fastapi-app
deployment.apps/fastapi-app rolled back
```

17. Проверяем статус отката:
```bash
$ kubectl rollout status deployments/fastapi-app
deployment "fastapi-app" successfully rolled out
```

18. Проверяем версию:
```bash
$ curl 192.168.49.2:30000/version
{"version":1.0}⏎
```
Мы вернулись к версии 1.0

19. История ревизий:
```bash
$ kubectl rollout history deployments/fastapi-app 
deployment.apps/fastapi-app 
REVISION  CHANGE-CAUSE
2         update image to 2.0
3         init version 1.0
```
Видно, что текущая ревизия (№3) соответствует изначальной версии 1.0


### Индивидуальное задание.

1. Повторить все для своего варианта.
2. В качестве отчета прикрепить скриншоты с историей ревизий и детальной информацией о каждой ревизии.
