import datetime
from venv import logger

from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import CreateView, FormView, UpdateView

from guest_user.mixins import RegularUserRequiredMixin
from imagekit.models import ProcessedImageField
from annoying.decorators import ajax_request
from notifications.models import Notification
from django.shortcuts import redirect

from .forms import UserCreateForm, PostPictureForm, ProfileEditForm, CommentForm, SettingsForm, BackgroundThemeForm, \
    CreateCommunityForm, RoomSettings
from .models import UserProfile, IGPost, Comment, Like, Message, Room, BackgroundTheme, SettingsModel, Community, \
    Friend, DefaultAvatar, DirectMessages, DirectMessageText


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


class ExploreView(ListView):
    model = BackgroundTheme
    template_name = 'feeds/explore.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        signed_in_user = self.request.user

        if signed_in_user.is_authenticated:
            context['theme'] = BackgroundTheme.objects.filter(is_active=1, user=signed_in_user)
            context['user_profile'] = UserProfile.objects.filter(user=signed_in_user).first()

        # Add random posts (reverse order handled in template)
        context['posts'] = IGPost.objects.all().order_by('?')[:40]
        return context


class ScrollExploreView(ListView):
    model = BackgroundTheme
    template_name = 'feeds/scrollexplore.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        signed_in_user = self.request.user

        if signed_in_user.is_authenticated:
            context['Background'] = BackgroundTheme.objects.filter(is_active=1, user=signed_in_user)
            context['user_profile'] = UserProfile.objects.filter(user=signed_in_user).first()

        # Add random posts (reverse order handled in template)
        context['posts'] = IGPost.objects.all().order_by('?')[:40]
        return context


class DiscoverCommunityView(ListView):
    model = Community
    template_name = 'feeds/discover.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        signed_in_user = self.request.user

        if signed_in_user.is_authenticated:
            context['theme'] = BackgroundTheme.objects.filter(is_active=1, user=signed_in_user)
            context['user_profile'] = UserProfile.objects.filter(user=signed_in_user).first()
        context['server'] = Community.objects.all().order_by('?')[:40]
        return context


class ScrollDiscoverView(ListView):
    model = Community
    template_name = 'feeds/scrolldiscover.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        signed_in_user = self.request.user

        if signed_in_user.is_authenticated:
            context['theme'] = BackgroundTheme.objects.filter(is_active=1, user=signed_in_user)
            context['user_profile'] = UserProfile.objects.filter(user=signed_in_user).first()
        context['server'] = Community.objects.all().order_by('?')[:40]
        return context


from django.http import HttpResponseRedirect


class CreateCommunityView(CreateView):
    model = Community
    form_class = CreateCommunityForm
    template_name = 'feeds/create_community.html'
    success_url = reverse_lazy('mycommunities')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        signed_in_user = self.request.user

        if signed_in_user.is_authenticated:
            context['theme'] = BackgroundTheme.objects.filter(is_active=1, user=signed_in_user)
            context['user_profile'] = UserProfile.objects.filter(user=signed_in_user).first()
        context['server'] = Community.objects.all().order_by('?')[:40]
        return context

    def form_valid(self, form):
        # Perform additional actions before saving the form if necessary
        form.instance.user = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        # This will help debug why the form is invalid
        print(form.errors)  # You can log this for debugging
        return self.render_to_response(self.get_context_data(form=form))


class MyCommunityView(ListView):
    model = Community
    template_name = 'feeds/mycommunities.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        signed_in_user = self.request.user

        if signed_in_user.is_authenticated:
            context['mycommunities'] = Community.objects.filter(is_active=1, user=signed_in_user)
            context['communityin'] = Community.objects.filter(is_active=True, members=signed_in_user)
            context['theme'] = BackgroundTheme.objects.filter(is_active=1, user=signed_in_user)
            context['user_profile'] = UserProfile.objects.filter(user=signed_in_user).first()
        return context


class FriendView(ListView):
    model = Friend
    template_name = 'feeds/friendslist.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        signed_in_user = self.request.user

        if signed_in_user.is_authenticated:
            context['theme'] = BackgroundTheme.objects.filter(is_active=1, user=signed_in_user)
            context['user_profile'] = UserProfile.objects.filter(user=signed_in_user).first()

            # Prefetch userprofile data related to each friend
            friends_with_profiles = Friend.objects.filter(user=signed_in_user).select_related('friend__userprofile')
            context['friends'] = friends_with_profiles
        return context

