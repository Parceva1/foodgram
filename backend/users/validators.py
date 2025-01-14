import re
from django.core.exceptions import ValidationError


def validate_username(value):
    pattern = r'[\w.@+-]+\Z'
    if not re.match(pattern, value):
        raise ValidationError('Username can not be with such simbols.')
