import os
from datetime import datetime, timedelta, timezone as dt_timezone

import bcrypt
import jwt
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import CookieJWTAuthentication
from .models import Todo, User
from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    TodoCreateSerializer,
    TodoSerializer,
    TodoUpdateSerializer,
)


def generate_token(payload: dict) -> str:
    exp = datetime.now(dt_timezone.utc) + timedelta(
        seconds=settings.JWT_EXPIRES_SECONDS
    )
    token = jwt.encode(
        {**payload, "exp": exp}, settings.JWT_SECRET_KEY, algorithm="HS256"
    )
    if isinstance(token, bytes):
        return token.decode("utf-8")
    return token


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = str(request.data.get("email", "")).strip()
        password = str(request.data.get("password", "")).strip()
        if not email or not password:
            return Response(
                {"error": "メールアドレスとパスワードを入力してください。"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            first_error = next(iter(serializer.errors.values()))[0]
            return Response(
                {"error": str(first_error)}, status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data["email"].strip()
        password = serializer.validated_data["password"].strip()

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "そのメールアドレスはすでに登録済みです。"},
                status=status.HTTP_409_CONFLICT,
            )

        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        User.objects.create(email=email, password=hashed.decode("utf-8"))

        return Response(
            {"message": "会員登録に成功しました。"}, status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "リクエストが不正です。"}, status=status.HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data["email"].strip()
        password = serializer.validated_data["password"].strip()

        user = User.objects.filter(email=email).first()
        if not user:
            return Response(
                {"error": "ユーザーが存在しません。"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
            return Response(
                {"error": "パスワードが間違っています。"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token = generate_token({"id": user.id, "email": user.email})

        response = Response(
            {"message": "ログインに成功しました。"}, status=status.HTTP_200_OK
        )
        is_production = os.getenv("NODE_ENV", "development") == "production"
        response.set_cookie(
            "authToken",
            token,
            httponly=True,
            secure=is_production,
            samesite="Strict" if is_production else "Lax",
            max_age=settings.JWT_EXPIRES_SECONDS,
        )
        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        response = Response(
            {"message": "ログアウトしました。"}, status=status.HTTP_200_OK
        )
        response.delete_cookie("authToken")
        return response


class CheckView(APIView):
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request):
        return Response({"message": "ログイン済みです。"}, status=status.HTTP_200_OK)


class TodoCollectionView(APIView):
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request):
        todos = Todo.objects.filter(user=request.user).order_by("-created_at")
        serializer = TodoSerializer(todos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = TodoCreateSerializer(data=request.data)
        if not serializer.is_valid():
            first_error = next(iter(serializer.errors.values()))[0]
            return Response(
                {"error": str(first_error)}, status=status.HTTP_400_BAD_REQUEST
            )

        Todo.objects.create(
            title=serializer.validated_data["title"],
            completed=False,
            user=request.user,
        )
        return Response(
            {"message": "ToDoを追加しました。"}, status=status.HTTP_201_CREATED
        )


class TodoDetailView(APIView):
    authentication_classes = [CookieJWTAuthentication]

    def put(self, request, todo_id: int):
        serializer = TodoUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            if "completed" in serializer.errors:
                return Response(
                    {"error": "リクエストが不正です。"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            first_error = next(iter(serializer.errors.values()))[0]
            return Response(
                {"error": str(first_error)}, status=status.HTTP_400_BAD_REQUEST
            )

        todo = Todo.objects.filter(id=todo_id, user=request.user).first()
        if not todo:
            return Response(
                {"error": "指定されたToDoが見つかりません。"},
                status=status.HTTP_404_NOT_FOUND,
            )

        todo.title = serializer.validated_data["title"]
        todo.completed = serializer.validated_data["completed"]
        todo.save(update_fields=["title", "completed"])

        return Response({"message": "ToDoを更新しました。"}, status=status.HTTP_200_OK)

    def delete(self, request, todo_id: int):
        todo = Todo.objects.filter(id=todo_id, user=request.user).first()
        if not todo:
            return Response(
                {"error": "指定されたToDoが見つかりません。"},
                status=status.HTTP_404_NOT_FOUND,
            )

        todo.delete()
        return Response({"message": "ToDoを削除しました。"}, status=status.HTTP_200_OK)
