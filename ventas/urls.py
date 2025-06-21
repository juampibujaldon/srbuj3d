from django.urls import path, include 
from rest_framework import routers
from ventas import views
from django.urls import path
from .views import (
    ProductCreateView,
    ProductDetailView,
    ProductUpdateView,
    ProductDeleteView,
)
from .views import CartAddView
from .views import ProductCreateView, ProductListView
from .views import OrderPanelView


router = routers.DefaultRouter()
router.register(r'admin', views.AdminView, basename='Admin')
router.register(r'product', views.ProductView, basename='Product')
router.register(r'order', views.OrderView, basename='Order')
router.register(r'cart', views.CartView, basename='Cart')
router.register(r'payment', views.PaymentView, basename='Payment')
router.register(r'stlmodel', views.STLModelView, basename='STLModel')
router.register(r'sell', views.SellView, basename='Sell')

urlpatterns = [
    path('ventas/model', include(router.urls)),
    path('products/', ProductCreateView.as_view(), name='product-create'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/<int:pk>/update/', ProductUpdateView.as_view(), name='product-update'),
    path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product-delete'),
    path('cart/add/', CartAddView.as_view(), name='cart-add'),
    path('products/list/', ProductListView.as_view(), name='product-list'),
    path('orders/panel/', OrderPanelView.as_view(), name='order-panel'),
]
