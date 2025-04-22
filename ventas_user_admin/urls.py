from django.urls import path, include
from rest_framework import routers
from .views import UserView

router = routers.DefaultRouter()
router.register(r'register', UserView, basename='register')

urlpatterns = [
    path('register/', include(router.urls)),
]