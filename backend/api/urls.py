from django.urls import path

from . import views

urlpatterns = [
    path("auth/register", views.RegisterView.as_view(), name="register"),
    path("auth/login", views.LoginView.as_view(), name="login"),
    path("auth/logout", views.LogoutView.as_view(), name="logout"),
    path("auth/check", views.CheckView.as_view(), name="check"),
    path("todos", views.TodoCollectionView.as_view(), name="todos_collection"),
    path("todos/<int:todo_id>", views.TodoDetailView.as_view(), name="todo_detail"),
]
