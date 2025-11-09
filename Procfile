release: python manage.py migrate
web: sh -c "python manage.py collectstatic --noinput && gunicorn srbuj_3d.wsgi:application --bind 0.0.0.0:$PORT"
