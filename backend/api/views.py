from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.generics import get_object_or_404
from rest_framework.authtoken.models import Token

from .pagination import CustomPagination
from users.models import User
from .serializers import (TokenObtainSerializer, SignUpSerializer,
                          UserSerializer, PasswordChangeSerializer,
                          UserAvatarSerializer)


class UserViewSet(viewsets.GenericViewSet,
                  mixins.ListModelMixin,
                  mixins.CreateModelMixin):
    queryset = User.objects.all()
    pagination_class = CustomPagination
    permission_classes_by_action = {
        'list': [AllowAny],
        'create': [AllowAny],
    }
    serializer_action_classes = {
        'list': UserSerializer,
        'create': SignUpSerializer,
    }

    def get_permissions(self):
        return [
            permission()
            for permission in self.permission_classes_by_action.get(
                self.action,
                [IsAuthenticated]
            )
        ]

    def get_serializer_class(self):
        return self.serializer_action_classes.get(self.action, UserSerializer)


class CustomTokenObtainView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenObtainSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get('user')

        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {'auth_token': token.key},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'Ошибка аутентификации'},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(APIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def get(self, request, id):
        user = get_object_or_404(User, id=id)
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)


class UserAvatarView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        avatar_data = request.data.get('avatar')
        if not avatar_data:
            return Response(
                {'error': 'Avatar is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        serializer = UserAvatarSerializer(
            user, data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = request.user
        if not user.avatar:
            return Response(
                {'error': 'No avatar to delete'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.avatar.delete()
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(
                serializer.validated_data['current_password']
            ):
                return Response(
                    {'current_password': ['Incorrect password.']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            Token.objects.get(user=request.user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Token.DoesNotExist:
            return Response(
                {'error': 'Token not found.'},
                status=status.HTTP_400_BAD_REQUEST
            )
