from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, CartItem, Category, Order, OrderItem, Review
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import F
from decimal import Decimal
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
from .forms import ProductForm, ReviewForm
from django.core.paginator import Paginator


def products(request):
    qs = Product.objects.select_related('category').all()
    category_slug = request.GET.get('category')
    search_query = request.GET.get('q', '').strip()
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    category = None
    if category_slug:
        category = Category.objects.filter(slug=category_slug).first()
        if category:
            qs = qs.filter(category=category)
    if search_query:
        qs = qs.filter(name__icontains=search_query)
    if price_min:
        try:
            qs = qs.filter(price__gte=float(price_min))
        except ValueError:
            pass
    if price_max:
        try:
            qs = qs.filter(price__lte=float(price_max))
        except ValueError:
            pass
    paginator = Paginator(qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'products': page_obj,
        'category': category,
        'categories': Category.objects.all(),
        'paginator': paginator,
        'page_obj': page_obj,
    }
    return render(request, 'shop/products.html', context)


def product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    reviews = product.reviews.select_related('user').all()
    in_cart = False
    can_review = False
    if request.user.is_authenticated:
        in_cart = CartItem.objects.filter(user=request.user, product=product).exists()
        has_ordered = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__status='delivered'
        ).exists()
        can_review = has_ordered
        if request.method == 'POST' and can_review:
            form = ReviewForm(request.POST)
            if form.is_valid():
                Review.objects.create(
                    user=request.user,
                    product=product,
                    text=form.cleaned_data['text'],
                    rating=form.cleaned_data['rating']
                )
                return redirect('shop:product', pk=pk)
        else:
            form = ReviewForm()
    else:
        form = None
    context = {
        'product': product,
        'reviews': reviews,
        'in_cart': in_cart,
        'can_review': can_review,
        'form': form,
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


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class ProductListView(ListView):
    model = Product
    template_name = 'shop/products.html'
    context_object_name = 'products'


class ProductDetailView(DetailView):
    model = Product
    template_name = 'shop/product.html'
    context_object_name = 'product'


class ProductCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'shop/product_form.html'
    success_url = reverse_lazy('shop:products')


class ProductUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'shop/product_form.html'
    success_url = reverse_lazy('shop:products')


class ProductDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Product
    template_name = 'shop/product_confirm_delete.html'
    success_url = reverse_lazy('shop:products')


@login_required
def order_list(request):
    if request.user.is_staff:
        orders = Order.objects.select_related('user').all().order_by('-created_at')
    else:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/orders.html', {'orders': orders})


@login_required
@require_POST
def change_order_status(request, order_id):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    order = get_object_or_404(Order, id=order_id)
    status = request.POST.get('status')
    if status not in dict(Order.STATUS_CHOICES):
        return JsonResponse({'error': 'Invalid status'}, status=400)
    order.status = status
    order.save()
    return JsonResponse({'success': True, 'status': order.get_status_display()})