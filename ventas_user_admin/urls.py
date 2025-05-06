from django.urls import path, include
from rest_framework import routers
from .views import UserView
from .views import UserView, LoginView, LogoutView, CreateUserByAdminView

router = routers.DefaultRouter()
router.register(r'register', UserView, basename='register')

urlpatterns = [
    path('register/', include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('admin/create-user/', CreateUserByAdminView.as_view(), name='admin-create-user'),
    # path('login/', LoginView.as_view(), name='login'),
    # path('logout/', LogoutView.as_view(), name='logout'),
]