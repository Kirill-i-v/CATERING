To run the application you need:
1. Go to the folder where you installed the application
2. Open it with command manager
3. Type py manage.py runserver(python manage.py runserver)
4. Go to  http://127.0.0.1:8000/ in your browser

Loading Test Fixtures

1. Run migrations:
   py manage.py migrate(python manage.py migrate)
2. Load test data:
   py manage.py loaddata food/fixtures/food_fixtures.json(python manage.py loaddata food/fixtures/food_fixtures.json)
   py manage.py loaddata delivery/fixtures/delivery_fixtures.json(python manage.py loaddata delivery/fixtures/delivery_fixtures.json)
3. Start the Django server and access the admin panel:
   py manage.py runserver(python manage.py runserver)

Why JSON Fixtures?
JSON is structured, easy to read, and maintains relationships between models effectively.
