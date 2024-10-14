from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from imagekit.forms import ProcessedImageField

from .models import IGPost, UserProfile, Comment, Like, SettingsModel, Community, BackgroundTheme, Room


class UserCreateForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(UserCreateForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class PostPictureForm(ModelForm):
    class Meta:
        model = IGPost
        fields = ['title', 'image', 'reel', 'photo', 'description']


class ProfileEditForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_pic', 'description']


class SettingsForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Your Username'}))
    password = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Your Password'}))
    email = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Your Email'}))

    class Meta:
        model = SettingsModel
        fields = ('username', 'password', 'email')

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.user = self.instance.user
        if commit:
            instance.save()
        return instance


class RoomSettings(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['public', 'logo']


class CreateCommunityForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'readonly': 'readonly'}))  # Make name field read-only
    cover_image = forms.ImageField()
    banner = forms.ImageField(required=False)
    description = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Describe Your Community!'}))
    public = forms.BooleanField(required=False)
    no_profanity = forms.BooleanField(required=False)
    nsfw_inclusive = forms.BooleanField(required=False)

    class Meta:
        model = Community
        fields = ('name', 'cover_image', 'description', 'public', 'no_profanity', 'nsfw_inclusive')

    def save(self, commit=True):
        if not self.instance.pk:
            self.instance.user = self.initial.get('user')  # Get the user from initial data

        # Check if an instance with the same user and name exists
        existing_instance = Community.objects.filter(user=self.instance.user, name=self.cleaned_data['name']).first()

        if existing_instance:
            # If an existing instance is found, update it
            instance = existing_instance
            instance.cover_image = self.cleaned_data.get('cover_image', instance.cover_image)
            instance.description = self.cleaned_data.get('description', instance.description)
            instance.public = self.cleaned_data.get('public', instance.public)
            instance.no_profanity = self.cleaned_data.get('no_profanity', instance.no_profanity)
            instance.nsfw_inclusive = self.cleaned_data.get('nsfw_inclusive', instance.nsfw_inclusive)
        else:
            # If no existing instance, create a new one
            instance = super().save(commit=False)
            instance.user = self.instance.user  # Ensure user is assigned

        if commit:
            instance.save()
        return instance


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['comment']


class BackgroundThemeForm(forms.ModelForm):
    class Meta:
        model = BackgroundTheme
        fields = [
            'backgroundtitle',
            'cover',
            'file',
        ]
        # Optional: You can add custom widgets, labels, or help texts here.
        widgets = {
            'backgroundtitle': forms.TextInput(attrs={'class': 'form-control'}),
            'cover': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'image_width': forms.NumberInput(attrs={'class': 'form-control'}),
            'image_length': forms.NumberInput(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'alternate': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control'}),
            'position': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.Select(attrs={'class': 'form-select'}),
        }
