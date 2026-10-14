from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction, connection, DatabaseError
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_GET
from .forms import ProjectForm, TaskForm, MemberForm, CommentForm, StatusForm
from .models import Project, Task, Membership
from .policies import visible_projects, filtered_tasks, task_stats, project_users, lock_visible_project


def accessible_project(user, pk, owner=False, lock=False):
    project = lock_visible_project(user, pk) if lock else get_object_or_404(visible_projects(user), pk=pk)
    if owner and project.owner_id != user.pk:
        raise PermissionDenied
    return project


def accessible_task(user, pk, owner=False, lock=False):
    task = get_object_or_404(Task.objects.select_related('project', 'assignee'),
                            pk=pk, project__in=visible_projects(user))
    if lock:
        project = accessible_project(user, task.project_id, lock=True)
        task = get_object_or_404(Task.objects.select_related('assignee'), pk=pk, project=project)
        task.project = project
    if owner and task.project.owner_id != user.pk:
        raise PermissionDenied
    return task


def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Обліковий запис створено. Почніть із нового проєкту!')
        return redirect('dashboard')
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def dashboard(request):
    projects = visible_projects(request.user).select_related('owner')
    tasks = Task.objects.filter(project__in=projects)
    return render(request, 'board/dashboard.html', {
        'projects': projects, 'stats': task_stats(tasks),
        'my_tasks': tasks.filter(assignee=request.user, archived=False).exclude(status='done').select_related('project')[:8],
    })


@login_required
@transaction.atomic
def project_form(request, pk=None):
    project = accessible_project(request.user, pk, owner=True, lock=True) if pk else None
    form = ProjectForm(request.POST or None, instance=project)
    if request.method == 'POST' and form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        messages.success(request, 'Проєкт збережено.')
        return redirect('project', pk=project.pk)
    return render(request, 'board/form.html', {'form': form,
        'title': 'Редагувати проєкт' if pk else 'Новий проєкт', 'project': project})


@login_required
def project_detail(request, pk):
    project = accessible_project(request.user, pk)
    tasks = filtered_tasks(project.tasks.all(), request.GET)
    page = Paginator(tasks, 60).get_page(request.GET.get('page'))
    columns = [{'key': key, 'label': label, 'tasks': [t for t in page.object_list if t.status == key]}
               for key, label in Task.Status.choices]
    query = request.GET.copy()
    query.pop('page', None)
    return render(request, 'board/project.html', {'project': project, 'page': page, 'columns': columns,
        'stats': task_stats(project.tasks.all()), 'members': project_users(project),
        'statuses': Task.Status.choices, 'priorities': Task.Priority.choices,
        'query': query.urlencode(), 'archived': request.GET.get('archived') == '1'})


@login_required
@transaction.atomic
def project_delete(request, pk):
    project = accessible_project(request.user, pk, owner=True, lock=True)
    if request.method == 'POST':
        project.delete()
        messages.success(request, 'Проєкт видалено.')
        return redirect('dashboard')
    return render(request, 'board/confirm.html', {'title': 'Видалити проєкт', 'object': project,
        'warning': 'Усі завдання та коментарі цього проєкту також буде видалено.', 'project': project})


@login_required
@transaction.atomic
def members(request, pk):
    project = accessible_project(request.user, pk, owner=True, lock=True)
    form = MemberForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        if form.member.pk != project.owner_id:
            Membership.objects.get_or_create(project=project, user=form.member)
        messages.success(request, 'Учасник має доступ до проєкту.')
        return redirect('members', pk=pk)
    return render(request, 'board/members.html', {'project': project, 'form': form,
        'memberships': Membership.objects.filter(project=project).select_related('user')})


@login_required
@require_POST
@transaction.atomic
def remove_member(request, pk, user_id):
    project = accessible_project(request.user, pk, owner=True, lock=True)
    if user_id == project.owner_id:
        return HttpResponseBadRequest('Власника не можна видалити.')
    with transaction.atomic():
        Membership.objects.filter(project=project, user_id=user_id).delete()
        project.tasks.filter(assignee_id=user_id).update(assignee=None)
    messages.success(request, 'Учасника видалено, його завдання залишено без виконавця.')
    return redirect('members', pk=pk)


@login_required
@transaction.atomic
def task_form(request, pk=None, project_id=None):
    task = accessible_task(request.user, pk, owner=True, lock=True) if pk else None
    project = task.project if task else accessible_project(request.user, project_id, owner=True, lock=True)
    form = TaskForm(request.POST or None, instance=task, project=project)
    if request.method == 'POST' and form.is_valid():
        task = form.save(commit=False)
        task.project = project
        task.save()
        messages.success(request, 'Завдання збережено.')
        return redirect('task', pk=task.pk)
    return render(request, 'board/form.html', {'form': form, 'project': project,
        'title': 'Редагувати завдання' if pk else 'Нове завдання'})


@login_required
def task_detail(request, pk):
    task = accessible_task(request.user, pk)
    can_change = task.project.owner_id == request.user.pk or (task.assignee_id == request.user.pk and not task.archived)
    return render(request, 'board/task.html', {'task': task, 'project': task.project,
        'comments': task.comments.select_related('author'), 'comment_form': CommentForm(),
        'status_form': StatusForm(instance=task), 'can_change': can_change})


@login_required
@require_POST
@transaction.atomic
def task_status(request, pk):
    task = accessible_task(request.user, pk, lock=True)
    if task.project.owner_id != request.user.pk and (task.assignee_id != request.user.pk or task.archived):
        raise PermissionDenied
    form = StatusForm(request.POST, instance=task)
    if not form.is_valid():
        return HttpResponseBadRequest('Некоректний статус.')
    task.save(update_fields=['status', 'updated_at'])
    return redirect('task', pk=pk)


@login_required
@require_POST
@transaction.atomic
def task_archive(request, pk):
    task = accessible_task(request.user, pk, owner=True, lock=True)
    if request.POST.get('archived') not in ['0', '1']:
        return HttpResponseBadRequest('Некоректний стан архіву.')
    task.archived = request.POST['archived'] == '1'
    task.save(update_fields=['archived', 'updated_at'])
    messages.success(request, 'Завдання архівовано.' if task.archived else 'Завдання відновлено.')
    return redirect('task', pk=pk)


@login_required
@transaction.atomic
def task_delete(request, pk):
    task = accessible_task(request.user, pk, owner=True, lock=True)
    if request.method == 'POST':
        project_id = task.project_id
        task.delete()
        messages.success(request, 'Завдання видалено.')
        return redirect('project', pk=project_id)
    return render(request, 'board/confirm.html', {'title': 'Видалити завдання', 'object': task,
        'warning': 'Коментарі до завдання також буде видалено.', 'project': task.project})


@login_required
@require_POST
@transaction.atomic
def comment_add(request, pk):
    task = accessible_task(request.user, pk, lock=True)
    form = CommentForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest('Коментар має містити від 1 до 3000 символів.')
    comment = form.save(commit=False)
    comment.task = task
    comment.author = request.user
    comment.save()
    return redirect('task', pk=pk)


@require_GET
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except DatabaseError:
        return JsonResponse({'status': 'unavailable'}, status=503)
    response = JsonResponse({'status': 'ok'})
    response['Cache-Control'] = 'no-store'
    return response
