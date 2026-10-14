from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from board.models import Project, Task, Comment


class Command(BaseCommand):
    help = 'Create sample projects for an existing user, without creating accounts or changing passwords.'

    def add_arguments(self, parser):
        parser.add_argument('--owner', required=True, help='Existing active username')

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            owner = get_user_model().objects.get(username=options['owner'], is_active=True)
        except get_user_model().DoesNotExist:
            raise CommandError('Create an active account first, then pass its username with --owner.')
        project, _ = Project.objects.get_or_create(owner=owner, name='Запуск нового продукту', defaults={
            'description': 'Від першого ескізу до релізу. Наш спільний план створення чогось особливого.'})
        for name, description in [
            ('Дизайн-система', 'Єдиний візуальний стиль, зрозумілі компоненти та увага до деталей.'),
            ('Навчальний простір', 'Нові знання, корисні матеріали та маленькі щоденні перемоги.'),
        ]:
            Project.objects.get_or_create(owner=owner, name=name, defaults={'description': description})
        entries = [
            ('Підготувати макет головної сторінки', 'todo', 'high', 2, 'Продумати структуру сторінки та основний сценарій користувача.'),
            ('Зібрати відгуки команди', 'todo', 'normal', 4, 'Обговорити перші враження й зібрати пропозиції до наступної ітерації.'),
            ('Написати тексти для онбордингу', 'todo', 'low', 6, 'Коротко пояснити новому користувачу, з чого почати.'),
            ('Розробити REST API завдань', 'doing', 'high', 1, 'Реалізувати створення, редагування та перевірку прав доступу.'),
            ('Перевірити адаптивну верстку', 'doing', 'normal', -1, 'Пройти ключові сторінки на телефоні, планшеті та великому екрані.'),
            ('Оформити документацію', 'doing', 'normal', 3, 'Додати інструкції користувача та кроки розгортання.'),
            ('Узгодити концепцію продукту', 'done', 'normal', -3, 'Визначити цільову аудиторію, проблему та очікуваний результат.'),
            ('Налаштувати репозиторій', 'done', 'low', -2, 'Створити структуру проєкту, шаблони задач і перевірки CI.'),
        ]
        for title, status, priority, days, description in entries:
            task, created = Task.objects.get_or_create(project=project, title=title, defaults={
                'description': description, 'status': status, 'priority': priority,
                'due_date': timezone.localdate() + timedelta(days=days), 'assignee': owner})
            if created and status == 'doing':
                Comment.objects.create(task=task, author=owner, body='Першу версію підготовлено. Наступний крок — перевірка результату.')
        self.stdout.write(self.style.SUCCESS('Demo ready. Existing records and passwords were not changed.'))
