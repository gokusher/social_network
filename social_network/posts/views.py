from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect

from .models import Post, Group, Comment, Follow
from .forms import PostForm, CommentForm

LAST_POSTS = 10


def paginator_group(request, post_list):
    paginator = Paginator(post_list, LAST_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.select_related('author', 'group').all()
    page_obj = paginator_group(request, post_list)
    return render(request, template, {'page_obj': page_obj})


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author').all()
    page_obj = paginator_group(request, post_list)
    context = {'group': group,
               'page_obj': page_obj}
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group').all()
    page_obj = paginator_group(request, post_list)
    following = (request.user.is_authenticated
                 and Follow.objects.filter(user=request.user,
                                           author=author).exists())
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def delete_comment(request, comment_id, post_id):
    comment = get_object_or_404(Comment, id=comment_id)
    post = get_object_or_404(Post, id=post_id)
    if comment.author == request.user:
        comment.delete()
    return redirect('posts:post_detail', post.id)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    author = post.author
    if author != request.user:
        return redirect('posts:post_detail', post_id)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author == request.user:
        post.delete()
    return redirect('posts:profile', request.user)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    posts_list = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator_group(request, posts_list)
    context = {"page_obj": page_obj}
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    Follow.objects.filter(user=user, author__username=username).delete()
    return redirect("posts:profile", username=username)
