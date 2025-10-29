from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, CartItem, Category, Order, OrderItem
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import F
from decimal import Decimal
from django.db import transaction


def products(request):
    qs = Product.objects.select_related('category').all()
    category_slug = request.GET.get('category')
    category = None
    if category_slug:
        category = Category.objects.filter(slug=category_slug).first()
        if category:
            qs = qs.filter(category=category)
    context = {
        'products': qs,
        'category': category,
        'categories': Category.objects.all(),
    }
    return render(request, 'shop/products.html', context)


def product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    reviews = product.reviews.select_related('user').all()

    in_cart = False
    if request.user.is_authenticated:
        in_cart = CartItem.objects.filter(user=request.user, product=product).exists()

    context = {
        'product': product,
        'reviews': reviews,
        'in_cart': in_cart,
    }
    return render(request, 'shop/product.html', context)


@login_required
def cart(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    cart_total = sum(item.get_total_price() for item in cart_items)
    return render(request, "shop/cart.html", {
        "cart_items": cart_items,
        "cart_total": cart_total,
    })


@login_required
def to_cart(request, product_id):
    if request.method == "POST":
        product = Product.objects.get(pk=product_id)
        cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        cart_item_count = CartItem.objects.filter(user=request.user).count()
        return JsonResponse({'cart_item_count': cart_item_count})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def from_cart(request, item_id):
    if request.method == "POST":
        item = get_object_or_404(CartItem, id=item_id, user=request.user)
        item.delete()
        cart_items = CartItem.objects.filter(user=request.user).select_related('product')
        total = sum((ci.get_total_price() for ci in cart_items), Decimal(0))
        cart_count = cart_items.count()
        cart_total_value = float(total)
        return JsonResponse({
            "cart_item_count": cart_count,
            "cart_total": cart_total_value,
            "item_id": item_id,
        })
    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def toggle_cart(request, product_id):
    if request.method == "POST":
        product = get_object_or_404(Product, pk=product_id)
        cart_item = CartItem.objects.filter(user=request.user, product=product).first()
        if cart_item:
            cart_item.delete()
            action = "removed"
        else:
            CartItem.objects.create(user=request.user, product=product, quantity=1)
            action = "added"
        cart_item_count = CartItem.objects.filter(user=request.user).count()
        return JsonResponse({'cart_item_count': cart_item_count, 'action': action})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
@require_POST
def update_cart_quantity(request, item_id):
    action = request.POST.get('action')
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    if action == "plus":
        item.quantity = F('quantity') + 1
        item.save(update_fields=['quantity'])
    elif action == "minus":
        if item.quantity > 1:
            item.quantity = F('quantity') - 1
            item.save(update_fields=['quantity'])
        else:
            item.delete()
            cart_items = CartItem.objects.filter(user=request.user).select_related('product')
            total = sum((ci.get_total_price() for ci in cart_items), Decimal(0))
            cart_count = cart_items.count()
            return JsonResponse({
                "deleted": True,
                "cart_item_count": cart_count,
                "cart_total": float(total),
                "item_id": item_id,
            })
    item.refresh_from_db()
    cart_items = CartItem.objects.filter(user=request.user).select_related('product')
    total = sum((ci.get_total_price() for ci in cart_items), Decimal(0))
    return JsonResponse({
        "deleted": False,
        "item_id": item.id,
        "quantity": item.quantity,
        "item_total": float(item.get_total_price()),
        "cart_total": float(total),
        "cart_item_count": cart_items.count(),
    })


@login_required
@transaction.atomic
def create_order(request):
    if request.method == "POST":
        selected_ids = request.POST.getlist("selected_items")
        if not selected_ids:
            return redirect("shop:cart")

        selected_items = CartItem.objects.filter(id__in=selected_ids, user=request.user).select_related('product')

        total_price = sum(item.get_total_price() for item in selected_items)

        order = Order.objects.create(
            user=request.user,
            total_price=total_price
        )

        for item in selected_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                buy_price=item.product.price
            )

        selected_items.delete()

        return redirect("shop:order_detail", order_id=order.id)

    return redirect("shop:cart")


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.items.select_related('product')
    return render(request, "shop/order.html", {
        "order": order,
        "items": items,
    })
