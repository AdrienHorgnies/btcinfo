# BTC info
Small project to fetch information about blocks and transactions from 'https://blockchain.info'.

Fetches information from the API and store them in a local database.

## Getting Started

This project uses Django ORM.
Refer to Django for its settings and usage.

Install requirements:

    pip install -r requirements.txt

Create a database with name, username and password equal to "postgres", 
or change the settings appropriately.

Example using Docker :
    
    docker run --name bcinfo_db -p 5432:5432 -e POSTGRES_PASSWORD=postgres -d postgres

Make and apply migrations for the database :

    ./manage.py makemigrations
    ./manage.py migrate


Start the script :

    ./main.py 01-01-2021 31-01-2021

