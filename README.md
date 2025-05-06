# srbuj_3d

**srbuj_3d** es un e-commerce desarrollado con Django, MySQL y React, orientado a la venta de impresiones 3D y archivos STL. 
El proyecto busca facilitar la conexión entre creadores/diseñadores y compradores interesados en productos personalizados o archivos digitales para impresión 3D.

## 🚀 Características

- 🛒 Carrito de compras y gestión de pedidos
- 👤 Autenticación de usuarios y panel administrativo
- 📦 Gestión de productos físicos e intangibles (.stl)
- 💳 Integración con pasarelas de pago (en progreso)
- 🔍 Búsqueda y filtrado de productos
- 📁 Descarga de archivos STL tras la compra
- ⚙️ Backend con Django + MySQL
- 🌐 Frontend con React

## 🛠️ Tecnologías

- **Backend:** Django
- **Base de Datos:** MySQL
- **Frontend:** Django Templates + Bootstrap
- **Autenticación:** Django Authentication System
- **API:** Django REST Framework

## 📦 Instalación local (modo desarrollo)

1. Clona el repositorio:

```bash
git clone https://github.com/tuusuario/srbuj_3d.git
cd srbuj_3d
```
Instalar dependencias
```
cd backend
python -m venv venv
source venv/bin/activate  # o venv\Scripts\activate en Windows
pip install -r requirements.txt
```
Ejecutar migraciones y servidor
````
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
````
Instalar Frontend
````
cd ../frontend
npm install
npm start
````
## 📄 Licencia
Este proyecto está bajo la licencia **MIT**.
