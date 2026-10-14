from rest_framework import serializers, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import Project, Task, Comment
from .policies import visible_projects, project_users, filtered_tasks, task_stats, numeric_id, lock_visible_project


class ProjectMutationLockMixin:
    """All HTML and REST writes use the same project lock, including membership changes."""
    @transaction.atomic
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method in permissions.SAFE_METHODS:
            return
        if self.kwargs.get('pk'):
            obj = self.get_object()
            project_id = obj.project_id if isinstance(obj, Task) else obj.pk
        elif self.basename == 'api-task':
            project_id = numeric_id(request.data.get('project', ''))
        else:
            project_id = None
        if project_id:
            lock_visible_project(request.user, project_id)


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'owner', 'created_at']
        read_only_fields = ['id', 'owner', 'created_at']


class ProjectViewSet(ProjectMutationLockMixin, viewsets.ModelViewSet):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return visible_projects(self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.owner_id != self.request.user.pk:
            raise PermissionDenied('Лише власник може редагувати проєкт.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.owner_id != self.request.user.pk:
            raise PermissionDenied('Лише власник може видалити проєкт.')
        instance.delete()

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        return Response(task_stats(self.get_object().tasks.all()))


class TaskSerializer(serializers.ModelSerializer):
    assignee_name = serializers.CharField(source='assignee.username', read_only=True, default=None)

    class Meta:
        model = Task
        fields = ['id', 'project', 'title', 'description', 'assignee', 'assignee_name', 'status',
                  'priority', 'due_date', 'archived', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = visible_projects(self.context['request'].user)
        self.fields['assignee'].queryset = get_user_model().objects.none()
        project = self.instance.project if isinstance(self.instance, Task) else None
        if not project:
            project_id = numeric_id(getattr(self, 'initial_data', {}).get('project', ''))
            if project_id:
                project = visible_projects(self.context['request'].user).filter(pk=project_id).first()
        if project:
            self.fields['assignee'].queryset = project_users(project)

    def validate(self, attrs):
        instance = self.instance
        project = attrs.get('project', instance.project if instance else None)
        if instance and project.pk != instance.project_id:
            raise serializers.ValidationError({'project': 'Перенесення між проєктами не підтримується.'})
        assignee = attrs.get('assignee', instance.assignee if instance else None)
        if assignee and not project_users(project).filter(pk=assignee.pk).exists():
            raise serializers.ValidationError({'assignee': 'Виконавець має бути активним учасником проєкту.'})
        return attrs


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True, default='Видалений користувач')

    class Meta:
        model = Comment
        fields = ['id', 'body', 'author_name', 'created_at']
        read_only_fields = ['id', 'author_name', 'created_at']


class TaskViewSet(ProjectMutationLockMixin, viewsets.ModelViewSet):
    serializer_class = TaskSerializer

    def get_queryset(self):
        queryset = Task.objects.filter(project__in=visible_projects(self.request.user)).select_related('project', 'assignee')
        if self.action == 'list':
            project_id = self.request.query_params.get('project', '')
            if numeric_id(project_id):
                queryset = queryset.filter(project_id=numeric_id(project_id))
            return filtered_tasks(queryset, self.request.query_params)
        return queryset

    def perform_create(self, serializer):
        if serializer.validated_data['project'].owner_id != self.request.user.pk:
            raise PermissionDenied('Лише власник може створювати завдання.')
        serializer.save()

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        if task.project.owner_id != request.user.pk:
            if task.assignee_id != request.user.pk or task.archived or set(request.data) != {'status'}:
                raise PermissionDenied('Виконавець може змінювати лише статус активного завдання.')
            kwargs['partial'] = True
        serializer = self.get_serializer(task, data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def perform_destroy(self, instance):
        if instance.project.owner_id != self.request.user.pk:
            raise PermissionDenied('Лише власник може видаляти завдання.')
        instance.delete()

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        task = self.get_object()
        if request.method == 'POST':
            serializer = CommentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(task=task, author=request.user)
            return Response(serializer.data, status=201)
        queryset = task.comments.select_related('author')
        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(CommentSerializer(page, many=True).data)
