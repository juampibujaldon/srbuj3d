from django.urls import path, include 
from rest_framework import routers
from ventas import views


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

]
