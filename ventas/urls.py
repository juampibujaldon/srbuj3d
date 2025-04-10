from django.urls import path, include 
from rest_framework import routers
from ventas import views

router = routers.DefaultRouter()
router.register(r'user', views.UserView, basename='User')
router.register(r'admin', views.UserView, basename='Admin')
router.register(r'product', views.UserView, basename='Product')
router.register(r'order', views.UserView, basename='Order')
router.register(r'cart', views.UserView, basename='Cart')
router.register(r'payment', views.UserView, basename='Payment')
router.register(r'stlmodel', views.UserView, basename='STLModel')
# router.register(r'transactions', views.TransactionView, basename='transactions')

urlpatterns = [
    path('ventas/model', include(router.urls)),
]
