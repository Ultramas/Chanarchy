import datetime

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView, FormView

from guest_user.mixins import RegularUserRequiredMixin
from imagekit.models import ProcessedImageField
from annoying.decorators import ajax_request
from notifications.models import Notification

from .forms import UserCreateForm, PostPictureForm, ProfileEditForm, CommentForm, SettingsForm, BackgroundThemeForm
from .models import UserProfile, IGPost, Comment, Like, Message, Room, BackgroundTheme, SettingsModel


class BackgroundView(ListView):
    model = BackgroundTheme

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        signed_in_user = self.request.user
        if signed_in_user.is_authenticated:
            context['Background'] = BackgroundTheme.objects.filter(is_active=1, user=signed_in_user)
            # Ensure you retrieve the correct UserProfile object for the signed-in user
            context['user_profile'] = UserProfile.objects.filter(user=signed_in_user).first()
        return context

    # Function-based view for the index page
    def index(request):
        if not request.user.is_authenticated:
            return redirect('login')

        posts = []
        user_profile = None
        if hasattr(request.user, 'userprofile'):
            users_followed = request.user.userprofile.following.all()
            posts = IGPost.objects.filter(user_profile__in=users_followed).order_by('-posted_on')
            user_profile = request.user.userprofile

        username = request.user.username if request.user.is_authenticated else None

        context = {
            'username': username,
            'posts': posts,
            'user_profile': user_profile,
        }

        return render(request, 'feeds/index.html', context)


def explore(request):
    random_posts = IGPost.objects.all().order_by('?')[:40]

    context = {
        'posts': random_posts
    }
    return render(request, 'feeds/explore.html', context)


@login_required
def notifications(request):
    context = {}
    return render(request, 'feeds/notifications.html', context)


@login_required
def inbox(request):
    user = request.user
    rooms = Room.objects.filter(Q(receiver=user) | Q(sender=user))
    context = {
        'rooms': rooms
    }
    return render(request, 'feeds/inbox.html', context)


@login_required
def chat(request, label):
    user = request.user
    room = Room.objects.get(label=label)
    messages = reversed(room.messages.order_by('-timestamp')[:50])

    context = {
        'room': room,
        'messages': messages
    }
    return render(request, 'feeds/chat.html', context)


@login_required
def new_chat(request):
    profiles = request.user.userprofile.following.all()
    context = {
        'profiles': profiles
    }
    return render(request, 'feeds/new_chat.html', context)


@login_required
def new_chat_create(request, username):
    user_to_message = User.objects.get(username=username)
    room_label = request.user.username + '_' + user_to_message.username

    try:
        does_room_exist = Room.objects.get(label=room_label)
    except:
        room = Room(label=room_label, receiver=user_to_message,
                    sender=request.user)
        room.save()

    return redirect('chat', label=room_label)


def signup(request):
    form = UserCreateForm()

    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            user = User.objects.get(username=request.POST['username'])
            profile = UserProfile(user=user)
            profile.save()

            new_user = authenticate(username=form.cleaned_data['username'],
                                    password=form.cleaned_data['password1'])
            login(request, new_user)
            return redirect('index')

    return render(request, 'feeds/signup.html', {
        'form': form
    })


def login_user(request):
    form = AuthenticationForm()

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')

    return render(request, 'feeds/login.html', {
        'form': form
    })


def signout(request):
    logout(request)
    return redirect('index')


def signup_success(request):
    return render(request, 'feeds/signup_success.html')


def profile(request, username):
    user = User.objects.get(username=username)
    if not user:
        return redirect('index')

    profile = UserProfile.objects.get(user=user)
    context = {
        'username': username,
        'user': user,
        'profile': profile
    }
    return render(request, 'feeds/profile.html', context)


@login_required
def profile_settings(request, username):
    user = User.objects.get(username=username)
    if request.user != user:
        return redirect('index')

    if request.method == 'POST':
        print(request.POST)
        form = ProfileEditForm(request.POST, instance=user.userprofile, files=request.FILES)
        if form.is_valid():
            form.save()
            return redirect(reverse('profile', kwargs={'username': user.username}))
    else:
        form = ProfileEditForm(instance=user.userprofile)

    context = {
        'user': user,
        'form': form
    }
    return render(request, 'feeds/profile_settings.html', context)


@login_required
def profile_settings(request, username):
    user = User.objects.get(username=username)
    if request.user != user:
        return redirect('index')

    if request.method == 'POST':
        print(request.POST)
        form = ProfileEditForm(request.POST, instance=user.userprofile, files=request.FILES)
        if form.is_valid():
            form.save()
            return redirect(reverse('profile', kwargs={'username': user.username}))
    else:
        form = ProfileEditForm(instance=user.userprofile)

    context = {
        'user': user,
        'form': form
    }
    return render(request, 'feeds/profile_settings.html', context)


