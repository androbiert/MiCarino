# love_app/urls.py
from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/<int:user_id>/', views.view_profile, name='view_profile'),
    path('discussions/', views.discussion_list, name='discussion_list'),
    path('discussion/<int:discussion_id>/', views.discussion_detail, name='discussion_detail'),
    path('discussion/<int:discussion_id>/messages/', views.discussion_messages, name='discussion_messages'),
    path('discussion/start/<int:user_id>/', views.start_discussion, name='start_discussion'),
    path('search-users/', views.search_users, name='search_users'),
]