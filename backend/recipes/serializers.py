import logging

from rest_framework import serializers
from api.serializers import Base64ImageField, UserSerializer
from .models import (Favorite, Ingredient,
                     IngredientRecipe, Recipe, ShoppingCart, Tag)


logger = logging.getLogger(__name__)


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def to_representation(self, instance):
        request = self.context.get('request')
        representation = super().to_representation(instance)
        representation['image'] = request.build_absolute_uri(
            instance.image.url
        )
        return representation


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )
    id = serializers.IntegerField(source='ingredient.id')
    amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeInputSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    ingredients = RecipeIngredientWriteSerializer(many=True, write_only=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'ingredients',
                  'name', 'image', 'text', 'cooking_time')

    def validate(self, data):
        logger.debug(f"Начало валидации данных: {data}")
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Необходимо указать хотя бы один ингредиент.'}
            )
        if len(set([item['id'] for item in ingredients])) != len(ingredients):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться.'}
            )
        if not data.get('tags'):
            raise serializers.ValidationError(
                {'tags': 'Необходимо указать хотя бы один тег.'}
            )
        return data

    def create(self, validated_data):
        logger.debug(f"Создание рецепта: {validated_data}")
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        for ingredient_data in ingredients_data:
            IngredientRecipe.objects.create(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('ingredients', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if tags_data:
            instance.tags.set(tags_data)

        if ingredients_data:
            instance.ingredientrecipe_set.all().delete()
            for ingredient_data in ingredients_data:
                IngredientRecipe.objects.create(
                    recipe=instance,
                    ingredient=ingredient_data['id'],
                    amount=ingredient_data['amount']
                )

        instance.save()
        return instance


class RecipeOutputSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True, read_only=True, source='ingredientrecipe_set'
    )
    image = Base64ImageField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'ingredients',
            'author', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image',
            'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()
