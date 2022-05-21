# BTC info
It is a small project to fetch information about blocks and transactions by querying 'https://blockchain.info'.

It fetches information from the API and store it in a local PostgresQL database.

## Getting Started

This project uses Django ORM.
Refer to Django for its settings and usage.

Install requirements:

    pip install -r requirements.txt

Create a database with name, username and password equal to "postgres", 
or change the settings appropriately.

Example using Docker :
    
    docker run --name bcinfo_db -p 5432:5432 -e POSTGRES_PASSWORD=postgres -d postgres

Make and apply the migrations for the database :

    ./manage.py makemigrations
    ./manage.py migrate


Retrieve the data :

    ./main.py retrieve 01-01-2021 31-01-2021

Draw graphs using the data :

    ./main.py draw
