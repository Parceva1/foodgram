from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.permissions import (IsAuthenticatedOrReadOnly,
                                        IsAuthenticated, AllowAny)
from rest_framework.viewsets import ReadOnlyModelViewSet
from django.http import HttpResponse

from .models import Recipe, ShoppingCart, Favorite, Ingredient, Tag
from .serializers import (IngredientSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          TagSerializer)
from api.permissions import IsAuthorOrReadOnly


class IngredientViewSet(ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    pagination_class = None
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer

    def get_queryset(self):
        """
        Фильтрует ингредиенты по началу имени, если передан параметр 'name'.
        """
        queryset = super().get_queryset()
        name_filter = self.request.query_params.get('name')
        if name_filter:
            queryset = queryset.filter(name__istartswith=name_filter)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related('tags')
        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')
        author = self.request.query_params.get('author')
        tags = self.request.query_params.getlist('tags')

        if self.request.user.is_authenticated:
            if is_favorited == '1':
                queryset = queryset.filter(
                    favorited_by__user=self.request.user
                )
            elif is_favorited == '0':
                queryset = queryset.exclude(
                    favorited_by__user=self.request.user
                )
            if is_in_shopping_cart == '1':
                queryset = queryset.filter(
                    in_shopping_cart__user=self.request.user
                )
            elif is_in_shopping_cart == '0':
                queryset = queryset.exclude(
                    in_shopping_cart__user=self.request.user
                )

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
                {'short-link': short_link},
                status=status.HTTP_200_OK
            )
        except Recipe.DoesNotExist:
            return Response(
                {'detail': 'Объект не найден'},
                status=status.HTTP_404_NOT_FOUND
            )


class ShoppingCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response(
                {'error': 'Рецепт не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if ShoppingCart.objects.filter(
            user=request.user, recipe=recipe
        ).exists():
            return Response(
                {'error': 'Рецепт уже добавлен в корзину.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ShoppingCartSerializer(
            data={'recipe': recipe.id},
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                {'id': recipe.id, 'name': recipe.name,
                 'image': request.build_absolute_uri(recipe.image.url),
                 'cooking_time': recipe.cooking_time},
                status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        recipe = Recipe.objects.get(pk=pk)
        user = request.user
        ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
        return Response(
            {'detail': 'Removed from shopping cart'},
            status=status.HTTP_204_NO_CONTENT
        )


class DownloadShoppingCartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart_items = ShoppingCart.objects.filter(
            user=request.user).select_related('recipe')

        if not cart_items.exists():
            return Response(
                {'error': 'Список покупок пуст.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ingredients = {}
        for item in cart_items:
            for recipe_ingredient in item.recipe.ingredientrecipe_set.all():
                ingredient_name = recipe_ingredient.ingredient.name
                measurement_unit = (
                    recipe_ingredient.ingredient.measurement_unit
                )
                amount = recipe_ingredient.amount
                if ingredient_name in ingredients:
                    ingredients[ingredient_name]['amount'] += amount
                else:
                    ingredients[ingredient_name] = {
                        'amount': amount,
                        'unit': measurement_unit
                    }

        shopping_list = "Список покупок:\n"
        for name, details in ingredients.items():
            shopping_list += (
                f"{name} - {details['amount']} {details['unit']}\n"
            )

        response = HttpResponse(
            shopping_list, content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response


class FavoriteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response(
                {'error': 'Рецепт не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {'error': 'Рецепт уже добавлен в избранное.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        Favorite.objects.create(user=request.user, recipe=recipe)
        return Response(
            {'id': recipe.id, 'name': recipe.name,
             'image': request.build_absolute_uri(recipe.image.url),
             'cooking_time': recipe.cooking_time},
            status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response(
                {'error': 'Рецепт не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )

        favorite = Favorite.objects.filter(
            user=request.user,
            recipe=recipe).first()
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
