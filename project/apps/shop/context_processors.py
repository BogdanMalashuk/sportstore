from .models import CartItem


def cart_count(request):
    """Добавляет количество товаров в корзине во все шаблоны."""
    if request.user.is_authenticated:
        count = CartItem.objects.filter(user=request.user).count()
    else:
        count = 0
    return {'cart_count': count}
