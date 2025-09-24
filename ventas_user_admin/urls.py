from django.urls import path, include
from rest_framework import routers
from .views import (
    UserView,
    LoginView,
    LogoutView,
    RegisterView,
    ProfileView,
    CreateUserByAdminView,
)

router = routers.DefaultRouter()
router.register(r'users', UserView, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('admin/create-user/', CreateUserByAdminView.as_view(), name='admin-create-user'),
]
