python ecommerce/manage.py flush --noinput
python ecommerce/manage.py migrate
ecommerce/manage.py loaddata db.json
