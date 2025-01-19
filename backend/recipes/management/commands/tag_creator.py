from recipes.models import Tag

Tag.objects.create(name='Завтрак', slug='zavtrak')
Tag.objects.create(name='Обед', slug='obed')
Tag.objects.create(name='Ужин', slug='uzhin')
Tag.objects.create(name='Вегетарианское', slug='vegetarianskoe')
