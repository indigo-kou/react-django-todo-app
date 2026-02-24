from django.utils import timezone
from rest_framework import serializers

from .models import Todo


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_password(self, value: str) -> str:
        if len(value.strip()) < 8:
            raise serializers.ValidationError(
                "パスワードは8文字以上で入力してください。"
            )
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class TodoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = ["title"]

    def validate_title(self, value: str) -> str:
        title = value.strip()
        if not title:
            raise serializers.ValidationError("ToDoを入力してください。")
        if len(title) > 50:
            raise serializers.ValidationError("ToDoは50文字以内で入力してください。")
        return title


class TodoUpdateSerializer(serializers.Serializer):
    title = serializers.CharField()
    completed = serializers.BooleanField()

    def validate_title(self, value: str) -> str:
        title = value.strip()
        if not title:
            raise serializers.ValidationError("ToDoを入力してください。")
        if len(title) > 50:
            raise serializers.ValidationError("ToDoは50文字以内で入力してください。")
        return title


class TodoSerializer(serializers.ModelSerializer):
    createdAt = serializers.SerializerMethodField()

    class Meta:
        model = Todo
        fields = ["id", "title", "completed", "createdAt"]

    def get_createdAt(self, obj: Todo) -> str:
        return timezone.localtime(obj.created_at).isoformat()
