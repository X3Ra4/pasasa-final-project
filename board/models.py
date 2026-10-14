from django.conf import settings
from django.db import models


class Project(models.Model):
    name = models.CharField('Назва', max_length=120)
    description = models.TextField('Опис', blank=True, max_length=5000)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_projects')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Membership', related_name='team_projects')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']

    def __str__(self):
        return self.name


class Membership(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['project', 'user'], name='unique_project_member')]


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = 'todo', 'Заплановано'
        DOING = 'doing', 'У роботі'
        DONE = 'done', 'Виконано'

    class Priority(models.TextChoices):
        LOW = 'low', 'Низький'
        NORMAL = 'normal', 'Звичайний'
        HIGH = 'high', 'Високий'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField('Назва', max_length=180)
    description = models.TextField('Опис', blank=True, max_length=10000)
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='assigned_tasks', verbose_name='Виконавець')
    status = models.CharField('Статус', max_length=10, choices=Status.choices, default=Status.TODO)
    priority = models.CharField('Пріоритет', max_length=10, choices=Priority.choices, default=Priority.NORMAL)
    due_date = models.DateField('Термін виконання', null=True, blank=True)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        indexes = [models.Index(fields=['project', 'archived', 'status'])]
        constraints = [
            models.CheckConstraint(condition=models.Q(status__in=['todo', 'doing', 'done']), name='valid_task_status'),
            models.CheckConstraint(condition=models.Q(priority__in=['low', 'normal', 'high']), name='valid_task_priority'),
        ]

    def __str__(self):
        return self.title


class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    body = models.TextField('Коментар', max_length=3000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'pk']
