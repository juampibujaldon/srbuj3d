from django.urls import path, include
from rest_framework import routers
from ventas import views

router = routers.DefaultRouter()
router.register(r'admin', views.AdminViewSet, basename='Admin')
router.register(r'products', views.ProductViewSet, basename='Product')
router.register(r'orders', views.OrderViewSet, basename='Order')
router.register(r'cart', views.CartViewSet, basename='Cart')
router.register(r'payment', views.PaymentViewSet, basename='Payment')
router.register(r'stlmodel', views.STLModelViewSet, basename='STLModel')
router.register(r'sell', views.SellViewSet, basename='Sell')

urlpatterns = [
    path('ventas/model/', include(router.urls)),
    path('products/', views.ProductCreateView.as_view(), name='product-create'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('products/<int:pk>/update/', views.ProductUpdateView.as_view(), name='product-update'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product-delete'),
    path('cart/add/', views.CartAddView.as_view(), name='cart-add'),
    path('products/list/', views.ProductListView.as_view(), name='product-list'),
    path('orders/panel/', views.OrderPanelView.as_view(), name='order-panel'),
    path('payment-methods/', views.PaymentMethodListView.as_view(), name='payment-method-list'),
    path('cart/checkout/', views.CartCheckoutView.as_view(), name='cart-checkout'),
]