from django.urls import path, include
from rest_framework import routers
from .views import UserView
from .views import UserView, LoginView, LogoutView, CreateUserByAdminView

router = routers.DefaultRouter()
router.register(r'register', UserView, basename='register')

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', CreateUserByAdminView.as_view(), name='register'),
    path('admin/create-user/', CreateUserByAdminView.as_view(), name='admin-create-user'),
]