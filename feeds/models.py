import uuid
from datetime import datetime
from random import randint
from urllib.parse import urlencode

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User, BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.db.models import Q, Max
from django.urls import reverse
from django.utils import timezone
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.db.models.signals import post_save, post_delete, pre_delete
from notifications.models import Notification as BaseNotification


from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill

from datetime import datetime

DISCOVERY = (
    ('N', 'None'),
    ('B', 'Bronze'),
    ('S', 'Silver'),
    ('G', 'Gold'),
    ('P', 'Platinum'),
    ('C', 'Crystal'),
    ('S', 'Sapphire'),
    ('R', 'Ruby'),
    ('E', 'Emerald'),
    ('D', 'Diamond'),
)

LEVEL = (
    ('C', 'Common'),
    ('U', 'Uncommon'),
    ('R', 'Rare'),
    ('E', 'Epic'),
    ('M', 'Mythical'),
    ('T', 'Transcendent'),
    ('P', 'Primordial'),
    ('L', 'Legendary'),
    ('U', 'Ultimate'),
)


POSTTYPE = (
    ('I', 'Image'),
    ('V', 'Video'),
    ('P', 'Photo'),
    ('R', 'Reel'),
    ('L', 'Live'),
    ('S', 'Story'),
)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    followers = models.ManyToManyField('UserProfile',
                                       related_name="followers_profile",
                                       blank=True)
    following = models.ManyToManyField('UserProfile',
                                       related_name="following_profile",
                                       blank=True)
    profile_pic = ProcessedImageField(upload_to='profile_pics',
                                      format='JPEG',
                                      options={'quality': 100},
                                      null=True,
                                      blank=True, verbose_name="Profile Picture")

    description = models.CharField(max_length=200, null=True, blank=True)
    is_active = models.IntegerField(default=1,
                                    blank=True,
                                    null=True,
                                    help_text='1->Active, 0->Inactive',
                                    choices=((1, 'Active'), (0, 'Inactive')), verbose_name="Set active?")

    class Meta:
        verbose_name = "User Profile"

    def get_number_of_followers(self):
        print(self.followers.count())
        if self.followers.count():
            return self.followers.count()
        else:
            return 0

    def get_number_of_following(self):
        if self.following.count():
            return self.following.count()
        else:
            return 0

    def save(self, *args, **kwargs):
        # Check if the UserProfile does not have a profile_pic set
        if self.pk is None and not self.profile_pic:
            self.profile_pic = 'profile_placeholder.jpg'
        super(UserProfile, self).save(*args, **kwargs)

    def get_profile_url(self):
        profile = UserProfile.objects.filter(user=self.user).first()
        if profile:
            return reverse('profile', args=[str(profile.pk)])

    def __str__(self):
        return self.user.username


class SettingsModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='settings')
    username = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    email = models.EmailField(help_text='Your password', max_length=200, blank=True, null=True)
    is_active = models.IntegerField(default=1,
                                    blank=True,
                                    null=True,
                                    help_text='1->Active, 0->Inactive',
                                    choices=((1, 'Active'), (0, 'Inactive')), verbose_name="Set active?")

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "Setting"
        verbose_name_plural = "Settings"


class IGPost(models.Model):
    user_profile = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(choices=POSTTYPE, max_length=1)
    image = ProcessedImageField(upload_to='posts',
                                # processors=[ResizeToFill(200,200)],
                                format='JPEG',
                                options={'quality': 100})
    reel = models.FileField(upload_to="posts", blank=True, null=True)
    photo = ProcessedImageField(upload_to='posts',
                                # processors=[ResizeToFill(200,200)],
                                format='JPEG',
                                options={'quality': 100}, blank=True, null=True)
    video = models.FileField(upload_to="posts", blank=True, null=True)
    cover_photo = ProcessedImageField(upload_to='posts',
                                # processors=[ResizeToFill(200,200)],
                                format='JPEG',
                                options={'quality': 100})
    ide = models.CharField(max_length=100, blank=True, null=True)
    posted_on = models.DateTimeField(default=datetime.now)

    def get_number_of_likes(self):
        return self.like_set.count()

    def get_number_of_comments(self):
        return self.comment_set.count()

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.ide:
            self.ide = self.title + ''.join([str(randint(0, 9)) for _ in range(10)])

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Chanarchy Post"


