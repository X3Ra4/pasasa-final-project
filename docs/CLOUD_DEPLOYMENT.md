# Розгортання на AWS EC2

Потрібен **новий окремий EC2 з Ubuntu Server 24.04 LTS, x86_64**. Скрипти не призначені для сервера з іншими застосунками. Фактичний EC2 ще не розгорнуто.

## 1. AWS та мережа

У власному AWS-акаунті виберіть регіон, зазначену Ubuntu, щонайменше 2 GiB пам’яті й достатній EBS-диск для медіа (наприклад, 20 GiB). Увімкніть публічну IPv4, створіть SSH key pair. Приватний `.pem` зберігайте локально.

Security Group: SSH `22` лише з вашої IP `/32`; HTTP `80` та HTTPS `443` для відвідувачів. **Порти 5432 і 8001 не відкривати:** PostgreSQL і Gunicorn слухають localhost.

Перевірте вартість EC2, EBS і публічної IPv4 у своєму акаунті; безкоштовний тариф не припускається. Для постійного DNS потрібна стабільна адреса: після stop/start звичайна публічна IP може змінитися. AWS API keys у застосунку не використовуються.

## 2. Первинна установка

```bash
ssh -i /path/to/pasasa.pem ubuntu@YOUR_EC2_PUBLIC_DNS
sudo apt-get update
sudo apt-get install -y git
git clone --branch cloud-solutions-aws --single-branch https://github.com/X3Ra4/pasasa-final-project.git pasasa-bootstrap
cd pasasa-bootstrap
sudo bash deploy/ec2/bootstrap.sh YOUR_EC2_PUBLIC_DNS
```

Передайте реальну адресу без схеми, шляху чи порту. Bootstrap встановлює залежності, клонує гілку в `/opt/pasasa`, створює системного користувача `pasasa`, БД і роль PostgreSQL без прав суперкористувача. Випадкові секрети записуються в `/etc/pasasa/.env` без друку на екран. Далі виконуються міграції, демодані, `collectstatic`, налаштування Nginx і `systemctl enable --now pasasa`.

Скрипт не перезаписує наявний `/opt/pasasa`, `.env` чи БД `pasasa`. Якщо установка перервалася, діагностуйте конкретний крок. Не використовуйте bootstrap для оновлення й не видаляйте БД навмання.

## 3. Перевірка

```bash
sudo systemctl is-enabled pasasa
sudo systemctl is-active pasasa
sudo systemctl status pasasa postgresql nginx --no-pager
curl -f http://YOUR_EC2_PUBLIC_DNS/healthz/
sudo bash /opt/pasasa/deploy/ec2/manage.sh showmigrations
sudo -u postgres psql -d pasasa -c 'SELECT count(*) FROM maps_map;'
```

Очікується `enabled`, `active`, JSON зі `status: ok`, застосовані міграції й 9 демокарт. Відкрийте `/catalog/maps/`.

Початковий HTTP-режим потрібний для перевірки зв’язності й демонстраційних даних. Перед використанням реальних паролів завершіть HTTPS-крок.

## 4. HTTPS

Потрібен власний домен з A-записом на EC2. Додайте домен у `server_name` файлу `/etc/nginx/sites-available/pasasa`, виконайте `sudo nginx -t` і `sudo systemctl reload nginx`.

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d pasasa.example.com
```

Замініть домен своїм. Через `sudoedit /etc/pasasa/.env` встановіть:

```ini
DJANGO_ALLOWED_HOSTS=pasasa.example.com,127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=https://pasasa.example.com
DJANGO_HTTPS=1
```

```bash
sudo systemctl restart pasasa
curl -f https://pasasa.example.com/healthz/
sudo certbot renew --dry-run
```

HTTPS-профіль вмикає redirect, secure cookies і HSTS поточного хоста. HSTS для всіх піддоменів і preload навмисно вимкнені: контроль над HTTPS кожного піддомену не припускається. `check --deploy` може показувати W005/W021. У початковому HTTP-режимі додаткові HTTPS-попередження очікувані.

## 5. Адміністратор і команди Django

```bash
sudo bash /opt/pasasa/deploy/ec2/manage.sh createsuperuser
```

Команда запитає ім’я та пароль. `manage.sh` запускає тимчасову systemd-службу з тим самим `EnvironmentFile`: команди працюють із правильною PostgreSQL. Звичайна реєстрація доступна на `/accounts/signup/`.

## 6. Оновлення

Зробіть резервну копію, потім виконайте:

```bash
sudo bash /opt/pasasa/deploy/ec2/update.sh
```

Скрипт перевіряє гілку й чистоту checkout, зупиняє службу, виконує `git pull --ff-only`, встановлює залежності, застосовує міграції, збирає static та запускає застосунок. Так запити не потрапляють у змішану стару/нову версію коду. БД, `.env` та медіа поза checkout зберігаються. Nginx/TLS-конфіг не перезаписується; зміни його шаблону застосовуйте окремо.

Можлива коротка перерва доступності. При помилці міграції скрипт намагається знову запустити службу; автоматичного відкату схеми немає. Для відновлення потрібні резервна копія та сумісна версія коду.

## 7. Резервна копія

```bash
sudo systemctl stop pasasa
sudo install -d -m 0700 /var/backups/pasasa
sudo bash -c 'umask 077; runuser -u postgres -- pg_dump -Fc pasasa > /var/backups/pasasa/database.dump'
sudo tar -czf /var/backups/pasasa/media.tar.gz -C /var/lib/pasasa media
sudo chmod 0600 /var/backups/pasasa/media.tar.gz
sudo systemctl start pasasa
```

Команди перезаписують копії з тими самими назвами; для історії додайте дату. Зберігайте копії поза інстансом захищеним способом. EBS не замінює окреме резервне копіювання. Відновлення спочатку перевірте на тестовій БД.

## 8. Діагностика і здача

```bash
sudo journalctl -u pasasa -n 100 --no-pager
sudo nginx -t
sudo ss -lntp
sudo systemctl cat pasasa
sudo stat -c '%a %U:%G %n' /etc/pasasa/.env
```

Показуйте шлях `EnvironmentFile`, але не `cat /etc/pasasa/.env`, паролі чи ключі. Для перевірки автозапуску збережіть роботу, виконайте `sudo reboot`, повторно підключіться та перевірте службу й URL. Docker-тест не доводить автозапуск systemd на EC2.

Після захисту приберіть непотрібні AWS-ресурси у своєму акаунті. Докази для здачі перелічено в [CLOUD_DEFENSE.md](CLOUD_DEFENSE.md).

## Офіційні джерела

- [AWS: підключення до EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-connect-methods.html).
- [Django: deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/).
- [Gunicorn: deployment](https://gunicorn.org/deploy/).
- [systemd: EnvironmentFile](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html).
