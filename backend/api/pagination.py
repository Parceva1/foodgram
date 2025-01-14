from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size = 10  # Количество объектов по умолчанию
    page_size_query_param = 'limit'  # Параметр запроса для изменения размера страницы
    max_page_size = 100  # Максимальное количество объектов на странице
