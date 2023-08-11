pip install --user -r requirements.txt &&
pip install --user -r requirements-dev.txt &&
# pip install --user -r requirements-dev.txt &&
PGSERVICEFILE=".pgservice.conf" ./manage.py migrate
### If you prefer not to use django runserver
# pip install --user gunicorn
# gunicorn --bind 0.0.0.0:8000 lidotiku.wsgi --reload