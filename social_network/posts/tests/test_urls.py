from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post


User = get_user_model()


class TaskURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовое описание поста')
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание')

    def test_home_and_group(self):
        """Проверка открытых страниц на доступность всем пользователям."""
        url_names = (
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/',
        )
        for adress in url_names:
            with self.subTest():
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_authorized_client(self):
        """Доступ авторизованного пользователя"""
        url_names = ('/create/',
                     f'/posts/{self.post.id}/edit/')
        for adress in url_names:
            response = self.authorized_client.get(adress)
            error_name = f'Ошибка: нет доступа до страницы {adress}'
            self.assertEqual(response.status_code, HTTPStatus.OK, error_name)

    def test_private_url(self):
        """без авторизации приватные URL недоступны"""
        url_names = ('/create/',
                     f'/posts/{self.post.id}/edit/')
        for adress in url_names:
            with self.subTest():
                response = self.guest_client.get(adress)
                error_name = 'Страница доступна только авторизованному юзеру'
                self.assertEqual(response.status_code,
                                 HTTPStatus.FOUND,
                                 error_name)

    def test_urls_redirect_guest_client(self):
        """Редирект неавторизованного пользователя."""
        url1 = '/auth/login/?next=/create/'
        url2 = f'/auth/login/?next=/posts/{self.post.id}/edit/'
        pages = {'/create/': url1,
                 f'/posts/{self.post.id}/edit/': url2}
        for page, value in pages.items():
            response = self.guest_client.get(page)
            self.assertRedirects(response, value)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names: dict = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html'
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                error_name = f'Ошибка: {adress} ожидал шаблон {template}'
                self.assertTemplateUsed(response, template, error_name)

    def test_page_404(self):
        response = self.guest_client.get('/qwerty123456/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
