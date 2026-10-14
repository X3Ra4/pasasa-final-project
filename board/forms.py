from django import forms
from django.contrib.auth import get_user_model
from .models import Project, Task, Comment
from .policies import project_users


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assignee', 'status', 'priority', 'due_date']
        widgets = {'due_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')}

    def __init__(self, *args, project, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assignee'].queryset = project_users(project)


class MemberForm(forms.Form):
    username = forms.CharField(label='Ім’я користувача', max_length=150,
        help_text='Укажіть точне ім’я вже зареєстрованого учасника.')

    def clean_username(self):
        name = self.cleaned_data['username']
        try:
            self.member = get_user_model().objects.get(username=name, is_active=True)
        except get_user_model().DoesNotExist:
            raise forms.ValidationError('Активного користувача з таким іменем не знайдено.')
        return name


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']
        widgets = {'body': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Напишіть коментар…'})}


class StatusForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['status']
