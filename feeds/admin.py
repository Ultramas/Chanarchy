from django.contrib import admin
from .models import UserProfile, IGPost, Comment, Like, Message, Room, BackgroundTheme, BackgroundControl, Community, \
    Roles, Friend, EventItem, EventList

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(IGPost)
admin.site.register(Comment)
admin.site.register(Like)
admin.site.register(Message)
admin.site.register(Room)
admin.site.register(BackgroundTheme)
admin.site.register(BackgroundControl)
admin.site.register(Community)
admin.site.register(Friend)
admin.site.register(EventItem)
admin.site.register(EventList)


class RoleInLine(admin.TabularInline):
    model = Roles
    extra = 1