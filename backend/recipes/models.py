from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from users.models import User
from .recipes_constatnts import (MAX_COOKING_TIME, MAX_MEASUREMENT_UNIT_LENGTH,
                                 MAX_NAME_LENGTH, MAX_RECIPE_NAME_LENGTH,
                                 MAX_SLUG_LENGTH, MAX_TAG_NAME_LENGTH,
                                 MIN_COOKING_TIME, )


class Ingredient(models.Model):
    name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=MAX_MEASUREMENT_UNIT_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_TAG_NAME_LENGTH,
        unique=True,
        verbose_name='Название тега'
    )
    slug = models.SlugField(
        max_length=MAX_SLUG_LENGTH,
        unique=True,
        verbose_name='Slug тега'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return f'{self.name} ({self.slug})'


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=MAX_RECIPE_NAME_LENGTH,
        verbose_name='Название'
    )
    text = models.TextField(verbose_name='Описание')
    ingredients = models.ManyToManyField(
        Ingredient, through='IngredientRecipe',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_COOKING_TIME),
                    MaxValueValidator(MAX_COOKING_TIME)],
        verbose_name='Время приготовления'
    )
    image = models.ImageField(
        upload_to='recipes/image/',
        verbose_name='Картинка'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'{self.name}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='in_shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]
        verbose_name = 'Список покупок'

    def __str__(self):
        return f'{self.recipe}'


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Рецепт'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.recipe}'


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_COOKING_TIME),
                    MaxValueValidator(MAX_COOKING_TIME)],
        verbose_name='Количество'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.ingredient}'
