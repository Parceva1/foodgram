from django.contrib import admin
from django.utils.html import format_html

from .models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                     ShoppingCart, Tag)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author_link', 'added_to_favorites_count')
    search_fields = ('author__username', 'author__email', 'name')
    list_filter = ('tags',)
    inlines = (IngredientRecipeInline,)
    readonly_fields = ('added_to_favorites_count',)

    def author_link(self, obj):
        url = f"/admin/users/user/{obj.author.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.author.username)
    author_link.short_description = 'Автор рецепта'

    def added_to_favorites_count(self, obj):
        return obj.favorited_by.count()
    added_to_favorites_count.short_description = 'Добавлено в избранное'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'user__email', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'user__email', 'recipe__name')
