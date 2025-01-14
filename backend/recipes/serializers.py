import logging

from rest_framework import serializers
from api.serializers import UserSerializer

from .models import (Recipe, Tag, Ingredient,
                    ShoppingCart, Favorite, IngredientRecipe)
from api.serializers import Base64ImageField

logger = logging.getLogger(__name__)

class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def to_representation(self, instance):
        request = self.context.get('request')
        representation = super().to_representation(instance)
        representation['image'] = request.build_absolute_uri(instance.image.url)
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
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit', read_only=True)
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

class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True, write_only=True, required=True)
    ingredients = RecipeIngredientWriteSerializer(many=True, write_only=True)
    image = Base64ImageField(required=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    recipe_ingredients = IngredientInRecipeSerializer(many=True, read_only=True, source='ingredientrecipe_set')
    tags_representation = TagSerializer(many=True, read_only=True, source='tags') # Added for output

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'tags_representation', 'author', 'ingredients', 'is_favorited', 'recipe_ingredients',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = ['tags_representation'] # Ensure this is read-only

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

    def validate(self, data):
        ingredients = data.get('ingredients')  # Теперь ищем по 'ingredients'
        if not ingredients:
            raise serializers.ValidationError({'ingredients': 'Необходимо указать хотя бы один ингредиент.'})
        if len(set([item['id'] for item in ingredients])) != len(ingredients):
            raise serializers.ValidationError({'ingredients': 'Ингредиенты не должны повторяться.'})
        if not data.get('tags'):
            raise serializers.ValidationError({'tags': 'Необходимо указать хотя бы один тег.'})
        return data

    def create(self, validated_data):
        try:
            tags_data = validated_data.pop('tags')
            ingredients_data = validated_data.pop('ingredients')

            recipe = Recipe.objects.create(**validated_data)
            recipe.tags.set(tags_data)

            for ingredient_data in ingredients_data:
                ingredient = ingredient_data['id']
                IngredientRecipe.objects.create(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=ingredient_data['amount']
                )
            return recipe
        except Exception as e:
            logger.error(f"Ошибка при создании рецепта: {e}")
            raise
    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time', instance.cooking_time)
        if 'image' in validated_data:
            instance.image = validated_data['image']

        if tags_data:
            if len(set(tags_data)) != len(tags_data):
                raise serializers.ValidationError({'tags': 'Теги не должны повторяться.'})
            instance.tags.set(tags_data)
        elif not instance.tags.exists():  # Ensure tags are present during update
            raise serializers.ValidationError({'tags': 'Необходимо указать хотя бы один тег.'})

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

class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('id', 'recipe')

    def to_representation(self, instance):
        request = self.context.get('request')
        recipe = instance.recipe
        return {
            'id': recipe.id,
            'name': recipe.name,
            'image': request.build_absolute_uri(recipe.image.url),
            'cooking_time': recipe.cooking_time,
        }

class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('id', 'recipe')

    def to_representation(self, instance):
        request = self.context.get('request')
        return {
            'id': instance.recipe.id,
            'name': instance.recipe.name,
            'image': request.build_absolute_uri(instance.recipe.image.url),
            'cooking_time': instance.recipe.cooking_time,
        }

    def validate(self, data):
        user = self.context['request'].user
        recipe = data['recipe']
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError("Рецепт уже добавлен в избранное.")
        return data
