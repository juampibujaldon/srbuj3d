from django.urls import path, include 
from rest_framework import routers
from ventas import views

router = routers.DefaultRouter()
router.register(r'user', views.UserView, basename='User')
# router.register(r'transactions', views.TransactionView, basename='transactions')

urlpatterns = [
    path('ventas/model', include(router.urls)),
]
