from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.models.signals import m2m_changed
from .models import UserProfile
from .models import Friend

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # Check if the User is newly created
    if created:
        # Create a new UserProfile associated with the new User
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Save the UserProfile whenever the User is saved
    instance.userprofile.save()

@receiver(m2m_changed, sender=UserProfile.following.through)
def handle_unfollow(sender, instance, action, reverse, pk_set, **kwargs):
    # Check if this is a post-remove action (i.e., unfollow)
    if action == "post_remove":
        # Instance is the UserProfile that did the unfollowing
        unfollowing_user_profile = instance
        for unfollowed_profile_id in pk_set:
            unfollowed_user_profile = UserProfile.objects.get(pk=unfollowed_profile_id)
            # Find the corresponding Friend instances and delete them
            Friend.objects.filter(user=unfollowing_user_profile.user, friend=unfollowed_user_profile.user).delete()
            Friend.objects.filter(user=unfollowed_user_profile.user, friend=unfollowing_user_profile.user).delete()