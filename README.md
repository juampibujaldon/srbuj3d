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

📄 License

This project is licensed under the MIT license.