class SettingsView(RegularUserRequiredMixin, UserPassesTestMixin, FormView):
    """Only allow registered users to change their settings."""
    model = SettingsModel
    form_class = SettingsForm
    template_name = "feeds/account_settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_settings = self.request.user.settings

        context['username'] = self.request.user.username
        context['password'] = SettingsModel.password
        context['email'] = SettingsModel.email
        return context

    def get_success_url(self):
        # Get the username of the current user
        username = self.request.user.username
        # Redirect to the profile URL with the username as part of the path
        return reverse_lazy('profile', kwargs={'username': username})

    def test_func(self):
        return self.request.user.is_superuser


def background_theme_create(request):
    if request.method == 'POST':
        form = BackgroundThemeForm(request.POST, request.FILES)
        if form.is_valid():
            # Set the user automatically before saving
            background_theme = form.save(commit=False)
            background_theme.user = request.user  # Assuming the user is logged in
            background_theme.save()
            return redirect('themelist')  # Replace with your success URL
    else:
        form = BackgroundThemeForm()

    return render(request, 'feeds/mythemes.html', {'form': form})


class BackgroundThemeListView(ListView):
    model = BackgroundTheme
    template_name = "feeds/themelist.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        signed_in_user = self.request.user
        if signed_in_user.is_authenticated:
            context['theme'] = BackgroundTheme.objects.filter(is_active=1, user=signed_in_user)
            # Ensure you retrieve the correct UserProfile object for the signed-in user
            context['user_profile'] = UserProfile.objects.filter(user=signed_in_user).first()
        return context


def followers(request, username):
    user = User.objects.get(username=username)
    user_profile = UserProfile.objects.get(user=user)
    profiles = user_profile.followers.all

    context = {
        'header': 'Followers',
        'profiles': profiles,
    }

    return render(request, 'feeds/follow_list.html', context)


def following(request, username):
    user = User.objects.get(username=username)
    user_profile = UserProfile.objects.get(user=user)
    profiles = user_profile.following.all

    context = {
        'header': 'Following',
        'profiles': profiles
    }
    return render(request, 'feeds/follow_list.html', context)



@login_required
def post_picture(request):
    if request.method == 'POST':
        form = PostPictureForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            post = IGPost(user_profile=request.user.userprofile,
                          title=request.POST['title'],
                          image=request.FILES['image'],
                          posted_on=datetime.datetime.now())
            post.save()
            return redirect(reverse('profile', kwargs={'username': request.user.username}))
    else:
        form = PostPictureForm()

    context = {
        'form': form
    }
    return render(request, 'feeds/post_picture.html', context)


def post(request, pk):
    post = IGPost.objects.get(pk=pk)
    try:
        like = Like.objects.get(post=post, user=request.user)
        liked = 1
    except:
        like = None
        liked = 0

    context = {
        'post': post,
        'liked': liked
    }
    return render(request, 'feeds/post.html', context)


def likes(request, pk):
    #likes = IGPost.objects.get(pk=pk).like_set.all()
    #profiles = [like.user.userprofile for like in likes]

    post = IGPost.objects.get(pk=pk)
    profiles = Like.objects.filter(post=post)

    context = {
        'header': 'Likes',
        'profiles': profiles
    }
    return render(request, 'feeds/follow_list.html', context)


@ajax_request
@login_required
def add_like(request):
    post_pk = request.POST.get('post_pk')
    post = IGPost.objects.get(pk=post_pk)
    try:
        like = Like(post=post, user=request.user)
        like.save()
        result = 1
    except Exception as e:
        like = Like.objects.get(post=post, user=request.user)
        like.delete()
        result = 0

    return {
        'result': result,
        'post_pk': post_pk
    }


@ajax_request
@login_required
def add_comment(request):
    comment_text = request.POST.get('comment_text')
    post_pk = request.POST.get('post_pk')
    post = IGPost.objects.get(pk=post_pk)
    commenter_info = {}

    try:
        comment = Comment(comment=comment_text, user=request.user, post=post)
        comment.save()

        username = request.user.username
        profile_url = reverse('profile', kwargs={'username': request.user})

        commenter_info = {
            'username': username,
            'profile_url': profile_url,
            'comment_text': comment_text
        }


        result = 1
    except Exception as e:
        print(e)
        result = 0

    return {
        'result': result,
        'post_pk': post_pk,
        'commenter_info': commenter_info
    }


@ajax_request
@login_required
def follow_toggle(request):
    user_profile = UserProfile.objects.get(user=request.user)
    follow_profile_pk = request.POST.get('follow_profile_pk')
    follow_profile = UserProfile.objects.get(pk=follow_profile_pk)

    try:
        if user_profile != follow_profile:
            if request.POST.get('type') == 'follow':
                user_profile.following.add(follow_profile)
                follow_profile.followers.add(user_profile)
            elif request.POST.get('type') == 'unfollow':
                user_profile.following.remove(follow_profile)
                follow_profile.followers.remove(user_profile)
            user_profile.save()
            result = 1
        else:
            result = 0
    except Exception as e:
        print(e)
        result = 0

    return {
        'result': result,
        'type': request.POST.get('type'),
        'follow_profile_pk': follow_profile_pk
    }

@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(recipient=request.user)
    return render(request, 'notifications.html', {'notifications': notifications})