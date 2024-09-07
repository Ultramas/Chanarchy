from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, PasswordResetCompleteView, \
    PasswordResetDoneView
from django.urls import path, re_path, include

from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    re_path(r'^$', views.BackgroundView.as_view(), name='index'),
    re_path(r'^signup/$', views.signup, name='signup'),
    re_path(r'^login/$', views.login_user, name='login'),
    re_path(r'^signout/$', views.signout, name='signout'),
    re_path(r'^mythemes/$', views.background_theme_create, name='mythemes'),
    re_path(r'^themelist/$', views.BackgroundThemeListView.as_view(), name='themelist'),
    re_path(r'^signup_success/$', views.signup_success, name='signup_success'),
    re_path(r'^profile/(?P<username>[-_\w.]+)/$', views.profile, name='profile'),
    re_path(r'^profile/(?P<username>[-_\w.]+)/edit/$', views.profile_settings, name='profile_settings'),
    re_path(r'^account_settings/$', views.SettingsView.as_view(), name='account_settings'),
    re_path(r'^profile/(?P<username>[-_\w.]+)/followers/$', views.followers, name='followers'),
    re_path(r'^profile/(?P<username>[-_\w.]+)/following/$', views.following, name='following'),
    re_path(r'^post/(?P<pk>\d+)/$', views.post, name='post'),
    re_path(r'^post/$', views.post_picture, name='post_picture'),
    re_path(r'^explore/$', views.explore, name='explore'),
    re_path(r'^notifications/$', views.notifications, name='notifications'),
    re_path(r'^inbox/$', views.inbox, name='inbox'),
    re_path(r'^inbox/(?P<label>[-_\w.]+)/$', views.chat, name='chat'),
    re_path(r'^new_chat/$', views.new_chat, name='new_chat'),
    re_path(r'^new_chat/(?P<username>[-_\w.]+)/$', views.new_chat_create, name='new_chat_create'),
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
