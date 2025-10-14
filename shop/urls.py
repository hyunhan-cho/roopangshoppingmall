# shop/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # 메인 홈(랜딩)
    path('', views.home, name='home'),
    # 상품 목록
    path('products/', views.product_list, name='product_list'),
    # ex: /product/1/ -> 상품 상세 페이지
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    # ex: /cart/ -> 장바구니 페이지
    path('cart/', views.cart_view, name='cart_view'),
    path('api/cart/add/', views.add_to_cart, name='add_to_cart'),
    path('api/cart/update/', views.update_cart, name='update_cart'),
    path('api/cart/clear/', views.clear_cart, name='clear_cart'),
    path('api/recommend/ai/', views.api_ai_recommendations, name='api_ai_recommendations'),
    # 자동완성 & 트렌딩
    path('api/search/suggest/', views.api_search_suggest, name='api_search_suggest'),
    path('api/search/trending/', views.api_search_trending, name='api_search_trending'),
]