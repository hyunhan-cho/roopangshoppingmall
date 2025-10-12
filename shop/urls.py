# shop/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ex: / -> 상품 목록 페이지
    path('', views.product_list, name='product_list'),
    # ex: /product/1/ -> 상품 상세 페이지
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    # ex: /cart/ -> 장바구니 페이지
    path('cart/', views.cart_view, name='cart_view'),
    path('api/cart/add/', views.add_to_cart, name='add_to_cart'),
    path('api/recommend/ai/', views.api_ai_recommendations, name='api_ai_recommendations'),
]