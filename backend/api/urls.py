from django.urls import include, path
from recipes.views import (DownloadShoppingCartView, FavoriteView,
                           IngredientViewSet, RecipeShortLinkView,
                           RecipeViewSet, ShoppingCartView, TagViewSet)
from rest_framework.routers import DefaultRouter
from users.views import SubscribeView, SubscriptionView

from .views import (CurrentUserView, CustomTokenObtainView, LogoutView,
                    PasswordChangeView, UserAvatarView, UserProfileView,
                    UserViewSet)

router = DefaultRouter()
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('auth/token/login/',
         CustomTokenObtainView.as_view(),
         name='token_obtain_pair'),
    path('auth/token/logout/', LogoutView.as_view(), name='logout'),

    path('users/me/', CurrentUserView.as_view(), name='current_user'),
    path('users/<int:id>/',
         UserProfileView.as_view(),
         name='user-profile-detail'),
    path('users/me/avatar/', UserAvatarView.as_view(), name='user-avatar'),
    path('users/set_password/',
         PasswordChangeView.as_view(),
         name='set-password'),
    path('users/subscriptions/',
         SubscriptionView.as_view(),
         name='subscriptions'),
    path('users/<int:pk>/subscribe/',
         SubscribeView.as_view(),
         name='subscribe'),
    path('recipes/<int:pk>/get-link/',
         RecipeShortLinkView.as_view(),
         name='recipe-short-link'),
    path('recipes/<int:pk>/shopping_cart/',
         ShoppingCartView.as_view(),
         name='shopping-cart'),
    path('recipes/download_shopping_cart/',
         DownloadShoppingCartView.as_view(),
         name='download-shopping-cart'),
    path('recipes/<int:pk>/favorite/',
         FavoriteView.as_view(),
         name='favorite'),

    path('', include(router.urls)),
]
