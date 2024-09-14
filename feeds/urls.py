from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, PasswordResetCompleteView, \
    PasswordResetDoneView
from django.urls import path, re_path, include

from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.conf.urls.i18n import i18n_patterns

from . import views
from .views import FriendSearchResultsView

urlpatterns = [
    re_path(r'^i18n/', include('django.conf.urls.i18n')),
    re_path(r'^$', views.BackgroundView.as_view(), name='index'),
    re_path(r'^signup/$', views.signup, name='signup'),
    re_path(r'^login/$', views.login_user, name='login'),
    re_path(r'^signout/$', views.signout, name='signout'),
    re_path(r'^mythemes/$', views.background_theme_create, name='mythemes'),
    re_path(r'^create_community/$', views.CreateCommunityView.as_view(), name='create_community'),
    re_path(r'^mycommunities/$', views.MyCommunityView.as_view(), name='mycommunities'),
    re_path(r'^friendslist/$', views.FriendView.as_view(), name='friendslist'),
    re_path('friend-search/', FriendSearchResultsView.as_view(), name='friend-search'),
    re_path('friendslist/search/', views.FriendSearchResultsView.as_view(), name='friend_search'),
    re_path(r'^nav/$', TemplateView.as_view(template_name='nav.html'), name='nav'),
    re_path(r'^base/$', TemplateView.as_view(template_name='base.html'), name='base'),
    path('set-current-theme/<int:pk>/', views.set_current_theme, name='set-current-theme'),
    re_path(r'^themelist/$', views.BackgroundThemeListView.as_view(), name='themelist'),
    re_path(r'^signup_success/$', views.signup_success, name='signup_success'),
    re_path(r'^profile/(?P<username>[-_\w.]+)/$', views.ProfileView.as_view(), name='profile'),
    re_path(r'^profile/(?P<username>[-_\w.]+)/edit/$', views.ProfileSettingsView.as_view(), name='profile_settings'),
    re_path(r'^account_settings/$', views.SettingsView.as_view(), name='account_settings'),
    re_path(r'^profile/(?P<username>[-_\w.]+)/followers/$', views.followers, name='followers'),
    re_path(r'^profile/(?P<username>[-_\w.]+)/following/$', views.following, name='following'),
    re_path(r'^post/(?P<pk>\d+)/$', views.PostsView.as_view(), name='post'),
    path('post/<int:post_id>/comment_count/', views.get_comment_count, name='comment_count'),
    re_path(r'^post/$', views.post_picture, name='post_picture'),
    re_path(r'^explore/$', views.ExploreView.as_view(), name='explore'),
    re_path(r'^scrollexplore/$', views.ScrollExploreView.as_view(), name='scrollexplore'),
    re_path(r'^discover/$', views.DiscoverCommunityView.as_view(), name='discover'),
    re_path(r'^scrolldiscover/$', views.ScrollDiscoverView.as_view(), name='scrolldiscover'),
    re_path(r'^notifications/$', views.notifications, name='notifications'),
    re_path(r'^inbox/$', views.inbox, name='inbox'),
    re_path(r'^inbox/(?P<label>[-_\w.]+)/$', views.chat, name='chat'),
    re_path(r'^new_chat/$', views.new_chat, name='new_chat'),
    re_path(r'^new_chat/(?P<username>[-_\w.]+)/$', views.new_chat_create, name='new_chat_create'),
    re_path(r'^new_chat/checkview', views.checkview, name='checkview'),
    re_path(r'^new_chat/send', views.send, name='send'),
    re_path(r'^getMessages/<str:room>/', views.getMessages, name='getMessages'),
    #re_path(r'^send/', views.send, name='send-message'),
    re_path(r'^post/(?P<pk>\d+)/likes/$', views.likes, name='likes'),
    re_path(r'^like/$', views.add_like, name='like'),
    re_path(r'^comment/$', views.add_comment, name='comment'),
    re_path(r'^follow_toggle/$', views.follow_toggle, name='follow_toggle'),
    # re_path('accounts/change-password/', views.ChangePasswordView.as_view(), name="accounts/change-password"),
    re_path('reset_password/', PasswordResetView.as_view(), name='reset_password'),
    re_path('reset-password/done', PasswordResetDoneView.as_view(), name='password_reset_done'),
    re_path('reset_password/confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    re_path('reset-password/complete/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    # Forget Password
    re_path('password-reset/',
         auth_views.PasswordResetView.as_view(template_name='commons/password-reset/password_reset.html',
                                              subject_template_name='commons/password-reset/password_reset_subject.txt',
                                              email_template_name='commons/password-reset/password_reset_email.html',
                                              success_url='/login/'),
         name='password_reset'),
    re_path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='commons/password-reset/password_reset_done.html'),
         name='password_reset_done'),
    re_path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='commons/password-reset/password_reset_confirm.html'),
         name='password_reset_confirm'),
    re_path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='commons/password-reset/password_reset_complete.html'),
         name='password_reset_complete')
]