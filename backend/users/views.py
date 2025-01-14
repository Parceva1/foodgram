from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Subscription, User
from .serializers import SubscriptionSerializer

class SubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subscriptions = Subscription.objects.filter(user=request.user)
        serializer = SubscriptionSerializer(subscriptions, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            author = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)

        if request.user == author:
            return Response({'error': 'Нельзя подписаться на самого себя.'}, status=status.HTTP_400_BAD_REQUEST)

        if Subscription.objects.filter(user=request.user, author=author).exists():
            return Response({'error': 'Вы уже подписаны на этого пользователя.'}, status=status.HTTP_400_BAD_REQUEST)

        Subscription.objects.create(user=request.user, author=author)
        serializer = SubscriptionSerializer(
            Subscription.objects.get(user=request.user, author=author),
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        try:
            author = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)

        subscription = Subscription.objects.filter(user=request.user, author=author).first()
        if subscription:
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Вы не подписаны на этого пользователя.'}, status=status.HTTP_400_BAD_REQUEST)
