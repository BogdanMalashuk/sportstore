from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.products, name='products'),
    path('product/<int:pk>/', views.product, name='product'),
    path('products/add/', views.ProductCreateView.as_view(), name='product_add'),
    path('products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),

    path("cart/", views.cart, name="cart"),
    path("cart/add/<int:product_id>/", views.to_cart, name="to_cart"),
    path("cart/remove/<int:item_id>/", views.from_cart, name="from_cart"),
    path('cart/toggle/<int:product_id>/', views.toggle_cart, name='toggle_cart'),
    path("cart/update/<int:item_id>/", views.update_cart_quantity, name="cart_quantity"),

    path("order/create/", views.create_order, name="create_order"),
    path("order/<int:order_id>/", views.order_detail, name="order_detail"),

    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/status/', views.change_order_status, name='change_order_status'),

    path('reviews/add/<int:pk>/', views.add_review_ajax, name='add_review_ajax'),
    path('reviews/delete/<int:review_id>/', views.delete_review, name='delete_review'),
]
