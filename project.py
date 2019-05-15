#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine, asc, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.functions import coalesce


from database_setup import Base, Cuisine, Recipe
from forms import CuisineForm, DeleteForm, RecipeForm

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///catalogwithdatedb.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showLogin():
    return 'Hi'


@app.route('/')
@app.route('/cuisines/')
def index():
    stmt = session.query(Recipe.cuisine_id, func.count('*').
                         label('recipe_count')).\
        group_by(Recipe.cuisine_id).subquery()
    cuisines = session.query(Cuisine, stmt.c.recipe_count, Cuisine.id, Cuisine.name).\
        outerjoin(stmt, Cuisine.id == stmt.c.cuisine_id).order_by(Cuisine.name)

    # print(cuisines)
    # cuisines = session.query(Cuisine).order_by(asc(Cuisine.name))

    # for c in cuisines:
    #     if c.recipe_count is None:
    #         print("It is None")
    #     print(type(c.recipe_count))
    #     print(c.recipe_count)

    latestRecipes = []
    recipes = session.query(Recipe).order_by(
        Recipe.creationDate.desc()).limit(10).all()
    if recipes is not None:
        for recipe in recipes:
            latestRecipesDict = {'cuisine': '', 'recipe': ''}
            latestRecipesDict['recipe'] = recipe
            cuisine = session.query(Cuisine).filter_by(id=recipe.cuisine_id).one()
            latestRecipesDict['cuisine'] = cuisine
            latestRecipes.append(latestRecipesDict)

    else:
        latestRecipes = None
    # return "Hi"
    return render_template("index.html", cuisines=cuisines, recipes=latestRecipes)


@app.route('/cuisine/new', methods=['GET', 'POST'])
def newCuisine():
    form = CuisineForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            cuisine = Cuisine(name=form.name.data)
            session.add(cuisine)
            session.commit()
            return redirect(url_for('index'))
    else:
        return render_template("newCuisine.html", form=form)


@app.route('/cuisine/<int:cuisine_id>/edit/', methods=['GET', 'POST'])
def editCuisine(cuisine_id):
    editedCuisine = session.query(
        Cuisine).filter_by(id=cuisine_id).one()
    form = CuisineForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            editedCuisine.name = form.name.data
            flash('Cuisine Successfully Edited %s' % editedCuisine.name)
            return redirect(url_for('showRecipes', cuisine_id=editedCuisine.id))
    return render_template('editCuisine.html', form=form, cuisine=editedCuisine)


@app.route('/cuisine/<int:cuisine_id>/delete/', methods=['GET', 'POST'])
def deleteCuisine(cuisine_id):
    cuisineToDelete = session.query(
        Cuisine).filter_by(id=cuisine_id).one()
    form = DeleteForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            session.delete(cuisineToDelete)
            flash('%s Successfully Deleted' % cuisineToDelete.name)
            session.commit()
            return redirect(url_for('index', cuisine_id=cuisine_id))
    return render_template('deleteCuisine.html', cuisine=cuisineToDelete, form=form)


@app.route('/cuisine/<int:cuisine_id>/recipes')
def showRecipes(cuisine_id):
    cuisine = session.query(
        Cuisine).filter_by(id=cuisine_id).one()
    recipes = session.query(Recipe).filter_by(cuisine_id=cuisine_id).all()
    return render_template('recipes.html', cuisine=cuisine, recipes=recipes)


@app.route('/cuisine/<int:cuisine_id>/recipe/new', methods=['GET', 'POST'])
def newRecipe(cuisine_id):
    cuisine = session.query(
        Cuisine).filter_by(id=cuisine_id).one()
    form = RecipeForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            newRecipe = Recipe(name=form.name.data, description=form.description.data,
                               cuisine_id=cuisine_id)
            session.add(newRecipe)
            session.commit()
            flash('New Recipe %s Successfully Created' % (newRecipe.name))
            return redirect(url_for('showRecipes', cuisine_id=cuisine_id))
    return render_template('newRecipe.html', form=form, cuisine=cuisine)


@app.route('/cuisine/<int:cuisine_id>/recipe/<int:recipe_id>/')
def showRecipe(cuisine_id, recipe_id):
    cuisine = session.query(
        Cuisine).filter_by(id=cuisine_id).one()
    recipe = session.query(Recipe).filter_by(cuisine_id=cuisine_id, id=recipe_id).one()
    return render_template('recipe.html', cuisine=cuisine, recipe=recipe)


@app.route('/cuisine/<int:cuisine_id>/recipe/<int:recipe_id>/edit/', methods=['GET', 'POST'])
def editRecipe(cuisine_id, recipe_id):
    cuisine = session.query(
        Cuisine).filter_by(id=cuisine_id).one()
    editedRecipe = session.query(
        Recipe).filter_by(id=recipe_id).one()
    form = RecipeForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            editedRecipe.name = form.name.data
            editedRecipe.description = form.description.data
            flash('Recipe Successfully Edited %s' % editedRecipe.name)
            return redirect(url_for('showRecipes', cuisine_id=cuisine_id))
    return render_template('editRecipe.html', form=form, cuisine=cuisine, recipe=editedRecipe)


@app.route('/cuisine/<int:cuisine_id>/recipe/<int:recipe_id>/delete/', methods=['GET', 'POST'])
def deleteRecipe(cuisine_id, recipe_id):
    cuisine = session.query(
        Cuisine).filter_by(id=cuisine_id).one()
    recipeToDelete = session.query(
        Recipe).filter_by(cuisine_id=cuisine_id, id=recipe_id).one()
    form = DeleteForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            session.delete(recipeToDelete)
            flash('%s Successfully Deleted' % recipeToDelete.name)
            session.commit()
            return redirect(url_for('showRecipes', cuisine_id=cuisine_id))
    return render_template('deleteRecipe.html', recipe=recipeToDelete, form=form, cuisine=cuisine)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000, threaded=False)
