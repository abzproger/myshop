from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def order_history(request):
    """Страница истории заказов пользователя.

    Пока заказов нет — выводится заглушка.
    В будущем сюда можно подтянуть реальные модели заказов.
    """
    # Заглушка: список заказов пустой
    orders = []
    return render(request, 'orders/history.html', {'orders': orders})
