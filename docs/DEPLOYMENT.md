# Розгортання TaskFlow

## Локальне контейнерне розгортання

Потрібні Docker Engine/Desktop з Compose, Git і Python 3. Порти бази та Gunicorn не публікуються.
Nginx доступний лише на localhost:8088; інші проєкти Docker не зачіпаються.

```sh
git clone --branch taskflow-team-project --single-branch https://github.com/X3Ra4/pasasa-final-project.git taskflow
cd taskflow
python tools/init_env.py
docker compose up --build -d
docker compose ps
```

Відкрити http://127.0.0.1:8088/healthz/ — очікується `{"status":"ok"}`.
Далі відкрити головну сторінку та зареєструвати користувача. За потреби:

```sh
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_demo --owner your_username
```

Compose спочатку очікує готовність PostgreSQL. Web застосовує міграції, збирає статику,
запускає Gunicorn під непривілейованим користувачем. Nginx запускається після перевірки web.
WhiteNoise обслуговує зібрані локальні статичні файли через Gunicorn/Nginx.
Рестарт контейнерів налаштований `unless-stopped`.

`.env` генерується один раз, ніколи не перезаписується автоматично. Щоб змінити порт,
відредагуйте `TASKFLOW_PORT`. Секрети, БД і локальні логи ігноруються Git та Docker build context.
Демо-команда не створює облікових записів і не встановлює паролів.

## Публічний сервер Ubuntu

Локальне контейнерне розгортання вже є реалізацією додаткової вимоги PDF про контейнер.
Публічний сервер та домен для цього проєкту не надано, тому зовнішній URL не заявляється.
Для фактичного публічного розгортання потрібні власний сервер, домен, сертифікат і встановлений Docker.

1. Клонувати цю гілку на сервер і виконати `python3 tools/init_env.py`.
2. У `.env` задати `DJANGO_ALLOWED_HOSTS=taskflow.example.com`, `DJANGO_HTTPS=1`,
   `CSRF_TRUSTED_ORIGINS=https://taskflow.example.com`. Замінити example-домен реальним.
3. Залишити PostgreSQL та web без публічних портів. Дозволити з інтернету 80/443;
   SSH обмежити своєю адресою. Не відкривати 5432/8000.
4. Налаштувати TLS у Nginx контейнера: взяти [nginx.tls.conf.example](../deploy/nginx.tls.conf.example),
   замінити домен, змонтувати реальний `fullchain.pem` і `privkey.pem` read-only, опублікувати 80:80 і 443:443.
   Сертифікат потрібно отримати у свого центру сертифікації (наприклад, ACME) та налаштувати оновлення.
5. Прибрати локальне port mapping у `compose.yml` при заміні на публічні порти та змонтувати TLS-конфіг
   замість стандартного `nginx.conf`. Не передавати невідфільтрований `X-Forwarded-Proto` від клієнта:
   Nginx задає його зі своєї схеми `$scheme`.
6. Запустити `docker compose up --build -d`; перевірити HTTPS, вхід, створення завдання,
   `docker compose exec web python manage.py check --deploy --fail-level WARNING`.
7. Увімкнути запуск Docker після reboot (`sudo systemctl enable docker`) та перевірити сайт після перезапуску сервера.

Прямий HTTPS тут завершується в Nginx контейнера. Якщо TLS завершується на зовнішньому reverse proxy,
потрібна окрема конфігурація довіреного proxy; стандартний HTTP-конфіг навмисно не довіряє переданому клієнтом заголовку.
HSTS з includeSubDomains/preload вмикається в HTTPS-режимі — використовуйте окремий домен,
для якого HTTPS гарантовано на всіх піддоменах. У production секрети не повинні залишатися прикладами.

## Оновлення

Зробіть резервну копію перед змінами схеми. Потім у каталозі застосунку:

```sh
git pull --ff-only origin taskflow-team-project
docker compose up --build -d
docker compose ps
docker compose logs --tail=60 web
```

Це просте односерверне розгортання з короткою перервою під час оновлення, без обіцянки zero downtime.
Старий образ не відновлює схему БД автоматично; для відкату міграції потрібні перевірена резервна копія
та сумісна версія коду. Не видаляйте томи під час звичайного оновлення.

## Резервна копія

Створіть каталог `backups` на хості. Ці команди зберігають binary dump без небезпечного перенаправлення
двійкового потоку в Windows PowerShell:

```sh
docker compose exec db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/taskflow.dump'
docker compose cp db:/tmp/taskflow.dump backups/taskflow.dump
```

Збережіть dump і `.env` у приватному місці поза Git. Для реального сервера налаштуйте регулярне
копіювання та перевіряйте відновлення в окремому тестовому середовищі.
Відновлення замінює дані; перед ним зупиняють web/nginx, копіюють dump у контейнер БД
та використовують `pg_restore --clean --if-exists --no-owner` із правильними ім’ям БД та користувачем.
Не відновлюйте поверх чинної бази без окремої копії.

## Діагностика

```sh
docker compose ps
docker compose logs --tail=100 web nginx db
docker compose exec web python manage.py check
docker compose exec web python manage.py showmigrations
docker compose exec web python -m pip check
```

`DisallowedHost`: перевірити `DJANGO_ALLOWED_HOSTS`. CSRF при HTTPS: домен у
`CSRF_TRUSTED_ORIGINS`, правильна схема proxy, cookies. DB authentication failed:
початковий пароль PostgreSQL зберігається в томі; редагування `.env` не змінює пароль існуючої ролі.
Відновіть правильний секрет або змініть пароль ролі через адміністратора БД; не видаляйте том як «виправлення».

Перевірки production базуються на [Django deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/).
