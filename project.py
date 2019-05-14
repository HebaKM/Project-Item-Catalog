#!/usr/bin/env python3

from flask import Flask, render_template
from sqlalchemy import create_engine, asc, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.functions import coalesce


from database_setup import Base, Cuisine, Recipe


app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///catalogdb.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/cuisines/')
def index():
    stmt = session.query(Recipe.cuisine_id, func.count('*').
                         label('recipe_count')).\
        group_by(Recipe.cuisine_id).subquery()
    cuisines = session.query(Cuisine, stmt.c.recipe_count, Cuisine.name).\
        outerjoin(stmt, Cuisine.id == stmt.c.cuisine_id).order_by(Cuisine.name)

    print(cuisines)
    # cuisines = session.query(Cuisine).order_by(asc(Cuisine.name))
    # cuisines = [
    #     {
    #         'name': 'test#1',
    #         'count': 0
    #     },
    #     {
    #         'name': 'test#2',
    #         'count': 1
    #     },
    #     {
    #         'name': 'test#3',
    #         'count': 2
    #     },
    #     {
    #         'name': 'test#4',
    #         'count': 3
    #     },
    #     {
    #         'name': 'test#5',
    #         'count': 4
    #     }
    # ]
    # for c in cuisines:
    #     if c.recipe_count is None:
    #         print("It is None")
    #     print(type(c.recipe_count))
    #     print(c.recipe_count)

    recipes = [
        {
            'name': 'test#1',
            'cuisine': "test"
        },
        {
            'name': 'test#2',
            'cuisine': "test"
        },
        {
            'name': 'test#3',
            'cuisine': "test"
        },
        {
            'name': 'test#4',
            'cuisine': "test"
        },
        {
            'name': 'test#5',
            'cuisine': "test"
        }
    ]
    # return "Hi"
    return render_template("index.html", cuisines=cuisines, recipes=recipes)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000, threaded=False)
