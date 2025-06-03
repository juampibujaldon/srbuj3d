# Comandos CURL para probar la API

## 1. Registrar un nuevo usuario
```
curl -X POST http://127.0.0.1:8000/api/accounts/register/ \
-H "Content-Type: application/json" \
-d '{
    "username": "nuevo_usuario",
    "email": "nuevo_usuario@example.com",
    "password": "password123",
    "password2": "password123"
}'
```

---

## 2. Loguear un usuario (obtener tokens JWT)
```
curl -X POST http://127.0.0.1:8000/api/accounts/login/ \
-H "Content-Type: application/json" \
-d '{
    "username": "nuevo_usuario",
    "password": "password123"
}'
```

---

## 3. Ver el usuario actual (requiere token de acceso)
Reemplaza `<ACCESS_TOKEN>` con el token de acceso obtenido en el paso 2.

```
curl -X GET http://127.0.0.1:8000/api/accounts/me/ \
-H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

## 4. Desloguear un usuario (invalidar el refresh token)
Reemplaza `<REFRESH_TOKEN>` con el token de refresco obtenido en el paso 2.
```
curl -X POST http://127.0.0.1:8000/api/accounts/logout/ \
-H "Content-Type: application/json" \
-d '{
    "refresh": "<REFRESH_TOKEN>"
}'
```