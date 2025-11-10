srbuj_3d is an e-commerce platform developed with Django, MySQL, and React, focused on selling 3D prints and STL files.
The project aims to facilitate the connection between creators/designers and buyers interested in customized products or digital files for 3D printing.
🚀 Features

🛒 Shopping cart and order management

👤 User authentication and admin panel

📦 Management of physical and digital products (.stl)

💳 Payment gateway integration (in progress)

🔍 Product search and filtering

📁 STL file download after purchase

⚙️ Backend with Django + MySQL

🌐 Frontend with React

🛠️ Technologies

    Backend: Django

    Database: MySQL

    Frontend: Django Templates + Bootstrap

    Authentication: Django Authentication System

    API: Django REST Framework

📦 Local Installation (development mode)

Clone the repository:

```bash
git clone https://github.com/tuusuario/srbuj_3d.git
cd srbuj_3d
```
Install dependencies:
```
cd backend
python -m venv venv
source venv/bin/activate  # o venv\Scripts\activate en Windows
pip install -r requirements.txt
```
Run migrations and start the server:
````
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
````
Install Frontend:
````
cd ../frontend
npm install
npm start
````

🚂 Deploy en Railway
--------------------

1. Crea un servicio **Django** en Railway y conecta este repositorio.
2. Configura la variable `PYTHON_VERSION` (opcional) y añade los valores de `.env.example` en la pestaña **Variables** (al menos `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`, `DATABASE_URL` o `DB_*`, `CORS_ALLOWED_ORIGINS` y `CSRF_TRUSTED_ORIGINS`).
3. Railway instalará dependencias con `pip install -r requirements.txt` y levantará el proyecto usando el `Procfile`.
4. Después del primer deploy abre la consola del servicio y ejecuta:
   ```
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py createsuperuser --noinput  # opcional
   ```
5. Una vez finalizado, el backend quedará expuesto en `https://<tu-servicio>.up.railway.app`.

📄 License

This project is licensed under the MIT license.
