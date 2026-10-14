from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Case, When, IntegerField, F
from django.utils import timezone
from django.http import Http404
from django.shortcuts import get_object_or_404
from .models import Project, Task


def visible_projects(user):
    return Project.objects.filter(Q(owner=user) | Q(members=user)).distinct()


def project_users(project):
    return get_user_model().objects.filter(
        Q(pk=project.owner_id) | Q(team_projects=project), is_active=True).distinct()


def numeric_id(value):
    value = str(value)
    if value.isascii() and value.isdecimal() and len(value) <= 19:
        parsed = int(value)
        if 0 < parsed <= 9223372036854775807:
            return parsed
    return None


def lock_visible_project(user, pk):
    """Caller must be atomic. One shared row lock orders all project mutations."""
    project = get_object_or_404(Project.objects.select_for_update(), pk=pk)
    if not visible_projects(user).filter(pk=pk).exists():
        raise Http404
    return project


def filtered_tasks(queryset, params):
    queryset = queryset.select_related('assignee', 'project')
    queryset = queryset.filter(archived=params.get('archived') == '1')
    if params.get('q'):
        queryset = queryset.filter(Q(title__icontains=params['q']) | Q(description__icontains=params['q']))
    for field, choices in [('status', Task.Status.values), ('priority', Task.Priority.values)]:
        if params.get(field) in choices:
            queryset = queryset.filter(**{field: params[field]})
    assignee = params.get('assignee', '')
    if assignee == 'none':
        queryset = queryset.filter(assignee__isnull=True)
    elif numeric_id(assignee):
        queryset = queryset.filter(assignee_id=numeric_id(assignee))
    sort = params.get('sort')
    if sort == 'due':
        return queryset.order_by(F('due_date').asc(nulls_last=True), 'pk')
    if sort == 'priority':
        return queryset.annotate(rank=Case(When(priority='high', then=0), When(priority='normal', then=1),
            default=2, output_field=IntegerField())).order_by('rank', '-created_at', '-pk')
    return queryset.order_by('-created_at', '-pk')


def task_stats(queryset):
    return queryset.filter(archived=False).aggregate(
        total=Count('id'), done=Count('id', filter=Q(status='done')),
        active=Count('id', filter=~Q(status='done')),
        overdue=Count('id', filter=Q(due_date__lt=timezone.localdate()) & ~Q(status='done')),
    )
