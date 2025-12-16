from django.urls import path
from .views import post_login_redirect

urlpatterns = [
    path("post-login/", post_login_redirect, name="post_login_redirect"),
]
