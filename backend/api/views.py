from django.http import HttpResponse
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from users.models import User
from api.pagination import CustomPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (IngredientSerializer, PasswordChangeSerializer,
                             RecipeInputSerializer, RecipeOutputSerializer,
                             SignUpSerializer, SubscriptionSerializer,
                             TagSerializer, TokenObtainSerializer,
                             UserAvatarSerializer, UserSerializer)


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
        if 'avatar' not in request.data:
            return Response(
                {'error': 'Avatar is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user = request.user
        serializer = UserAvatarSerializer(
            user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

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
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(
            serializer.validated_data['current_password']
        ):
            return Response(
                {'current_password': ['Incorrect password.']},
                status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


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


class IngredientViewSet(ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    pagination_class = None
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        name_filter = self.request.query_params.get('name')
        if name_filter:
            queryset = queryset.filter(name__istartswith=name_filter)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeOutputSerializer
        return RecipeInputSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        output_serializer = RecipeOutputSerializer(
            serializer.instance, context={'request': request}
        )
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        output_serializer = RecipeOutputSerializer(
            serializer.instance, context={'request': request}
        )
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        serializer.save()

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related(
            'tags').order_by('-id')
        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')
        author = self.request.query_params.get('author')
        tags = self.request.query_params.getlist('tags')

        if self.request.user.is_authenticated:
            if is_favorited == '1':
                queryset = queryset.filter(
                    favorited_by__user=self.request.user)
            elif is_favorited == '0':
                queryset = queryset.exclude(
                    favorited_by__user=self.request.user)
            if is_in_shopping_cart == '1':
                queryset = queryset.filter(
                    in_shopping_cart__user=self.request.user)
            elif is_in_shopping_cart == '0':
                queryset = queryset.exclude(
                    in_shopping_cart__user=self.request.user)

        if author:
            queryset = queryset.filter(author__id=author)
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()

        return queryset


class RecipeShortLinkView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            recipe = Recipe.objects.get(pk=pk)  # noqa: F841
            short_link = request.build_absolute_uri(f'/api/recipes/{pk}/')
            return Response(
                {'short-link': short_link}, status=status.HTTP_200_OK)
        except Recipe.DoesNotExist:
            return Response(
                {'detail': 'Объект не найден'},
                status=status.HTTP_404_NOT_FOUND)


class ShoppingCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response(
                {'error': 'Рецепт не найден.'},
                status=status.HTTP_404_NOT_FOUND)

        if ShoppingCart.objects.filter(
                user=request.user, recipe=recipe).exists():
            return Response(
                {'error': 'Рецепт уже добавлен в корзину.'},
                status=status.HTTP_400_BAD_REQUEST)

        ShoppingCart.objects.create(user=request.user, recipe=recipe)
        return Response(
            {'id': recipe.id, 'name': recipe.name,
             'image': request.build_absolute_uri(recipe.image.url),
             'cooking_time': recipe.cooking_time},
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, pk):
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response(
                {'error': 'Рецепт не найден.'},
                status=status.HTTP_404_NOT_FOUND)

        ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe).delete()
        return Response(
            {'detail': 'Removed from shopping cart'},
            status=status.HTTP_204_NO_CONTENT)


class DownloadShoppingCartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart_items = ShoppingCart.objects.filter(
            user=request.user).select_related('recipe')

        if not cart_items.exists():
            return Response(
                {'error': 'Список покупок пуст.'},
                status=status.HTTP_400_BAD_REQUEST)

        ingredients = {}
        for item in cart_items:
            for recipe_ingredient in item.recipe.ingredientrecipe_set.all():
                ingredient_name = recipe_ingredient.ingredient.name
                measurement_unit = (
                    recipe_ingredient.ingredient.measurement_unit)
                amount = recipe_ingredient.amount
                if ingredient_name in ingredients:
                    ingredients[ingredient_name]['amount'] += amount
                else:
                    ingredients[ingredient_name] = {
                        'amount': amount, 'unit': measurement_unit}

        shopping_list = "Список покупок:\n"
        for name, details in ingredients.items():
            shopping_list += (
                f"{name} - {details['amount']} {details['unit']}\n")

        response = HttpResponse(
            shopping_list, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"')
        return response


class FavoriteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response(
                {'error': 'Рецепт не найден.'},
                status=status.HTTP_404_NOT_FOUND)

        if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {'error': 'Рецепт уже добавлен в избранное.'},
                status=status.HTTP_400_BAD_REQUEST)

        Favorite.objects.create(user=request.user, recipe=recipe)
        return Response(
            {'id': recipe.id, 'name': recipe.name,
             'image': request.build_absolute_uri(recipe.image.url),
             'cooking_time': recipe.cooking_time},
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, pk):
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response(
                {'error': 'Рецепт не найден.'},
                status=status.HTTP_404_NOT_FOUND)

        favorite = Favorite.objects.filter(
            user=request.user, recipe=recipe).first()
        if favorite:
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Рецепт отсутствует в избранном.'},
            status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(ReadOnlyModelViewSet):
    pagination_class = None
    permission_classes = [AllowAny]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class SubscriptionView(ListAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return self.request.user.subscribed_users.all()


class SubscribeView(APIView):
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            author = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {'error': 'Пользователь не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SubscriptionSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        try:
            author = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {'error': 'Пользователь не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )

        subscription = request.user.subscribed_users.filter(
            author=author).first()
        if subscription:
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'error': 'Вы не подписаны на этого пользователя.'},
            status=status.HTTP_400_BAD_REQUEST
        )
