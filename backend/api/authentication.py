import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import APIException, AuthenticationFailed

from .models import User


class TokenExpired(APIException):
    status_code = 440
    default_detail = "認証トークンが有効期限切れです。"
    default_code = "token_expired"


class CookieJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.COOKIES.get("authToken")
        if not token:
            raise AuthenticationFailed("認証トークンがありません。")

        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError as exc:
            raise TokenExpired() from exc
        except jwt.InvalidTokenError as exc:
            raise AuthenticationFailed("認証トークンが無効です。") from exc

        user = User.objects.filter(
            id=payload.get("id"),
            email=payload.get("email"),
        ).first()
        if not user:
            raise AuthenticationFailed("認証トークンが無効です。")

        return (user, token)
