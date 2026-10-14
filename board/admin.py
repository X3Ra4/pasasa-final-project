from django.contrib import admin
from .models import Project, Membership, Task, Comment


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'created_at']
    search_fields = ['name', 'owner__username']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'assignee', 'status', 'priority', 'archived']
    list_filter = ['status', 'priority', 'archived']
    search_fields = ['title', 'description']


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['project', 'user', 'joined_at']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'author', 'created_at']
    search_fields = ['body']
