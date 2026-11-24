from django.contrib.auth.models import User
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import EmailConfirm, Task


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class TaskTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='owner', password='test-password')
        cls.other_user = User.objects.create_user(username='other', password='test-password')
        cls.task = Task.objects.create(user=cls.user, title='Learn Django', description='Read a lesson')
        cls.other_task = Task.objects.create(user=cls.other_user, title='Private Django task')

    def setUp(self):
        self.client.force_login(self.user)

    def test_pages_require_login(self):
        self.client.logout()
        urls = [reverse('home'), reverse('profile'), reverse('task_create')]
        for name in ['task_detail', 'task_update', 'task_delete']:
            urls.append(reverse(name, args=[self.task.id]))
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, reverse('login') + '?next=' + url)

    def test_profile_and_search_only_show_own_tasks(self):
        for query in ['', 'dJaNgO']:
            with self.subTest(query=query):
                response = self.client.get(reverse('profile'), {'q': query})
                self.assertContains(response, self.task.title)
                self.assertNotContains(response, self.other_task.title)
        response = self.client.get(reverse('profile'), {'q': 'missing'})
        self.assertContains(response, 'No tasks found')
        self.assertNotContains(response, self.task.title)

    def test_task_pages_show_saved_values(self):
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)
        self.assertContains(self.client.get(reverse('task_create')), 'Create task')
        response = self.client.get(reverse('task_detail', args=[self.task.id]))
        self.assertContains(response, self.task.description)
        self.assertContains(response, 'In progress')
        self.task.is_completed = True
        self.task.save()
        response = self.client.get(reverse('task_update', args=[self.task.id]))
        self.assertContains(response, 'value="Learn Django"')
        self.assertContains(response, self.task.description)
        self.assertContains(response, 'name="is_completed" checked')

    def test_create_task_saves_owner_and_completed_checkbox(self):
        for completed in [False, True]:
            with self.subTest(completed=completed):
                data = {'title': 'New task', 'description': 'Details', 'user': self.other_user.id}
                if completed:
                    data['is_completed'] = 'on'
                response = self.client.post(reverse('task_create'), data)
                self.assertRedirects(response, reverse('profile'))
                task = Task.objects.latest('id')
                self.assertEqual(task.user, self.user)
                self.assertEqual(task.title, 'New task')
                self.assertEqual(task.description, 'Details')
                self.assertEqual(task.is_completed, completed)

    def test_update_task_can_complete_and_reopen_it(self):
        url = reverse('task_update', args=[self.task.id])
        for completed in [True, False]:
            with self.subTest(completed=completed):
                data = {'title': 'Updated task', 'description': 'New details', 'user': self.other_user.id}
                if completed:
                    data['is_completed'] = 'on'
                response = self.client.post(url, data)
                self.assertRedirects(response, reverse('profile'))
                self.task.refresh_from_db()
                self.assertEqual(self.task.title, 'Updated task')
                self.assertEqual(self.task.description, 'New details')
                self.assertEqual(self.task.is_completed, completed)
                self.assertEqual(self.task.user, self.user)

    def test_delete_requires_post(self):
        url = reverse('task_delete', args=[self.task.id])
        self.assertRedirects(self.client.get(url), reverse('profile'))
        self.assertTrue(Task.objects.filter(id=self.task.id).exists())
        self.assertRedirects(self.client.post(url), reverse('profile'))
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())

    def test_other_users_and_missing_tasks_are_not_accessible(self):
        for task_id in [self.other_task.id, self.other_task.id + 1000]:
            with self.subTest(task_id=task_id):
                for name in ['task_detail', 'task_update']:
                    response = self.client.get(reverse(name, args=[task_id]))
                    self.assertRedirects(response, reverse('profile'))
                response = self.client.post(reverse('task_update', args=[task_id]), {'title': 'Changed'})
                self.assertRedirects(response, reverse('profile'))
                response = self.client.post(reverse('task_delete', args=[task_id]))
                self.assertRedirects(response, reverse('profile'))
        self.other_task.refresh_from_db()
        self.assertEqual(self.other_task.title, 'Private Django task')

    def test_task_changes_require_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        urls = [reverse('task_create')]
        for name in ['task_update', 'task_delete']:
            urls.append(reverse(name, args=[self.task.id]))
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(client.post(url, {'title': 'Changed'}).status_code, 403)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Learn Django')
        self.assertEqual(Task.objects.count(), 2)

    def test_registration_and_email_confirmation(self):
        self.client.logout()
        response = self.client.post(reverse('registration'), {
            'username': 'new-user', 'email': 'new@example.com', 'password': 'test-password',
        })
        self.assertRedirects(response, reverse('confirm_email'))
        user = User.objects.get(username='new-user')
        self.assertFalse(user.is_active)
        code = EmailConfirm.objects.get(user=user).code
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(code, mail.outbox[0].body)
        response = self.client.post(reverse('confirm_email'), {'username': user.username, 'code': code})
        self.assertRedirects(response, reverse('profile'))
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(self.client.session['_auth_user_id'], str(user.id))

    def test_unknown_confirmation_user_does_not_crash(self):
        self.client.logout()
        response = self.client.post(reverse('confirm_email'), {'username': 'unknown', 'code': '12345678'})
        self.assertRedirects(response, reverse('confirm_email'))

    def test_login_with_password(self):
        self.client.logout()
        response = self.client.post(reverse('login'), {'username': self.user.username, 'password': 'test-password'})
        self.assertRedirects(response, reverse('profile'))
        self.assertEqual(self.client.session['_auth_user_id'], str(self.user.id))
