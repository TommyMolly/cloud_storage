"""Views для работы с пользователями."""

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserSerializer

User = get_user_model()


class RegisterView(APIView):
    """Регистрация нового пользователя."""

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        email = request.data.get("email")
        full_name = request.data.get("full_name", "")

        if not username or not password or not email:
            return Response(
                {"error": "Необходимо заполнить все обязательные поля"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Проверка на уникальность
        if User.objects.filter(username=username).exists():
            return Response(
                {"username": ["Пользователь с таким логином уже существует."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"email": ["Пользователь с таким email уже существует."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            full_name=full_name,
        )

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email,
                "is_admin": user.is_admin,
                "storage_path": user.storage_path,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Аутентификация и получение JWT токенов."""

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "Необходимо указать логин и пароль"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(username=username).first()
        if user is None or not user.check_password(password):
            return Response(
                {"error": "Неверный логин или пароль"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {"refresh": str(refresh), "access": str(refresh.access_token)}, status=200
        )


class UserDeleteView(APIView):
    """Удаление пользователя (только для администраторов)."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id):
        if not request.user.is_admin:
            return Response(
                {"error": "Нет прав для удаления пользователей"},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = get_object_or_404(User, id=user_id)
        user.delete()
        return Response(
            {"status": f"Пользователь {user_id} удалён"},
            status=status.HTTP_204_NO_CONTENT,
        )


class UserListView(APIView):
    """Получение списка всех пользователей (только для администраторов)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_admin:
            return Response(
                {"error": "Нет прав для просмотра пользователей"},
                status=status.HTTP_403_FORBIDDEN,
            )

        users = User.objects.all()
        data = [
            {
                "id": u.id,
                "username": u.username,
                "full_name": u.full_name,
                "email": u.email,
                "is_admin": u.is_admin,
                "storage_path": u.storage_path,
            }
            for u in users
        ]
        return Response(data)


class ToggleAdminView(APIView):
    """Переключение статуса администратора пользователя (только для администраторов)."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, user_id):
        if not request.user.is_admin:
            return Response(
                {"error": "Нет прав для изменения статуса администратора"},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = get_object_or_404(User, id=user_id)
        user.is_admin = not user.is_admin
        user.save()
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
