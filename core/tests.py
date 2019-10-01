from django.test import TestCase, Client
from django.contrib.auth.models import User


class AccessTestCase(TestCase):
    def setUp(self):
        self.user = {
            'username': 'test',
            'password': 'test'}
        User.objects.create_user(**self.user)

    def test_login(self):
        c = Client()
        response = c.post('/login/',  self.user, follow=True)
        self.assertTrue(response.context['user'].is_active)
