from django.contrib.auth import authenticate, login, logout
from rest_framework import viewsets, generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from .models import User
from .serializer import UserSerializer, UserCreateByAdminSerializer
from .permissions import IsAdminUserCustom
from rest_framework.authtoken.models import Token


class UserView(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()

class LoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response({
                "message": "Login exitoso",
                "username": user.username,
                "role": user.role
            }, status=status.HTTP_200_OK)
        return Response({"error": "Credenciales inválidas"}, status=status.HTTP_400_BAD_REQUEST)
    
class LogoutView(APIView):
    def post(self, request):
        if request.user.is_authenticated:
            logout(request)
            return Response({"message": "Sesión cerrada"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "No hay sesión activa"}, status=status.HTTP_400_BAD_REQUEST)
    
class CreateUserByAdminView(generics.CreateAPIView):
    serializer_class = UserCreateByAdminSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserCustom]
    

    def perform_create(self, serializer):
        user = self.request.user
        if user.role != 'admin':
            raise serializers.ValidationError({"detail": "No tienes permiso para crear usuarios."})
        serializer.save(company=user.company)