class Comment(models.Model):
    post = models.ForeignKey('IGPost', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.CharField(max_length=400)
    posted_on = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return self.comment

    def get_number_of_likes(self):
        return self.like_set.count()

    def get_number_of_replies(self):
        return self.comment_set.count()


class Reply(models.Model):
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reply = models.CharField(max_length=200)
    posted_on = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return self.comment

    def get_number_of_likes(self):
        return self.like_set.count()

    def get_number_of_replies(self):
        return self.comment_set.count()


class Send(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="postsender")  # Sender
    friends = models.ManyToManyField(User, related_name="friendrecipients")  # Recipients
    ig_post = models.ForeignKey(IGPost, on_delete=models.CASCADE)  # IGPost to be sent
    sent_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} sent a post"


class Like(models.Model):
    post = models.ForeignKey('IGPost', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("post", "user")

    def __str__(self):
        return 'Like: ' + self.user.username + ' ' + self.post.title


class CommentLike(models.Model):
    post = models.ForeignKey('Comment', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("post", "user")

    def __str__(self):
        return 'Like: ' + self.user.username + ' ' + self.post.title


class DirectMessages(models.Model):
    label = models.SlugField(unique=True)
    receiver = models.ForeignKey(User, related_name="receiver", on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name="sender", on_delete=models.CASCADE)
    message_number = models.PositiveIntegerField(default=0, editable=False)
    file = models.FileField(upload_to='images/', null=True, blank=True)
    image_length = models.PositiveIntegerField(blank=True, null=True, default=100,
                                               help_text='Original length of the advertisement (use for original ratio).',
                                               verbose_name="image length")
    image_width = models.PositiveIntegerField(blank=True, null=True, default=100,
                                              help_text='Original width of the advertisement (use for original ratio).',
                                              verbose_name="image width")
    shared_posts = models.ManyToManyField(IGPost, blank=True)
    is_active = models.IntegerField(default=1, blank=True, null=True, help_text='1->Active, 0->Inactive',
                                    choices=((1, 'Active'), (0, 'Inactive')), verbose_name="Set active?")

    def get_last_message(self):
        message = DirectMessageText.objects.filter(room=self).last()
        return message.text if message else ""

    def get_last_message_timestamp(self):
        message = DirectMessageText.objects.filter(room=self).last()
        return message.timestamp if message else ""

    def get_profile_url(self):
        profile = UserProfile.objects.filter(user=self.sender).first()
        if profile:
            return reverse('profile', args=[str(profile.pk)])

    def get_profile_url2(self):
        profile = UserProfile.objects.filter(user=self.receiver).first()
        if profile:
            return reverse('profile', args=[str(profile.pk)])

    def __str__(self):
        return self.label


class DirectMessageText(models.Model):
    room = models.ForeignKey(DirectMessages, related_name='directmessagetext_set', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    date = models.DateTimeField(default=timezone.now, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.text}"


class Message(models.Model):
    value = models.CharField(max_length=1000000)
    date = models.DateTimeField(default=timezone.now, blank=True)
    user = models.CharField(max_length=1000000, verbose_name="Username")
    signed_in_user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='messages',
                                       verbose_name="User")
    room = models.CharField(max_length=1000000)
    message_number = models.PositiveIntegerField(default=0, editable=False)
    file = models.FileField(upload_to='images/', null=True, blank=True)
    image_length = models.PositiveIntegerField(blank=True, null=True, default=100,
                                               help_text='Original length of the advertisement (use for original ratio).',
                                               verbose_name="image length")
    image_width = models.PositiveIntegerField(blank=True, null=True, default=100,
                                              help_text='Original width of the advertisement (use for original ratio).',
                                              verbose_name="image width")
    is_active = models.IntegerField(default=1, blank=True, null=True, help_text='1->Active, 0->Inactive',
                                    choices=((1, 'Active'), (0, 'Inactive')), verbose_name="Set active?")

    def __str__(self):
        if self.value:
            return f"{self.value} in {self.room}"
        else:
            return f"blank message in {self.room}"

    def save(self, *args, **kwargs):
        if not self.pk:
            # Get the current maximum message number
            max_message_number = Message.objects.aggregate(max_message_number=Max('message_number'))[
                                     'max_message_number'] or 0
            # Increment the maximum message number to get the new message number
            self.message_number = max_message_number + 1

            # Get the associated UserProfile for the donor
            profile = UserProfile.objects.filter(user=self.signed_in_user).first()

            # Set the position to the position value from the associated UserProfile if it exists
            if profile and hasattr(self, 'position'):
                self.position = profile.position

        super().save(*args, **kwargs)

        # Update the Friend instances associated with the signed_in_user and friend fields
        if self.signed_in_user and self.room:
            # Get the Friend instances associated with the signed_in_user and friend fields
            friends = Friend.objects.filter(
                (Q(user=self.signed_in_user) & Q(friend__username=self.room)) |
                (Q(user__username=self.room) & Q(friend=self.signed_in_user))
            )

            # Update the Friend instances with the latest message and the date
            for friend in friends:
                friend.latest_messages = self
                friend.last_messaged = self.date
                friend.save(update_fields=['latest_messages', 'last_messaged'])

    def get_profile_url(self):
        profile = UserProfile.objects.filter(user=self.signed_in_user).first()
        if profile:
            return reverse('profile', args=[str(profile.pk)])

    def get_absolute_url(self):
        # Construct the URL for the room detail page
        room_url = reverse("room", kwargs={'room': str(self.room)})
        # Construct the query parameters
        final_url = f"{room_url}?username={self.signed_in_user.username}"
        return final_url


def get_friends(self):
    from .models import FriendRequest  # Import here to avoid circular import
    accepted_friend_requests = FriendRequest.objects.filter(
        Q(sender=self, status=FriendRequest.ACCEPTED) | Q(receiver=self, status=FriendRequest.ACCEPTED))
    friends = set()
    for friend_request in accepted_friend_requests:
        if friend_request.sender == self:
            friends.add(friend_request.receiver)
        else:
            friends.add(friend_request.sender)
    print('friends here')
    return friends


class FriendRequest(models.Model):
    PENDING = 0
    ACCEPTED = 1
    DECLINED = 2

    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (DECLINED, 'Declined'),
    )

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    status = models.IntegerField(choices=STATUS_CHOICES, default=PENDING)

    def __str__(self):
        return f'{self.sender.username} -> {self.receiver.username}: {self.get_status_display()}'

    def get_friend_profile_pic(self):
        return self.friend.userprofile.profile_pic.url if self.friend.userprofile.profile_pic else None

    def get_user_profile_pic(self):
        return self.user.userprofile.profile_pic.url if self.user.userprofile.profile_pic else None

    def get_profile_url(self, current_user):
        if current_user == self.sender or current_user == self.receiver:
            profile = UserProfile.objects.filter(user=current_user).first()
            if profile:
                return reverse('profile', args=[str(profile.pk)])

    # Handle the case where the current user is neither the sender nor the receiver

    class Meta:
        verbose_name = "Friend Request"
        verbose_name_plural = "Friend Requests"
        unique_together = ('sender', 'receiver')


User.add_to_class('get_friends', get_friends)


class Friend(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    friend = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friends')
    friend_username = models.CharField(max_length=500, blank=True, null=True)
    latest_messages = models.ForeignKey(Message, blank=True, null=True, on_delete=models.CASCADE)
    last_messaged = models.DateTimeField(blank=True, null=True)
    currently_active = models.BooleanField(default=False)  # are you currently on the person's chat profile
    created_at = models.DateTimeField(auto_now_add=True)
    online = models.BooleanField(default=False)
    is_active = models.IntegerField(default=1,
                                    blank=True,
                                    null=True,
                                    help_text='1->Active, 0->Inactive',
                                    choices=((1, 'Active'), (0, 'Inactive')), verbose_name="Set active?")

    def __str__(self):
        return str(self.user) + " is friends with " + str(self.friend) + "!"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Call the original save method first
        if self.currently_active:
            # Update the currently_active field for all instances with the same user field, except for this instance
            Friend.objects.exclude(pk=self.pk).filter(user=self.user).update(currently_active=False)
        self.friend_username = self.friend.username
        latest_message_queryset = Message.objects.filter(Q(signed_in_user=self.user) | Q(signed_in_user=self.friend))

        latest_message = latest_message_queryset.order_by('-date').first()
        if latest_message:
            self.latest_messages = latest_message
            self.last_messaged = latest_message.date
        super().save(*args, **kwargs)  # Save the model again with the updated field (optional)

    def get_profile_url(self):
        profile = UserProfile.objects.filter(user=self.user).first()
        if profile:
            return reverse('profile', args=[str(profile.pk)])

    def get_profile_url2(self):
        # If friend_username is None, return the base 'new_chat' URL
        if self.friend_username is None:
            return reverse("new_chat")

        # If friend_username exists, use it for the new_chat_create view
        room_url = reverse("new_chat_create", kwargs={'username': self.friend_username})

        # Construct the query parameters with the username
        final_url = f"{room_url}?username={self.user.username}"

        return final_url

    @receiver(post_save, sender=FriendRequest)
    def handle_friend_request(sender, instance, created, **kwargs):
        if instance.status == FriendRequest.ACCEPTED:
            Friend.objects.get_or_create(user=instance.sender, friend=instance.receiver)
        elif instance.status == FriendRequest.DECLINED:
            Friend.objects.filter(
                (Q(user=instance.sender) & Q(friend=instance.receiver)) |
                (Q(user=instance.receiver) & Q(friend=instance.sender))
            ).delete()

    post_save.connect(handle_friend_request, sender=FriendRequest)

    class Meta:
        unique_together = ('user', 'friend')


def update_friend_username(sender, instance, created, **kwargs):
    if created:  # Check if a new object is created
        instance.friend_username = instance.friend.username
        instance.save()  # Save the model again with the updated field


post_save.connect(update_friend_username, sender=Friend)


class Community(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Community Leader", blank=True)
    name = models.CharField(max_length=200)
    cover_image = models.ImageField()
    banner = models.ImageField(blank=True, null=True)
    description = models.CharField(max_length=800)
    label = models.SlugField(blank=True, null=True, unique=True)
    invite = models.CharField(blank=True, null=True, max_length=300)
    random_tackon = models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    members = models.ManyToManyField(User, related_name="community_members", blank=True)
    no_profanity = models.BooleanField(default=False)
    nsfw_inclusive = models.BooleanField(default=False)
    discovery_level = models.CharField(max_length=1, default='N')
    public = models.BooleanField(default=False)
    is_active = models.IntegerField(default=1,
                                    blank=True,
                                    null=True,
                                    help_text='1->Active, 0->Inactive',
                                    choices=((1, 'Active'), (0, 'Inactive')), verbose_name="Set active?")

    def save(self, *args, **kwargs):
        creating = not self.pk  # Check if this is a new community creation

        if not self.random_tackon:
            self.random_tackon = ''.join([str(randint(0, 9)) for _ in range(10)])

        if not self.label and self.user and self.name:
            self.label = f"{self.user.username}-{self.name}"

        super().save(*args, **kwargs)  # Save to generate a valid primary key

        # Automatically create or update the related Room
        if creating:
            room = Room.objects.create(
                name=self.name,
                signed_in_user=self.user,
                public=self.public,  # Match the community's public status
                logo=self.cover_image,  # Use community's cover image for room logo
            )
        else:
            # If the Community already exists, update the Room's name
            if self.room_set.exists():  # Check if related Room exists
                room = self.room_set.first()
                room.name = self.name  # Update Room name to match Community name
                room.save()
                print('room name is saved to ' + room.name)

        # Update invite link using the room URL
        room_url = reverse('room', kwargs={'room': room.name})
        self.invite = f"{room_url}/{self.random_tackon}"

        # Add the user as a member of the community
        if self.user:
            self.members.add(self.user)

        super().save(update_fields=['invite'])  # Save again only to update invite field

    def __str__(self):
        return f"{self.name} owned by {self.user}"

    def get_absolute_url(self):
        # Base URL for the 'new_chat' view with 'room' argument
        base_url = reverse('new_chat', kwargs={'room': self.name})

        # Build query string with the username
        query_string = urlencode({'username': self.user.username})

        # Combine base URL and query string
        return f"{base_url}?{query_string}"

    class Meta:
        unique_together = ("user", "name")
        verbose_name_plural = "Communities"


class Room(models.Model):
    name = models.CharField(max_length=1000, null=True, blank=True)
    signed_in_user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='room',
                                       verbose_name="Room Creator")
    community = models.ForeignKey(Community, on_delete=models.CASCADE, verbose_name="Community", blank=True, null=True)
    members = models.ManyToManyField(User, blank=True, related_name="members")
    time = models.DateTimeField(default=timezone.now, blank=True)
    public = models.BooleanField(default=False, verbose_name="Make Public?")
    logo = models.FileField(blank=True, null=True, verbose_name="Logo")
    shared_posts = models.ManyToManyField(IGPost, blank=True, related_name='rooms_shared_with')
    invite_code = models.CharField(max_length=100, blank=True, null=True, unique=True)  # Store invite codes
    welcome_note = models.CharField(max_length=100, blank=True, null=True)  # Store invite codes
    is_active = models.IntegerField(default=1,
                                    blank=True,
                                    null=True,
                                    help_text='1->Active, 0->Inactive',
                                    choices=((1, 'Active'), (0, 'Inactive')), verbose_name="Set active?")

    def __str__(self):
        if self.name:
            return str(self.name)
        else:
            return str('Guest')

    def add_member(self, user):
        if user not in self.members.all():
            self.members.add(user)
            return True
        return False

    def generate_invite_code(self):
        """Generate a unique invite code for this room."""
        self.invite_code = ''.join([str(randint(0, 9)) for _ in range(10)])
        self.save()

    def check_user_access(self, user, invite_code=None):
        """
        Check if a user can access the room.
        If they are not a member, they must have a valid invite code to join.
        """
        if self.public:
            print('public server')
            return True

        print('private server')
        # Check if the user is already a member
        if user in self.members.all():
            return True

        # Check if an invite code is provided and valid
        if invite_code and invite_code == self.invite_code:
            # Add the user to members and allow access
            self.members.add(user)
            return True

        # Deny access if no invite code or incorrect code
        return False

    def get_room_url(self):
        """Return the normal room URL, handle case where room name is blank."""
        if not self.name:
            return reverse("room", kwargs={'room': 'guest'})  # or handle as needed
        return reverse("room", kwargs={'room': self.name})

    def get_absolute_url(self):
        # Check if the room has a valid name
        if not self.name:
            return reverse("room", kwargs={'room': ''})

        # Use signed_in_user (assumed to be the creator) for the username
        room_url = reverse('room', kwargs={'username': self.signed_in_user.username, 'room': self.name})

        # Construct the query parameters with the room name
        final_url = f"{room_url}?username={self.name}"

        return final_url


# Receiver function for following relationship
@receiver(m2m_changed, sender=UserProfile.following.through)
def create_friend_instance(sender, instance, action, reverse, pk_set, **kwargs):
    """
    This function will trigger when the following relationship changes (i.e., when someone follows/unfollows).
    """
    if action == 'post_add':  # Check if a new following relationship is created
        for followed_profile_pk in pk_set:
            followed_profile = UserProfile.objects.get(pk=followed_profile_pk)

            # Check if the followed user is also following the current user
            if instance in followed_profile.following.all():
                # Create Friend instance for both users if not already friends
                Friend.objects.get_or_create(user=instance.user, friend=followed_profile.user)
                Friend.objects.get_or_create(user=followed_profile.user, friend=instance.user)


class Achievements(models.Model):
    name = models.CharField(max_length=250)

    posted_on = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return self.comment


class Roles(models.Model):
    role = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=7, default='#FF0000')  # Store hex code in CharField
    icon = models.ImageField(blank=True, null=True)

    def __str__(self):
        if self.description:
            return self.role + " " + str(self.description) + " " + str(self.color)
        else:
            return self.role + " " + str(self.color)

    class Meta:
        verbose_name = "Role"


class Rules(models.Model):
    rule = models.CharField(max_length=400)
    description = models.TextField(blank=True, null=True)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)

    def __str__(self):
        return self.rule + " " + str(self.description) + " " + str(self.community)

    class Meta:
        verbose_name = "Rule"


