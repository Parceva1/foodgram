from django.db import models
from django.core.validators import MinValueValidator

from users.models import User

class Ingredient(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=100)

    class Meta:
        ordering = ('name', )

class Tag(models.Model):
    name = models.CharField(
        max_length=32,
        unique=True,
        verbose_name="Название тега"
    )
    slug = models.SlugField(
        max_length=32,
        unique=True,
        verbose_name="Slug тега"
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

class Recipe(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes', verbose_name='Автор')
    name = models.CharField(max_length=256, verbose_name='Название')
    text = models.TextField(verbose_name='Описание')
    ingredients = models.ManyToManyField(Ingredient, through='IngredientRecipe', related_name='recipes', verbose_name='Ингредиенты')
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    cooking_time = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)], verbose_name='Время приготовления')
    image = models.ImageField(upload_to='recipes/images/', verbose_name='Картинка')

class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shopping_cart')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='in_shopping_cart')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'], name='unique_shopping_cart')
        ]

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='favorited_by')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'], name='unique_favorite')
        ]

class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, verbose_name='Ингредиент')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, verbose_name='Рецепт')
    amount = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)], verbose_name='Количество')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['ingredient', 'recipe'], name='unique_recipe_ingredient')
        ]