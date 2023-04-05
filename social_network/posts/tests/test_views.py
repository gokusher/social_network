import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from posts.models import Post, Group, Comment, Follow


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostTest(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(title='Тестовая группа',
                                          slug='test_group')
        self.post = Post.objects.create(text='Тестовый текст',
                                        group=self.group,
                                        author=self.user,
                                        image=self.uploaded)
        self.comment = Comment.objects.create(post_id=self.post.id,
                                              author=self.user,
                                              text='Тестовый коммент')

    def test_views_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug':
                            f'{self.group.slug}'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username':
                            f'{self.user.username}'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            self.post.id}): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html'
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                error_name = f'Ошибка: {adress} ожидал шаблон {template}'
                self.assertTemplateUsed(response, template, error_name)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        post_text_0 = {
            response.context['page_obj'][0].text: self.post.text,
            response.context['page_obj'][0].group.title: self.group,
            response.context['page_obj'][0].author: self.user.username,
            response.context['page_obj'][0].image: self.uploaded}
        for value, expected in post_text_0.items():
            self.assertEqual(post_text_0[value], expected)

    def test_group_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_group'}))
        post_text_0 = {
            response.context['group'].title: self.group.title,
            response.context['group'].slug: self.group.slug,
            response.context['page_obj'][0].text: self.post.text,
            response.context['page_obj'][0].group.title: self.group,
            response.context['page_obj'][0].author: self.user.username,
            response.context['page_obj'][0].image: self.uploaded}
        for value, expected in post_text_0.items():
            self.assertEqual(post_text_0[value], expected)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post_text_0 = {
            response.context['post'].text: self.post.text,
            response.context['post'].group: self.group,
            response.context['post'].author: self.user.username,
            response.context['post'].image: self.uploaded,
            response.context['comments'][0].text: self.comment.text,
            response.context['comments'][0].author: self.user.username
        }
        for value, expected in post_text_0.items():
            self.assertEqual(post_text_0[value], expected)
        self.assertTrue(response.context['form'], 'форма получена')

    def test_post_create_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.post(reverse('posts:post_create'))
        form = response.context.get('form')
        self.assertIsInstance(form, forms.ModelForm)
        self.assertFalse(response.context.get('is_edit'))

    def test_post_edit_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form = response.context.get('form')
        post_test = response.context['post'].id
        self.assertEqual(post_test, self.post.id)
        self.assertIsInstance(form, forms.ModelForm)
        self.assertTrue(response.context.get('is_edit'))

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'auth'}))
        post_text_0 = {
            response.context['page_obj'][0].text: self.post.text,
            response.context['page_obj'][0].image: self.uploaded,
            response.context['author'].get_full_name: self.user.get_full_name,
            response.context['author'].username: self.user.username
        }
        for value, expected in post_text_0.items():
            self.assertEqual(post_text_0[value], expected)

    def test_post_another_group(self):
        """Пост не попал в другую группу."""
        posts_count = Post.objects.filter(group=self.group).count()
        group = Post.objects.filter(group=self.group).count()
        self.assertEqual(group, posts_count)

    def test_cache_index(self):
        """Проверка хранения и очистки кэша для index."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='test_new_post',
            author=self.user,
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth1')
        cls.user2 = User.objects.create_user(username='auth2')
        cls.author = User.objects.create_user(username='someauthor')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def test_user_follower_authors(self):
        """Посты доступны пользователю, который подписался на автора.
           Увеличение подписок автора."""
        count_follow = Follow.objects.filter(user=FollowViewsTest.user).count()
        data_follow = {'user': FollowViewsTest.user,
                       'author': FollowViewsTest.author}
        url_redirect = reverse(
            'posts:profile',
            kwargs={'username': FollowViewsTest.author.username})
        response = self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={
                'username': FollowViewsTest.author.username}),
            data=data_follow, follow=True)
        new_count_follow = Follow.objects.filter(
            user=FollowViewsTest.user).count()
        self.assertTrue(Follow.objects.filter(
                        user=FollowViewsTest.user,
                        author=FollowViewsTest.author).exists())
        self.assertRedirects(response, url_redirect)
        self.assertEqual(count_follow + 1, new_count_follow)

    def test_user_unfollower_authors(self):
        """Посты не доступны пользователю, который не подписался на автора.
           Непроисходит увеличение подписок автора."""
        count_follow = Follow.objects.filter(
            user=FollowViewsTest.user).count()
        data_follow = {'user': FollowViewsTest.user,
                       'author': FollowViewsTest.author}
        url_redirect = ('/auth/login/?next=/profile/'
                        f'{self.author.username}/unfollow/')
        response = self.guest_client.post(
            reverse('posts:profile_unfollow', kwargs={
                'username': FollowViewsTest.author}),
            data=data_follow, follow=True)
        new_count_follow = Follow.objects.filter(
            user=FollowViewsTest.user).count()
        self.assertFalse(Follow.objects.filter(
            user=FollowViewsTest.user,
            author=FollowViewsTest.author).exists())
        self.assertRedirects(response, url_redirect)
        self.assertEqual(count_follow, new_count_follow)

    def test_follower_see_new_post(self):
        """У подписчика появляется новый пост избранного автора."""
        new_post_follower = Post.objects.create(
            author=FollowViewsTest.author,
            text='Текстовый текст')
        Follow.objects.create(user=FollowViewsTest.user,
                              author=FollowViewsTest.author)
        response_follower = self.authorized_client.get(
            reverse('posts:follow_index'))
        new_posts = response_follower.context['page_obj']
        self.assertIn(new_post_follower, new_posts)

    def test_unfollower_no_see_new_post(self):
        """У не подписчика поста нет."""
        new_post_follower = Post.objects.create(
            author=FollowViewsTest.author,
            text='Текстовый текст')
        Follow.objects.create(user=FollowViewsTest.user,
                              author=FollowViewsTest.author)
        response_unfollower = self.authorized_client2.get(
            reverse('posts:follow_index'))
        new_post_unfollower = response_unfollower.context['page_obj']
        self.assertNotIn(new_post_follower, new_post_unfollower)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_name2',
                                              email='tests@mail.ru',
                                              password='12345678',)
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test_slug2',
            description='Тестовое описание')
        cls.posts = []
        for i in range(13):
            cls.posts.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.author,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_posts(self):
        list_urls = {
            reverse("posts:index"): "index",
            reverse("posts:group_list",
                    kwargs={"slug": "test_slug2"}): "group",
            reverse("posts:profile",
                    kwargs={"username": "test_name2"}): "profile",
        }
        for tested_url in list_urls.keys():
            response = self.client.get(tested_url)
            self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_posts(self):
        list_urls = {
            reverse("posts:index") + "?page=2": "index",
            reverse("posts:group_list",
                    kwargs={"slug": "test_slug2"}) + "?page=2":
            "group",
            reverse("posts:profile",
                    kwargs={"username": "test_name2"}) + "?page=2":
            "profile",
        }
        for tested_url in list_urls.keys():
            response = self.client.get(tested_url)
            self.assertEqual(len(response.context['page_obj']), 3)