class CommunityBanList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rule_broken = models.ForeignKey(Rules, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    ban_time = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return self.user + " broke " + str(str.rule_broken)

    class Meta:
        verbose_name = "Community Banlist"


class CommunityBanListAppeal(models.Model):
    name = models.CharField(max_length=100)
    Rule_broken = models.CharField(max_length=200,
                                   help_text='Tell us the numbers of the rule(s) you broke. Refer to our rules page to see the rules and their corresponding numbers.')
    Why_I_should_have_my_ban_revoked = models.TextField(
        help_text='Tell us why we should unban you, and tell us you can do to fix your mistake. If you think your punishment is a mistake, tell us why.',
        verbose_name="Why I should have my ban revoked.")
    Additional_comments = models.TextField(
        help_text='Put any additional evidence or comments you may have here.')
    is_active = models.IntegerField(default=1,
                                    blank=True,
                                    null=True,
                                    help_text='1->Active, 0->Inactive',
                                    choices=((1, 'Active'), (0, 'Inactive')), verbose_name="Set active?")

    def __str__(self):
        return self.Why_I_should_have_my_ban_revoked + " submitted by " + str(self.name)

    class Meta:
        verbose_name = "Community Ban Appeal"


class BackgroundTheme(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    backgroundtitle = models.TextField(verbose_name="Background Title", blank=True, null=True)
    cover = models.ImageField(blank=True, null=True, upload_to='images/', verbose_name="Images")
    image_width = models.PositiveIntegerField(blank=True, null=True, default=100,
                                              help_text='Width of the image (in percent relative).',
                                              verbose_name="image width")
    image_length = models.PositiveIntegerField(blank=True, null=True, default=100,
                                               help_text='Length of the image (in percent relative).',
                                               verbose_name="image length")
    file = models.FileField(blank=True, null=True, upload_to='images/', verbose_name="Non-image File")
    alternate = models.TextField(verbose_name="Alternate Text", blank=True, null=True)
    currently_set = models.BooleanField(default=True)
    position = models.IntegerField(verbose_name="Image Position", blank=True, null=True)
    default_set = models.BooleanField(default=False)
    is_active = models.IntegerField(default=1,
                                    blank=True,
                                    null=True,
                                    help_text='1->Active, 0->Inactive',
                                    choices=((1, 'Active'), (0, 'Inactive')), verbose_name="Set active?")

    def __str__(self):
        return self.backgroundtitle

    class Meta:
        verbose_name = "Background Theme"

    def save(self, *args, **kwargs):
        # Validation logic: Ensure either cover or file, but not both, are provided
        if not self.cover and self.file:
            raise ValidationError("Cannot save: You must provide a cover image if a file is present.")
        if self.cover and self.file:
            raise ValidationError("Cannot save: You cannot have both a cover image and a file.")

        # Set user if provided via kwargs
        user = kwargs.pop('user', None)  # Get the 'user' argument if passed
        if not self.user and user:
            self.user = user  # Set the user field to the current user

        # Ensure only one instance has 'currently_set' as True for a given user
        if self.currently_set:
            # If this instance is set to True, set others to False
            BackgroundTheme.objects.filter(user=self.user, currently_set=True).exclude(pk=self.pk).update(
                currently_set=False)

        # Set alternate text if not provided
        if self.cover and not self.alternate:  # Set alternate text if missing
            self.alternate = str(self.cover)
        elif self.file and not self.alternate:
            self.alternate = str(self.file)

        # Call the parent save method
        super().save(*args, **kwargs)


class BackgroundControl(models.Model):
    backgroundtitle = models.TextField(verbose_name="Background Title", blank=True, null=True)
    cover = models.ImageField(blank=True, null=True, upload_to='images/', verbose_name="Images")
    image_width = models.PositiveIntegerField(blank=True, null=True, default=100,
                                              help_text='Width of the image (in percent relative).',
                                              verbose_name="image width")
    image_length = models.PositiveIntegerField(blank=True, null=True, default=100,
                                               help_text='Length of the image (in percent relative).',
                                               verbose_name="image length")
    file = models.FileField(blank=True, null=True, upload_to='images/', verbose_name="Non-image File")
    alternate = models.TextField(verbose_name="Alternate Text", blank=True, null=True)
    page = models.TextField(verbose_name="Page Name")
    url = models.CharField(verbose_name="Page URL", max_length=250, blank=True, null=True)
    position = models.IntegerField(verbose_name="Image Position", blank=True, null=True)
    is_active = models.IntegerField(default=1,
                                    blank=True,
                                    null=True,
                                    help_text='1->Active, 0->Inactive',
                                    choices=((1, 'Active'), (0, 'Inactive')), verbose_name="Set active?")

    def __str__(self):
        return self.backgroundtitle

    class Meta:
        verbose_name = "Background Control"

    def save(self, *args, **kwargs):
        if not self.url and self.page == "index":
            self.url = 'http://127.0.0.1:8000/'
        elif not self.url and self.page == "login":
            self.url = 'http://127.0.0.1:8000/accounts/login'
        elif not self.url:
            self.url = f'http://127.0.0.1:8000/{self.page}'
        elif not self.url.startswith('http://127.0.0.1:8000/'):
            self.url = f'http://127.0.0.1:8000/{self.url}'
        if not self.page.endswith('.html'):
            self.page += '.html'
        # Prevent saving if the conditions are met
        if not self.cover and self.file:
            raise ValidationError("Cannot save: You must provide a cover image if a file is present.")
        if self.cover and self.file:
            raise ValidationError("Cannot save: You cannot have both a cover image and a file.")

        if not self.pk:  # Check if this is a new object
            self.position = BackgroundControl.objects.filter(page=self.page).count() + 1
        super().save(*args, **kwargs)

        # Set alternate text based on the cover or file
        if self.cover and not self.alternate:  # Set alternate text if missing
            self.alternate = str(self.cover)
        elif self.file and not self.alternate:
            self.alternate = str(self.file)

        # Call the parent save method
        super().save(*args, **kwargs)


class NotificationType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Notification(BaseNotification):
    recipient_user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)
    message = models.TextField()  # Ensure this field exists

    class Meta:
        app_label = 'feeds'
        ordering = ['-timestamp']


class DefaultAvatar(models.Model):
    default_avatar_name = models.CharField(max_length=300, blank=True, null=True)
    default_avatar = models.ImageField(upload_to='images/')
    is_active = models.IntegerField(default=1,
                                    blank=True,
                                    null=True,
                                    help_text='1->Active, 0->Inactive',
                                    choices=((1, 'Active'), (0, 'Inactive')), verbose_name="Set active?")

    def __str__(self):
        if self.default_avatar_name:
            return str(self.default_avatar_name)

    def save(self, *args, **kwargs):
        if not self.default_avatar_name and self.default_avatar:
            self.default_avatar_name = self.default_avatar.name
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Default Avatar"
        verbose_name_plural = "Default Avatars"


def one_week_hence():
    return timezone.now() + timezone.timedelta(days=7)


class EventType(models.Model):
    eventtype = models.CharField(max_length=200)

    def __str__(self):
        return 'Event Type - ' + self.eventtype

    class Meta:
        verbose_name = "Event Type"
        verbose_name_plural = "Event Types"


class EventList(models.Model):
    title = models.CharField(max_length=100, unique=True)

    def get_absolute_url(self):
        return reverse("list", args=[self.id])

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Event List"
        verbose_name_plural = "Event Lists"


class EventItem(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(default=one_week_hence)
    todo_list = models.ForeignKey(EventList, on_delete=models.CASCADE)
    type = models.ForeignKey(EventType, on_delete=models.CASCADE)
    is_active = models.IntegerField(default=1,
                                    blank=True,
                                    null=True,
                                    help_text='1->Active, 0->Inactive',
                                    choices=((1, 'Active'), (0, 'Inactive')), verbose_name="Set active?")


    def get_absolute_url(self):
        return reverse(
            "item-update", args=[str(self.todo_list.id), str(self.id)]
        )

    def __str__(self):
        return f"{self.title}: due {self.due_date}"

    class Meta:
        ordering = ["due_date"]
        verbose_name = "Event Item"
        verbose_name_plural = "Event Items"


class Call(models.Model):
    channel_name = models.CharField(max_length=255)
    is_active = models.IntegerField(default=1,
                                    blank=True,
                                    null=True,
                                    help_text='1->Active, 0->Inactive',
                                    choices=((1, 'Active'), (0, 'Inactive')), verbose_name="Set active?")

    def __str__(self):
        return self.channel_name


class CallUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    call = models.ForeignKey(Call, on_delete=models.CASCADE, null=True)
    STATUS_CHOICES = [
        ('ONLINE', 'Online'),
        ('OFFLINE', 'Offline'),
    ]
    status = models.CharField(max_length=7, choices=STATUS_CHOICES, default='OFFLINE')
    flavor_text = models.CharField(max_length=1000, blank=True, null=True)
    is_active = models.IntegerField(default=1,
                                    blank=True,
                                    null=True,
                                    help_text='1->Active, 0->Inactive',
                                    choices=((1, 'Active'), (0, 'Inactive')))

    def __str__(self):
        return self.user + " " + self.call

    class Meta:
        verbose_name = "Call User"


class RoomMember(models.Model):
    name = models.CharField(max_length=200)
    uid = models.CharField(max_length=1000)
    room_name = models.CharField(max_length=200)
    insession = models.BooleanField(default=True)

    def __str__(self):
        return self.name