from django.contrib import admin
from .models import UserProfile, IGPost, Comment, Like, Message, Room, BackgroundTheme, BackgroundControl, Community, \
    Roles, Friend, EventItem, EventList, CallUser, Call, DirectMessageText

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
admin.site.register(DirectMessageText)


class CallUserAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Call Information', {
            'fields': ('user', 'call', 'status', 'is_active',)
        }),
    )


admin.site.register(CallUser, CallUserAdmin)


class CallAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Call Information', {
            'fields': ('channel_name', 'is_active',)
        }),
    )


admin.site.register(Call, CallAdmin)


class RoleInLine(admin.TabularInline):
    model = Roles
    extra = 1


class RoomInLine(admin.TabularInline):
    model = Room
    extra = 1