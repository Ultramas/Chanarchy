from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User, BaseUserManager, AbstractBaseUser, PermissionsMixin

from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill

from datetime import datetime


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

    def __str__(self):
        return self.user.username


class SettingsModel(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='settings')
    username = models.CharField(help_text='Your username', max_length=200)
    password = models.CharField(help_text='Your password', max_length=200)
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
    image = ProcessedImageField(upload_to='posts',
                                #processors=[ResizeToFill(200,200)],
                                format='JPEG',
                                options={'quality': 100})
    reel = models.FileField(upload_to="posts", blank=True, null=True)
    photo = ProcessedImageField(upload_to='posts',
                                #processors=[ResizeToFill(200,200)],
                                format='JPEG',
                                options={'quality': 100})
    video = models.FileField(upload_to="posts", blank=True, null=True)
    posted_on = models.DateTimeField(default=datetime.now)

    def get_number_of_likes(self):
        return self.like_set.count()

    def get_number_of_comments(self):
        return self.comment_set.count()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Chanarchy Post"


class Comment(models.Model):
    post = models.ForeignKey('IGPost', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.CharField(max_length=100)
    posted_on = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return self.comment


class Like(models.Model):
    post = models.ForeignKey('IGPost', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("post", "user")

    def __str__(self):
        return 'Like: ' + self.user.username + ' ' + self.post.title


class Room(models.Model):
    label = models.SlugField(unique=True)
    receiver = models.ForeignKey(User, related_name="receiver", on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name="sender", on_delete=models.CASCADE)

    def get_last_message(self):
        message = Message.objects.filter(room=self).last()
        return message.text if message else ""

    def get_last_message_timestamp(self):
        message = Message.objects.filter(room=self).last()
        return message.timestamp if message else ""

    def __str__(self):
        return self.label


class Message(models.Model):
    room = models.ForeignKey(Room, related_name="messages", on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(default=datetime.now, db_index=True)

    def __str__(self):
        return self.text + " S:" + self.sender.username


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

from django.conf import settings
from django.contrib.auth.models import User
from notifications.models import Notification as BaseNotification


class Notification(BaseNotification):
    recipient_user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)
    message = models.TextField()  # Ensure this field exists

    class Meta:
        app_label = 'feeds'
        ordering = ['-timestamp']
