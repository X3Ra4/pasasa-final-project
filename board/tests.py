from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from .models import Project, Task, Membership, Comment
from django.test import TransactionTestCase
from django.db import connection, connections, transaction
from unittest import skipUnless
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import time


class WebsiteContractTests(TestCase):
    def test_owner_can_create_project(self):
        user = get_user_model().objects.create_user('owner', password='Good-pass-12345')
        self.client.force_login(user)
        response = self.client.post('/projects/new/', {'name': 'Release', 'description': 'Team work'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/projects/'))


class WorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_user('owner', password='Good-pass-12345')
        cls.member = User.objects.create_user('member', password='Good-pass-12345')
        cls.outsider = User.objects.create_user('outsider', password='Good-pass-12345')
        cls.project = Project.objects.create(name='Private release', owner=cls.owner)
        Membership.objects.create(project=cls.project, user=cls.member)
        cls.task = Task.objects.create(project=cls.project, title='Ship feature', assignee=cls.member)

    def setUp(self):
        self.client.force_login(self.owner)
        self.api = APIClient()
        self.api.force_authenticate(self.owner)

    def test_anonymous_redirected(self):
        self.client.logout()
        self.assertEqual(self.client.get('/').status_code, 302)

    def test_outsider_cannot_read_private_pages(self):
        self.client.force_login(self.outsider)
        for url in [f'/projects/{self.project.pk}/', f'/tasks/{self.task.pk}/', f'/projects/{self.project.pk}/members/']:
            self.assertEqual(self.client.get(url).status_code, 404)
        self.assertNotContains(self.client.get('/'), self.project.name)

    def test_owner_task_crud(self):
        response = self.client.post(f'/projects/{self.project.pk}/tasks/new/', {
            'title': 'New work', 'status': 'todo', 'priority': 'high', 'assignee': self.owner.pk})
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(title='New work')
        self.assertEqual(task.assignee, self.owner)
        self.assertEqual(self.client.post(f'/tasks/{task.pk}/edit/', {
            'title': 'Updated work', 'status': 'doing', 'priority': 'normal'}).status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.title, 'Updated work')
        self.assertEqual(self.client.post(f'/tasks/{task.pk}/delete/').status_code, 302)
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())

    def test_project_edit_delete(self):
        self.assertEqual(self.client.post(f'/projects/{self.project.pk}/edit/', {'name': 'Renamed'}).status_code, 302)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Renamed')
        self.assertEqual(self.client.post(f'/projects/{self.project.pk}/delete/').status_code, 302)
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())

    def test_invalid_assignee_rejected_in_html(self):
        response = self.client.post(f'/projects/{self.project.pk}/tasks/new/', {
            'title': 'Intruder', 'status': 'todo', 'priority': 'normal', 'assignee': self.outsider.pk})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(title='Intruder').exists())

    def test_member_only_changes_assigned_status(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.post(f'/tasks/{self.task.pk}/status/', {'status': 'done', 'title': 'Injected'}).status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'done')
        self.assertEqual(self.task.title, 'Ship feature')
        for url in [f'/tasks/{self.task.pk}/edit/', f'/tasks/{self.task.pk}/delete/',
                    f'/projects/{self.project.pk}/edit/', f'/projects/{self.project.pk}/tasks/new/']:
            self.assertEqual(self.client.post(url, {}).status_code, 403)

    def test_unassigned_member_cannot_change_status(self):
        self.task.assignee = self.owner
        self.task.save()
        self.client.force_login(self.member)
        self.assertEqual(self.client.post(f'/tasks/{self.task.pk}/status/', {'status': 'done'}).status_code, 403)

    def test_remove_member_revokes_access_and_assignment(self):
        self.assertEqual(self.client.post(f'/projects/{self.project.pk}/members/{self.member.pk}/remove/').status_code, 302)
        self.task.refresh_from_db()
        self.assertIsNone(self.task.assignee)
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(f'/tasks/{self.task.pk}/').status_code, 404)

    def test_add_member_idempotent(self):
        for _ in range(2):
            self.assertEqual(self.client.post(f'/projects/{self.project.pk}/members/', {'username': self.outsider.username}).status_code, 302)
        self.assertEqual(Membership.objects.filter(project=self.project, user=self.outsider).count(), 1)

    def test_archive_restore(self):
        self.client.post(f'/tasks/{self.task.pk}/archive/', {'archived': '1'})
        self.task.refresh_from_db()
        self.assertTrue(self.task.archived)
        self.assertNotContains(self.client.get(f'/projects/{self.project.pk}/'), self.task.title)
        self.assertContains(self.client.get(f'/projects/{self.project.pk}/?archived=1'), self.task.title)
        self.client.force_login(self.member)
        self.assertEqual(self.client.post(f'/tasks/{self.task.pk}/status/', {'status': 'done'}).status_code, 403)
        self.client.force_login(self.owner)
        self.client.post(f'/tasks/{self.task.pk}/archive/', {'archived': '0'})
        self.task.refresh_from_db()
        self.assertFalse(self.task.archived)

    def test_comments_escaped_and_author_not_forged(self):
        self.client.force_login(self.member)
        self.client.post(f'/tasks/{self.task.pk}/comments/', {'body': '<script>alert(1)</script>', 'author': self.owner.pk})
        self.assertEqual(Comment.objects.get().author, self.member)
        response = self.client.get(f'/tasks/{self.task.pk}/')
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')

    def test_mutations_reject_get(self):
        for url in [f'/tasks/{self.task.pk}/archive/', f'/tasks/{self.task.pk}/status/',
                    f'/tasks/{self.task.pk}/comments/', f'/projects/{self.project.pk}/members/{self.member.pk}/remove/']:
            self.assertEqual(self.client.get(url).status_code, 405)
        self.client.get(f'/tasks/{self.task.pk}/delete/')
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())

    def test_csrf_required(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(client.post(f'/tasks/{self.task.pk}/delete/').status_code, 403)

    def test_filters_stats_and_sorting(self):
        Task.objects.create(project=self.project, title='Urgent work', priority='high', due_date=timezone.localdate()-timedelta(days=1))
        Task.objects.create(project=self.project, title='Done work', status='done')
        Task.objects.create(project=self.project, title='Old archive', archived=True)
        response = self.client.get(f'/projects/{self.project.pk}/?q=urgent&priority=high&sort=due')
        self.assertContains(response, 'Urgent work')
        self.assertNotContains(response, self.task.title)
        self.assertEqual(response.context['stats'], {'total': 3, 'active': 2, 'done': 1, 'overdue': 1})

    def test_api_list_isolation(self):
        self.api.force_authenticate(self.outsider)
        self.assertEqual(self.api.get('/api/tasks/').json()['count'], 0)
        self.assertEqual(self.api.get('/api/projects/').json()['count'], 0)
        self.assertEqual(self.api.get(f'/api/tasks/{self.task.pk}/').status_code, 404)

    def test_api_owner_crud_and_validation(self):
        payload = {'title': 'API work', 'project': self.project.pk, 'assignee': self.member.pk}
        response = self.api.post('/api/tasks/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        task_id = response.json()['id']
        self.assertEqual(self.api.patch(f'/api/tasks/{task_id}/', {'title': 'API revised'}, format='json').status_code, 200)
        self.assertEqual(self.api.patch(f'/api/tasks/{task_id}/', {'assignee': self.outsider.pk}, format='json').status_code, 400)
        other = Project.objects.create(name='Other', owner=self.owner)
        self.assertEqual(self.api.patch(f'/api/tasks/{task_id}/', {'project': other.pk}, format='json').status_code, 400)
        self.assertEqual(self.api.delete(f'/api/tasks/{task_id}/').status_code, 204)

    def test_api_member_permissions(self):
        self.api.force_authenticate(self.member)
        self.assertEqual(self.api.patch(f'/api/tasks/{self.task.pk}/', {'status': 'doing'}, format='json').status_code, 200)
        self.assertEqual(self.api.patch(f'/api/tasks/{self.task.pk}/', {'title': 'Hack'}, format='json').status_code, 403)
        self.assertEqual(self.api.delete(f'/api/tasks/{self.task.pk}/').status_code, 403)
        self.assertEqual(self.api.post('/api/tasks/', {'title': 'Hack', 'project': self.project.pk}, format='json').status_code, 403)
        self.assertEqual(self.api.patch(f'/api/tasks/{self.task.pk}/', {'archived': True}, format='json').status_code, 403)

    def test_api_comments_and_archived_member(self):
        self.api.force_authenticate(self.member)
        response = self.api.post(f'/api/tasks/{self.task.pk}/comments/', {'body': 'Looks good'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Comment.objects.get().author, self.member)
        self.task.archived = True
        self.task.save()
        self.assertEqual(self.api.patch(f'/api/tasks/{self.task.pk}/', {'status': 'done'}, format='json').status_code, 403)

    def test_api_auth_required(self):
        self.api.force_authenticate(None)
        self.assertIn(self.api.get('/api/tasks/').status_code, [401, 403])

    def test_invalid_status_and_empty_comment(self):
        self.assertEqual(self.client.post(f'/tasks/{self.task.pk}/status/', {'status': 'invalid'}).status_code, 400)
        self.assertEqual(self.client.post(f'/tasks/{self.task.pk}/comments/', {'body': '   '}).status_code, 400)
        self.assertFalse(Comment.objects.exists())

    def test_signup_login_logout(self):
        self.client.logout()
        response = self.client.post('/accounts/signup/', {
            'username': 'new-person', 'password1': 'Teamflow-2026-strong', 'password2': 'Teamflow-2026-strong'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/accounts/logout/').status_code, 405)
        self.client.post('/accounts/logout/')
        self.assertEqual(self.client.get('/').status_code, 302)
        response = self.client.post('/accounts/login/', {'username': 'new-person', 'password': 'Teamflow-2026-strong'})
        self.assertEqual(response.status_code, 302)

    def test_token_auth_and_inactive_user(self):
        from rest_framework.authtoken.models import Token
        token = Token.objects.create(user=self.member)
        self.api.force_authenticate(None)
        self.api.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        self.assertEqual(self.api.get('/api/tasks/').json()['count'], 1)
        self.member.is_active = False
        self.member.save()
        self.assertIn(self.api.get('/api/tasks/').status_code, [401, 403])

    def test_api_filters_order_stats(self):
        Task.objects.create(project=self.project, title='Important', priority='high', due_date=timezone.localdate())
        response = self.api.get('/api/tasks/?sort=priority')
        self.assertEqual(response.json()['results'][0]['title'], 'Important')
        self.assertEqual(self.api.get('/api/tasks/?assignee=none').json()['count'], 1)
        self.assertEqual(self.api.get(f'/api/projects/{self.project.pk}/stats/').json()['total'], 2)

    def test_seed_idempotent_preserves_edits(self):
        from django.core.management import call_command
        from io import StringIO
        call_command('seed_demo', owner=self.owner.username, stdout=StringIO())
        count = Task.objects.count()
        demo = Task.objects.filter(project__owner=self.owner).exclude(pk=self.task.pk).first()
        demo.description = 'Personal edit'
        demo.save()
        call_command('seed_demo', owner=self.owner.username, stdout=StringIO())
        self.assertEqual(Task.objects.count(), count)
        demo.refresh_from_db()
        self.assertEqual(demo.description, 'Personal edit')

    def test_health_and_database_failure(self):
        from unittest.mock import patch
        from django.db import DatabaseError
        self.assertEqual(self.client.get('/healthz/').json(), {'status': 'ok'})
        with patch('board.views.connection.cursor', side_effect=DatabaseError('private connection info')):
            response = self.client.get('/healthz/')
        self.assertEqual(response.status_code, 503)
        self.assertNotContains(response, 'private', status_code=503)

    def test_browsable_api_does_not_list_unrelated_users(self):
        self.api.force_authenticate(self.outsider)
        response = self.api.get('/api/tasks/', HTTP_ACCEPT='text/html')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '>owner</option>')
        self.assertNotContains(response, '>member</option>')
        self.api.force_authenticate(self.owner)
        response = self.api.get(f'/api/tasks/{self.task.pk}/', HTTP_ACCEPT='text/html')
        self.assertNotContains(response, '>outsider</option>')

    def test_status_update_does_not_overwrite_other_task_fields(self):
        from unittest.mock import patch
        from .forms import StatusForm
        original_is_valid = StatusForm.is_valid

        def archive_after_validation(form):
            result = original_is_valid(form)
            Task.objects.filter(pk=self.task.pk).update(archived=True, assignee=None)
            return result

        self.client.force_login(self.member)
        with patch.object(StatusForm, 'is_valid', archive_after_validation):
            self.client.post(f'/tasks/{self.task.pk}/status/', {'status': 'doing'})
        self.task.refresh_from_db()
        self.assertTrue(self.task.archived)
        self.assertIsNone(self.task.assignee)

    def test_malformed_numeric_filters_never_crash(self):
        for value in ['²', '9' * 100, '-1', 'abc']:
            for field in ['assignee', 'project']:
                self.assertEqual(self.api.get('/api/tasks/', {field: value}).status_code, 200)
            self.assertEqual(self.client.get(f'/projects/{self.project.pk}/', {'assignee': value}).status_code, 200)


@skipUnless(connection.vendor == 'postgresql', 'Row-lock concurrency requires PostgreSQL')
class ConcurrentPermissionsTests(TransactionTestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user('concurrent-owner')
        self.member = User.objects.create_user('concurrent-member')
        self.project = Project.objects.create(name='Concurrency', owner=self.owner)
        Membership.objects.create(project=self.project, user=self.member)
        self.task = Task.objects.create(project=self.project, title='Concurrent work', assignee=self.member)
        self.client.force_login(self.member)

    def assert_serialized(self, api=False, remove=False):
        started = Event()
        task_id = self.task.pk
        member_client = self.client
        if api:
            member_client = APIClient()
            member_client.force_authenticate(self.member)

        def member_request():
            try:
                started.set()
                if api:
                    return member_client.patch(f'/api/tasks/{task_id}/', {'status': 'done'}, format='json').status_code
                return member_client.post(f'/tasks/{task_id}/status/', {'status': 'done'}).status_code
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                Project.objects.select_for_update().get(pk=self.project.pk)
                if remove:
                    Membership.objects.filter(project=self.project, user=self.member).delete()
                    Task.objects.filter(pk=task_id).update(assignee=None)
                else:
                    Task.objects.filter(pk=task_id).update(archived=True)
                future = pool.submit(member_request)
                self.assertTrue(started.wait(timeout=3))
                time.sleep(.25)
                was_waiting = not future.done()
            self.assertTrue(was_waiting, 'Member mutation must wait for the owner project transaction')
            self.assertEqual(future.result(timeout=10), 404 if remove else 403)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'todo')
        if remove:
            self.assertIsNone(self.task.assignee)
        else:
            self.assertTrue(self.task.archived)

    def test_html_status_waits_for_archive(self):
        self.assert_serialized()

    def test_api_status_waits_for_archive(self):
        self.assert_serialized(api=True)

    def test_html_status_waits_for_membership_removal(self):
        self.assert_serialized(remove=True)

    def test_api_status_waits_for_membership_removal(self):
        self.assert_serialized(api=True, remove=True)
