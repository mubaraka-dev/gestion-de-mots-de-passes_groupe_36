from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("verify-otp/", views.verify_otp_view, name="verify_otp"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("passwords/", views.password_list, name="password_list"),
    path("passwords/add/", views.password_create, name="password_add"),
    path("passwords/<int:pk>/", views.password_detail, name="password_detail"),
    path("passwords/<int:pk>/edit/", views.password_update, name="password_edit"),
    path("passwords/<int:pk>/delete/", views.password_delete, name="password_delete"),
    path("generator/", views.password_generator, name="password_generator"),
]
