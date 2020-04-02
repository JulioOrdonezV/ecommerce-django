# ecommerce-django #
this is a demo application for an ecommerce site developed with python's Django framework, its purpose is to demonstrate how 
to process orders and payments using different payment gateways or web services (Stripe and Pagadito)

### installation ###

* clone the repository and install the requiremets by running
`pip install -r requirements.txt`

* run the migrations:
`python manage.py migrate` (from the project home)

* load the seed data (optional)
`./manage.py loaddata db.json`

* run the local server:
`python manage.py runserver`


there is also a Procfile included if you want to deploy the application in heroku

for more information refer to the heroku documentation:
https://devcenter.heroku.com/articles/django-app-configuration

