from django.shortcuts import render

from rest_framework import viewsets
from .serializer import *
from .models import *  
from ventas_user_admin.serializer import UserSerializer    
from ventas_user_admin.models import User 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from rest_framework.permissions import IsAuthenticated
from .models import User
from .serializer import UserSerializer, UserCreateByAdminSerializer
from rest_framework import generics, permissions, serializers
from .permissions import IsAdminUserCustom



class UserView(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()

#!ADAPTARLO A MI DB


class LoginView(APIView):
    def post(self, request):
        identifier = request.data.get("identifier")
        password = request.data.get("password")
        if not identifier or not password:
            return Response({"error": "Se requiere 'identifier' y 'password'"}, status=status.HTTP_400_BAD_REQUEST)


        try:
            user_obj = User.objects.get(username=identifier)
        except User.DoesNotExist:
            try:
                user_obj = User.objects.get(email=identifier)
            except User.DoesNotExist:
                return Response({"error": "Usuario no encontrado"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=user_obj.username, password=password)
        if user:
            login(request, user)
            return Response({
                "message": "Login exitoso",
                "username": user.username,
                "role": user.role
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Credenciales inválidas"}, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logout exitoso"}, status=status.HTTP_200_OK)
    
class CreateUserByAdminView(generics.CreateAPIView):
    serializer_class = UserCreateByAdminSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserCustom]

    def perform_create(self, serializer):
        user = self.request.user
        if user.role != 'admin':
            raise serializers.ValidationError({"detail": "No tienes permiso para crear usuarios."})
        serializer.save(company=user.company) 