from django.db.models import Q

from django.http import JsonResponse
from django.template.loader import render_to_string


class FriendSearchResultsView(ListView):
    model = Friend
    template_name = 'feeds/friendslist.html'
    context_object_name = 'friends'

    def get_queryset(self):
        search_term = self.request.GET.get('search', '')
        if search_term:
            friends = Friend.objects.filter(friend__username__icontains=search_term)
        else:
            friends = Friend.objects.filter(user=self.request.user)

        # Return a distinct set of friends
        distinct_friends = []
        seen_friends = set()

        for friend in friends:
            if friend.friend not in seen_friends:
                distinct_friends.append(friend)
                seen_friends.add(friend.friend)

        return distinct_friends

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('search', '')
        return context

    def friend_search(self, request):
        search_term = request.GET.get('search', '')
        if search_term:
            friends = Friend.objects.filter(friend__username__icontains=search_term)
        else:
            friends = Friend.objects.filter(user=request.user)

        # Use a distinct set of friends
        distinct_friends = []
        seen_friends = set()

        for friend in friends:
            if friend.friend not in seen_friends:
                distinct_friends.append(friend)
                seen_friends.add(friend.friend)

        if request.is_ajax():
            html = render_to_string('feeds/friendslist_results.html', {'friends': distinct_friends})
            return JsonResponse({'html': html})

        context = {
            'friends': distinct_friends,
            'search_term': search_term,
        }
        return render(request, 'feeds/friendslist.html', context)


@login_required
def notifications(request):
    context = {}
    return render(request, 'feeds/notifications.html', context)


@login_required
def inbox(request):
    user = request.user
    rooms = DirectMessages.objects.filter(Q(receiver=user) | Q(sender=user))
    context = {
        'rooms': rooms
    }
    return render(request, 'feeds/inbox.html', context)


@login_required
def chat(request, label):
    user = request.user
    try:
        room = DirectMessages.objects.get(label=label)
    except DirectMessages.DoesNotExist:
        raise PermissionDenied("This chat room does not exist.")

    # Check if the user is either the sender or the receiver
    if room.sender != user and room.receiver != user:
        return redirect('feeds/chat.html')

    messages = reversed(room.messages.order_by('-timestamp')[:50])

    context = {
        'room': room,
        'messages': messages
    }
    return render(request, 'feeds/chat.html', context)


