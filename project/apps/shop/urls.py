from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.products, name='products'),
    path('product/<int:pk>/', views.product, name='product'),
    path("cart/", views.cart, name="cart"),
    path("cart/add/<int:product_id>/", views.to_cart, name="to_cart"),
    path("cart/remove/<int:item_id>/", views.from_cart, name="from_cart"),
    path('cart/toggle/<int:product_id>/', views.toggle_cart, name='toggle_cart'),
    path("cart/update/<int:item_id>/", views.update_cart_quantity, name="cart_quantity"),
    path("order/create/", views.create_order, name="create_order"),
    path("order/<int:order_id>/", views.order_detail, name="order_detail"),
]
