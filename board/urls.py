from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('accounts/signup/', views.signup, name='signup'),
    path('projects/new/', views.project_form, name='project_new'),
    path('projects/<int:pk>/', views.project_detail, name='project'),
    path('projects/<int:pk>/edit/', views.project_form, name='project_edit'),
    path('projects/<int:pk>/delete/', views.project_delete, name='project_delete'),
    path('projects/<int:pk>/members/', views.members, name='members'),
    path('projects/<int:pk>/members/<int:user_id>/remove/', views.remove_member, name='remove_member'),
    path('projects/<int:project_id>/tasks/new/', views.task_form, name='task_new'),
    path('tasks/<int:pk>/', views.task_detail, name='task'),
    path('tasks/<int:pk>/edit/', views.task_form, name='task_edit'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('tasks/<int:pk>/status/', views.task_status, name='task_status'),
    path('tasks/<int:pk>/archive/', views.task_archive, name='task_archive'),
    path('tasks/<int:pk>/comments/', views.comment_add, name='comment_add'),
    path('healthz/', views.health, name='health'),
]