@csrf_exempt
def send(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        room_id = request.POST.get('room_id')
        page_name = request.POST.get('page_name')

        logger.debug(f"text: {text}, room_id: {room_id}, page_name: {page_name}")
        print(f"text: {text}, room_id: {room_id}, page_name: {page_name}")
        print('This is a community-sent message')

        try:
            room = Room.objects.get(id=room_id)
        except ObjectDoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Room does not exist.'})

        if not text:
            return JsonResponse({'status': 'error', 'message': 'Message is required.'})

        try:
            new_message = Message.objects.create(
                text=text,
                room=room,
                sender=request.user if request.user.is_authenticated else None
            )
            new_message.save()

            response_data = {
                'status': 'success',
                'message': 'Message sent successfully',
                'message_data': {
                    'text': new_message.text,
                    'user': new_message.sender.username if new_message.sender else 'Anonymous',
                    'room': new_message.room.name,
                    'file_url': new_message.file.url if new_message.file else None,
                }
            }

            return JsonResponse(response_data)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


class ChatView(ListView):
    model = Room
    template_name = "feeds/new_chat.html"  # Update the template name to match

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        signed_in_user = self.request.user
        context['communityin'] = Community.objects.filter(is_active=True, members=signed_in_user)
        if self.request.user.is_authenticated:
            context['theme'] = BackgroundTheme.objects.filter(is_active=1, user=signed_in_user)
            # Fetch user's friends
            context['Friends'] = Friend.objects.filter(user=self.request.user)

            current_user = self.request.user
            newprofile = UserProfile.objects.filter(is_active=1, user=current_user)
            context['Profiles'] = newprofile

            # Process profiles to add URLs and avatars
            for newprofile in context['Profiles']:
                user = newprofile.user
                profile = UserProfile.objects.filter(user=user).first()
                if profile:
                    newprofile.newprofile_profile_picture_url = profile.profile_pic.url
                    newprofile.newprofile_profile_url = newprofile.get_profile_url()

            # Fetch online profiles
            onlineprofile = Friend.objects.filter(is_active=1, user=current_user)
            context['OnlineProfiles'] = onlineprofile

            for onlineprofile in context['OnlineProfiles']:
                friend = onlineprofile.friend
                activeprofile = UserProfile.objects.filter(user=friend).first()
                if activeprofile:
                    onlineprofile.author_profile_picture_url = profile.profile_pic.url
                    onlineprofile.friend_profile_picture_url = activeprofile.profile_pic.url
                    onlineprofile.author_profile_url = onlineprofile.get_profile_url()
                    onlineprofile.friend_name = onlineprofile.friend.username
                    print('activeprofile exists')

            # Friends data with profiles
            friends = Friend.objects.filter(user=self.request.user)
            friends_data = []

            for friend in friends:
                profile = UserProfile.objects.filter(user=friend.friend).first()
                if profile:
                    friends_data.append({
                        'username': friend.friend.username,
                        'profile_picture_url': profile.profile_pic.url,
                        'profile_url': reverse('profile', args=[str(profile.pk)]),
                        'currently_active': friend.currently_active,
                        'user_profile_url': friend.get_profile_url2()
                    })

            context['friends_data'] = friends_data

            # Add the search functionality
            search_term = self.request.GET.get('search', '')
            if search_term:
                context = self.search_friends(context)

            # Add profiles (from the new_chat function)
            profiles = self.request.user.userprofile.following.all()
            context['profiles'] = profiles
        else:
            # Provide default empty lists for anonymous users
            context['Friends'] = []
            context['Profiles'] = []
            context['OnlineProfiles'] = []
            context['friends_data'] = []
            context['search_results'] = []
            context['profiles'] = []  # From new_chat logic

        return context

    def search_friends(self, context):
        search_term = self.request.GET.get('search', '')
        if search_term:
            item_list = Friend.objects.filter(
                Q(friend__username__icontains=search_term)
            ).prefetch_related('friend')

            search_results_data = []
            current_user = self.request.user

            for friend in item_list:
                profile = UserProfile.objects.filter(user=friend.friend).first()
                if profile:
                    search_results_data.append({
                        'username': friend.friend.username,
                        'profile_picture_url': profile.profile_pic.url if profile else None,
                        'profile_url': reverse('profile', args=[str(profile.pk)]),
                        'currently_active': friend.currently_active,
                    })
                    print('the friend does have a profile')
                else:
                    search_results_data.append({
                        'username': friend.friend.username,
                        'profile_picture_url': None,
                        'profile_url': reverse('profile', args=[str(friend.friend.pk)]),
                        'currently_active': friend.currently_active,
                    })
                    print('no profile on the friend')

            context['search_results'] = search_results_data
        else:
            context['search_results'] = []

        return context


@login_required
def new_chat_create(request, username):
    print(f"Username: {username}")  # For debugging purposes
    user_to_message = User.objects.get(username__iexact=username)
    room_label = request.user.username + '_' + user_to_message.username

    try:
        does_room_exist = DirectMessages.objects.get(label=room_label)
    except:
        room = DirectMessages(label=room_label, receiver=user_to_message,
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


from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist


# Profile Detail View


class ProfileView(DetailView):
    model = UserProfile
    template_name = 'feeds/profile.html'
    context_object_name = 'profile'

    def get_object(self):
        # Get the user by the username from the URL and return the corresponding profile
        user = get_object_or_404(User, username=self.kwargs['username'])
        return get_object_or_404(UserProfile, user=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_settings = self.request.user.settings
        context['username'] = self.request.user.username
        signed_in_user = self.request.user
        if signed_in_user.is_authenticated:
            context['Background'] = BackgroundTheme.objects.filter(is_active=1, user=signed_in_user)
            context['user_profile'] = UserProfile.objects.filter(user=signed_in_user).first()
        return context


# Profile Settings View
@method_decorator(login_required, name='dispatch')
class ProfileSettingsView(UpdateView):
    model = UserProfile
    form_class = ProfileEditForm
    template_name = 'feeds/profile_settings.html'
    context_object_name = 'userprofile'

    def get_object(self, queryset=None):
        user = get_object_or_404(User, username=self.kwargs['username'])
        if self.request.user != user:
            raise PermissionDenied  # Better than redirecting inside get_object
        return user.userprofile  # Assuming UserProfile is related to User

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        signed_in_user = self.request.user
        if signed_in_user.is_authenticated:
            context['Background'] = BackgroundTheme.objects.filter(is_active=1, user=signed_in_user)
            context['user_profile'] = UserProfile.objects.filter(user=signed_in_user).first()
        context['username'] = signed_in_user.username
        context['password'] = signed_in_user.password
        context['email'] = signed_in_user.email
        return context

    def form_valid(self, form):
        form.save()
        return redirect(reverse('profile', kwargs={'username': self.request.user.username}))


# Profile Settings Function View (if still needed)
@login_required
def profile_settings(request, username):
    user = get_object_or_404(User, username=username)
    if request.user != user:
        return redirect('index')

    if request.method == 'POST':
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
        signed_in_user = self.request.user

        context['username'] = self.request.user.username
        context['password'] = SettingsModel.password
        context['email'] = SettingsModel.email
        context['user_profile'] = UserProfile.objects.filter(user=signed_in_user).first()
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
            context['theme'] = BackgroundTheme.objects.filter(is_active=1, user=signed_in_user) #does currently_set need to be added?
            # Ensure you retrieve the correct UserProfile object for the signed-in user
            context['user_profile'] = UserProfile.objects.filter(user=signed_in_user).first()
        return context


from django.shortcuts import get_object_or_404


def set_current_theme(request, pk):
    # Check if the request is an AJAX request and if it's a POST method
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == 'POST':
        # Get the theme by ID and ensure it's for the current user
        theme = get_object_or_404(BackgroundTheme, pk=pk, user=request.user)

        # Set all other themes for the user to currently_set=False
        BackgroundTheme.objects.filter(user=request.user).update(currently_set=False)

        # Set the selected theme to currently_set=True
        theme.currently_set = True
        theme.save()

        # Return a JSON response indicating success
        return JsonResponse({'success': True, 'currently_set_theme_id': theme.id})

    return JsonResponse({'success': False}, status=400)


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


class PostsView(ListView):
    model = BackgroundTheme
    template_name = "feeds/post.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        signed_in_user = self.request.user

        # Handle user profile and theme
        if signed_in_user.is_authenticated:
            context['theme'] = BackgroundTheme.objects.filter(is_active=True, user=signed_in_user)
            context['user_profile'] = UserProfile.objects.filter(user=signed_in_user).first()

        # Add the post, liked functionality, and comment count
        post_id = self.kwargs.get('pk')  # Assuming 'pk' is passed in the URL
        if post_id:
            post = IGPost.objects.get(pk=post_id)
            try:
                like = Like.objects.get(post=post, user=signed_in_user)
                liked = 1
            except Like.DoesNotExist:
                liked = 0

            # Get comment count for the post
            comment_count = Comment.objects.filter(post=post).count()

            context['post'] = post
            context['liked'] = liked
            context['comment_count'] = comment_count

        return context


def get_comment_count(request, post_id):
    post = get_object_or_404(IGPost, pk=post_id)
    comment_count = Comment.objects.filter(post=post).count()
    return JsonResponse({'comment_count': comment_count})


def likes(request, pk):
    # likes = IGPost.objects.get(pk=pk).like_set.all()
    # profiles = [like.user.userprofile for like in likes]

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


class RoomView(TemplateView):
    model = Room
    template_name = 'feeds/room.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        room_name = self.kwargs['room']  # assuming 'room' is the room name passed in the URL
        rooms_with_logo_same_name = Room.objects.filter(name=room_name).exclude(logo='')
        context['rooms_with_logo_same_name'] = rooms_with_logo_same_name
        room = self.kwargs['room']

        signed_in_user = self.request.user
        username = self.request.GET.get('username')
        room_details = Room.objects.get(name=room)
        profile_details = UserProfile.objects.filter(user__username=username).first()
        context['Background'] = BackgroundTheme.objects.filter(is_active=1, user=signed_in_user)
        context['username'] = username
        context['room_details'] = room_details
        context['profile_details'] = profile_details

        # Assuming community name or identifier is passed in the URL, adjust accordingly
        community_name = self.kwargs.get('community_name')  # Assuming 'community_name' is passed in the URL
        if community_name:
            community = Community.objects.filter(name=community_name).first()
            context['community'] = community  # Pass the Community object to the template

        # Retrieve the author's profile avatar
        messages = Message.objects.all().order_by('-date')

        context['Messaging'] = messages

        for messages in context['Messaging']:
            profile = UserProfile.objects.filter(user=messages.signed_in_user).first()
            if profile:
                messages.user_profile_picture_url = profile.profile_pic.url
                messages.user_profile_url = messages.get_profile_url()

        current_user = self.request.user
        newprofile = UserProfile.objects.filter(is_active=1, user=current_user)

        context['Profiles'] = newprofile

        for newprofile in context['Profiles']:
            user = newprofile.user
            profile = UserProfile.objects.filter(user=user).first()
            if profile:
                newprofile.newprofile_profile_picture_url = profile.profile_pic.url
                newprofile.newprofile_profile_url = newprofile.get_profile_url()

        onlineprofile = Friend.objects.filter(is_active=1, user=current_user).order_by('-last_messaged')
        current_highlighted_profile = Friend.objects.filter(is_active=1, user=current_user)

        context['OnlineProfiles'] = onlineprofile
        context['CurrentProfiles'] = current_highlighted_profile

        for onlineprofile in context['OnlineProfiles']:
            friend = onlineprofile.friend
            activeprofile = UserProfile.objects.filter(user=friend).first()
            if activeprofile:
                onlineprofile.author_profile_picture_url = profile.profile_pic.url
                onlineprofile.author_profile_url = onlineprofile.get_profile_url()
                onlineprofile.friend_profile_picture_url = profile.profile_pic.url
                onlineprofile.friend_profile_picture_url = onlineprofile.get_profile_url()
                onlineprofile.friend_name = onlineprofile.friend.username
                print('activeprofile exists')

        for onlineprofile in context['CurrentProfiles']:
            friend = onlineprofile.friend
            activeprofile = UserProfile.objects.filter(user=friend).first()
            if activeprofile:
                onlineprofile.author_profile_picture_url = profile.profile_pic.url
                onlineprofile.friend_profile_picture_url = profile.profile_pic.url  # Add this line
                onlineprofile.author_profile_url = onlineprofile.get_profile_url()
                onlineprofile.friend_name = onlineprofile.friend.username
                print('currentfriendprofile exists')

        friends = Friend.objects.filter(user=self.request.user).order_by('last_messaged')

        # Prepare a list to hold the friends' data
        friends_data = []

        for friend in friends:
            # Get the friend's profile
            profile = UserProfile.objects.filter(user=friend.friend).first()
            friend_pk = self.request.GET.get('friend_pk')

            if profile:
                # Add the friend's data to the list
                friends_data.append({
                    'username': friend.friend.username,
                    'profile_picture_url': profile.profile_pic.url,
                    'profile_url': reverse('profile', args=[str(profile.pk)]),
                    'currently_active': friend.currently_active,
                    'user_profile_url': friend.get_profile_url2(),
                    'description': profile.description  # Add the description here
                })
            if friend_pk and int(friend_pk) == friend.pk:  # Check if PK matches
                print('setting currently active')
                friend.currently_active = True
                friend.save()  # Update the friend's currently_active field
                return redirect('room', room=room)  # Redirect back to the room URL

        # Add the friends' data to the context
        context['friends_data'] = friends_data

        search_term = self.request.GET.get('search', '')
        if search_term:
            context = self.search_friends(context)  # Call search_friends if search term exists

        return context

    def search_friends(self, context):
        search_term = self.request.GET.get('search', '')
        if search_term:
            item_list = Friend.objects.filter(
                Q(friend__username__icontains=search_term)
            ).prefetch_related('friend')  # Prefetch the friend object

            # Prepare a list to hold the searched friends' data
            search_results_data = []
            current_user = self.request.user

            for friend in item_list:

                profile = UserProfile.objects.filter(user=friend.friend).first()

                if profile:
                    search_results_data.append({
                        'username': friend.friend.username,
                        'profile_picture_url': profile.profile_pic.url if profile else None,
                        # Handle cases where profile might be missing
                        'profile_url': reverse('profile', args=[str(profile.pk)]),
                    })
                    print('the friend does have a profile')
                else:
                    # Handle cases where profile details might be missing (optional)
                    search_results_data.append({
                        'username': friend.friend.username,
                        'profile_picture_url': None,  # Set to None or a default image URL
                        'profile_url': reverse('profile', args=[str(friend.friend.pk)]),
                    })
                    print('no profile on the friend')

            context['search_results'] = search_results_data  # Update context with search results data
        else:
            context['search_results'] = []  # Empty list if no search

        return context


def room(request, room):
    username = request.GET.get('username')

    profile_details = UserProfile.objects.filter(user__username=username).first()

    return render(request, 'room.html', {
        'username': username,
        'room': room,
        'signed_in_user': signed_in_user,
        'room_details': room_details,
        'profile_details': profile_details,
    })


def checkview(request):
    room = request.POST['room_name']
    username = request.POST['username']

    request.session['room_name'] = room
    request.session['username'] = username

    # Check if room exists in the database
    if Room.objects.filter(name=room).exists():
        return redirect('/new_chat/' + room + '/?username=' + username)
    else:
        # Create room and assign user if authenticated
        new_room = Room.objects.create(name=room)
        signed_in_user = request.user
        print('the room owner is ' + str(signed_in_user))
        new_room.signed_in_user = signed_in_user if signed_in_user.is_authenticated else None
        new_room.save()
        # Redirect to create_room page after successful creation (assuming it exists)
        return redirect('create_community')  # Assuming you have a URL pattern named 'create_room'


@csrf_exempt
def send(request):
    if request.method == 'POST':
        message = request.POST.get('message')
        username = request.POST.get('username')
        room_id = request.POST.get('room_id')
        page_name = request.POST.get('page_name')

        if page_name == 'index.html':
            room_id = 'General'

        logger.debug(f"message: {message}, username: {username}, room_id: {room_id}, page_name: {page_name}")
        print(f"message: {message}, username: {username}, room_id: {room_id}, page_name: {page_name}")
        print('This is a community-sent message')

        try:
            room = Room.objects.get(name=room_id)
        except ObjectDoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Room does not exist.'})

        if not message:
            return JsonResponse({'status': 'error', 'message': 'Message is required.'})

        try:
            if request.user.is_authenticated:
                new_message = Message.objects.create(
                    value=message,
                    user=username,
                    room=room.name,
                    signed_in_user=request.user
                )
            else:
                new_message = Message.objects.create(
                    value=message,
                    user=username,
                    room=room.name
                )
            new_message.save()

            # Return only serializable data
            response_data = {
                'status': 'success',
                'message': 'Message sent successfully',
                'message_data': {
                    'value': new_message.value,
                    'user': new_message.user,
                    'room': new_message.room,
                    'file_url': new_message.file.url if new_message.file else None,
                    # You can include other fields that are JSON serializable
                }
            }

            return JsonResponse(response_data)
        except Exception as e:
            print(f"Error saving message: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})




from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import JsonResponse
from django.views import View
from django.core import serializers

"""
def get_profile_url(message):
   return f"http://127.0.0.1:8000/profile/{message.signed_in_user_id}/"
"""
from django.http import JsonResponse


class NewRoomSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "feeds/create_community.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room_name = self.request.session.get('room_name')
        username = self.request.session.get('username')

        room = Room.objects.filter(name=room_name).first()
        form = RoomSettings(instance=room)  # replace with your actual form class

        context['form'] = form
        context['room'] = room
        # add other context variables as needed

        return context

    def post(self, request, *args, **kwargs):
        room_name = self.request.session.get('room_name')
        username = self.request.session.get('username')
        room = Room.objects.filter(name=room_name).first()
        form = RoomSettings(request.POST, request.FILES, instance=room)  # replace with your actual form class

        if form.is_valid():
            form.save()
            return redirect(f'{reverse("room", kwargs={"room": room_name})}?username={username}')

        return render(request, self.template_name, {'form': form})


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages


def send_post_to_friend(request, post_id, room_name):
    post = get_object_or_404(IGPost, id=post_id)
    room = get_object_or_404(Room, name=room_name)

    if request.user in room.members.all() or room.public:
        room.shared_posts.add(post)  # Add the post to the room
        messages.success(request, f'Post "{post.title}" sent to {room.name}')
    else:
        messages.error(request, 'You are not allowed to send a post to this room.')

    return redirect('room', room_name=room.name)



def getMessages(request, room):
    try:
        room_details = Room.objects.get(name=room)
    except Room.DoesNotExist:
        return JsonResponse({'messages': []})

    # Convert shared_posts QuerySet into a list of dictionaries
    shared_posts = room_details.shared_posts.all().values('id', 'image', 'like', 'photo', 'reel','title',
                                                          'user_profile','user_profile_id', 'video', 'posted_on')
    messages = Message.objects.filter(room=room_details)
    messages_data = []
    for message in messages:
        profile_details = UserProfile.objects.filter(user=message.signed_in_user).first()
        if profile_details:
            user_profile_url = message.get_profile_url()
            avatar_url = profile_details.profile_pic.url
        else:
            user_profile_url = f'/new_chat/{room}/?username={request.user.username}'
            avatar_url = DefaultAvatar.objects.first()

        message_data = {
            'user_profile_url': user_profile_url,
            'avatar_url': avatar_url,
            'user': message.user,
            'value': message.value,
            'date': message.date.strftime("%Y-%m-%d %H:%M:%S"),
            'message_number': message.message_number,
            'file': message.file.url if message.file else None,
            'shared_posts': list(shared_posts),  # Convert shared_posts QuerySet to a list
        }
        messages_data.append(message_data)

    return JsonResponse({'messages': messages_data})


def getDirectMessages(request, room):
    # Fetch the room by label
    room_details = get_object_or_404(DirectMessages, label=room)

    # Fetch all messages for the room
    messages = DirectMessageText.objects.filter(room=room_details)

    # Construct the response data
    messages_data = []
    for message in messages:
        profile_details = UserProfile.objects.filter(user=message.sender).first()

        # Build user profile URL and avatar
        if profile_details:
            user_profile_url = message.get_profile_url()  # Assuming get_profile_url is a custom method
            avatar_url = profile_details.profile_pic.url if profile_details.profile_pic else None
        else:
            # Fallback for new chat or missing user profile
            user_profile_url = f'/new_chat/{room}/?username={message.sender.username}'
            avatar_url = DefaultAvatar.objects.first().url if DefaultAvatar.objects.exists() else None

        # Prepare message data
        message_data = {
            'user_profile_url': user_profile_url,
            'avatar_url': avatar_url,
            'user': message.sender.username,
            'value': message.text,
            'date': message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            'message_number': message.id,
            'file': message.file.url if message.file else None,  # Handle files if present
        }
        messages_data.append(message_data)

    return JsonResponse({'messages': messages_data})


def chat_view(request, room):
    try:
        room_details = DirectMessages.objects.get(label=room)
    except DirectMessages.DoesNotExist:
        room_details = None

    return render(request, 'chat.html', {'label': room})


# event_list/todo_app/views.py
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    UpdateView,
)

from .models import EventItem, EventList


class ListListView(ListView):
    model = EventList
    template_name = "todo_app/index.html"


class ItemListView(ListView):
    model = EventItem
    template_name = "todo_app/event_list.html"

    def get_queryset(self):
        return EventItem.objects.filter(event_list_id=self.kwargs["list_id"])

    def get_context_data(self):
        context = super().get_context_data()
        context["event_list"] = EventList.objects.get(id=self.kwargs["list_id"])
        return context


class ListCreate(CreateView):
    model = EventList
    fields = ["title"]

    def get_context_data(self):
        context = super().get_context_data()
        context["title"] = "Add a new list"
        return context


class ItemCreate(CreateView):
    model = EventItem
    fields = [
        "event_list",
        "title",
        "description",
        "due_date",
    ]

    def get_initial(self):
        initial_data = super().get_initial()
        event_list = EventList.objects.get(id=self.kwargs["list_id"])
        initial_data["event_list"] = event_list
        return initial_data

    def get_context_data(self):
        context = super().get_context_data()
        event_list = EventList.objects.get(id=self.kwargs["list_id"])
        context["event_list"] = event_list
        context["title"] = "Create a new item"
        return context

    def get_success_url(self):
        return reverse("list", args=[self.object.event_list_id])


class ItemUpdate(UpdateView):
    model = EventItem
    fields = [
        "event_list",
        "title",
        "description",
        "due_date",
    ]

    def get_context_data(self):
        context = super().get_context_data()
        context["event_list"] = self.object.event_list
        context["title"] = "Edit item"
        return context

    def get_success_url(self):
        return reverse("list", args=[self.object.event_list_id])


class ListDelete(DeleteView):
    model = EventList
    # You have to use reverse_lazy() instead of reverse(),
    # as the urls are not loaded when the file is imported.
    success_url = reverse_lazy("index")


class ItemDelete(DeleteView):
    model = EventItem

    def get_success_url(self):
        return reverse_lazy("list", args=[self.kwargs["list_id"]])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event_list"] = self.object.event_list
        return context


