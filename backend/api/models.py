from django.db import models


class User(models.Model):
    email = models.EmailField(unique=True, max_length=255)
    password = models.CharField(max_length=255)

    class Meta:
        db_table = "users"


class Todo(models.Model):
    title = models.CharField(max_length=50)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="todos")

    class Meta:
        db_table = "todos"
