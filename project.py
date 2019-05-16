#!/usr/bin/env python3
import random
import string
import json

from sqlalchemy.sql.functions import coalesce
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy import create_engine, asc, func
from oauth2client.client import FlowExchangeError
from oauth2client.client import flow_from_clientsecrets
from flask import make_response
from flask import session as login_session
from flask import Flask, render_template, request, redirect, url_for, flash
from flask import jsonify
import httplib2
import requests

from database_setup import Base, User, Cuisine, Recipe
from forms import CuisineForm, DeleteForm, RecipeForm

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///catalogwithuserdb.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Fetches the client secrects from stored file
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


@app.route('/login')
def showLogin():
    """Login page route"""
    # Redirect to home page if user is logged in
    if 'username' in login_session:
        return redirect('/')

    # Creating state token
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    # Storing state token in the login session
    login_session['state'] = state

    # Passing state taken to client side
    return render_template('login.html', STATE=state)


# User Helper Functions


def createUser(login_session):
    """Creates a new user if the user does not exit in the db"""
    # Creates new user and commits the changes
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    # Fetches the new user then returns his/her id
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    """Returns user object using the passed id"""
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    """Returns the id associated with the passed email"""
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception as e:
        return None


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Google signin route"""
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    # print(h.request(url, 'GET')[1].decode("UTF-8"))
    result = json.loads(h.request(url, 'GET')[1].decode("UTF-8"))
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gid = credentials.id_token['sub']
    if result['user_id'] != gid:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the user is already logged in or not
    stored_access_token = login_session.get('access_token')
    stored_gid = login_session.get('gid')
    if stored_access_token is not None and gid == stored_gid:
        response = make_response(json.dumps
                                 ('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['provider'] = 'google'
    login_session['access_token'] = credentials.access_token
    login_session['gid'] = gid

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    # Storing the user data inside login session
    data = answer.json()
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ''' " style = "width: 300px; height: 300px;border-radius: 150px;
                -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '''

    flash("you are now logged in as %s" % login_session['username'])
    # print("done!")
    return output

# Facebook signin route
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    """Facebook signin route"""
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Fetches short-time access token from client
    access_token = request.data.decode('utf-8')
    # Fetches the app id and app secret from stored json file
    app_id = json.loads(open('fb_client_secret.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secret.json', 'r').read())['web']['app_secret']

    # Exchanging short-time token for login-time token
    url = "https://graph.facebook.com/oauth/access_token?client_id=%s" % (
        app_id)
    url += "&client_secret=%s&grant_type=fb_exchange_token" % (
        app_secret)
    url += "&fb_exchange_token=%s" % (access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1].decode('utf-8')
    token = result.split(',')[0].split(':')[1].replace('"', '')

    # Checking if user already logged in or not, if not return error message
    stored_access_token = login_session.get('access_token')
    if stored_access_token is not None:
        response = make_response(json.dumps
                                 ('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Sending request to fetch user data
    url = "https://graph.facebook.com/v3.2/me?access_token=%s" % token
    url += "&fields=name,id,email"
    h = httplib2.Http()
    result = h.request(url, 'GET')[1].decode('utf-8')

    # Storing user data in login session
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = "https://graph.facebook.com/v3.2/me/picture?access_token=%s" % token
    url += "&redirect=0&height=200&width=200"
    h = httplib2.Http()
    result = h.request(url, 'GET')[1].decode('utf-8')
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists, if it doesn't make a new one
    try:
        user = session.query(User).\
            filter_by(email=login_session['email']).one()
        user = user.id
    except Exception as e:
        user = None

    # user = getUserId(login_session['email'])
    if user is None:
        id = createUser(login_session)
        login_session['user_id'] = id
    else:
        login_session['user_id'] = user

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ''' " style = "width: 300px; height: 300px;border-radius: 150px;
                -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '''
    # Message to display when the user logs in
    flash("Now logged in as %s" % login_session['username'])

    return output


@app.route('/disconnect')
def disconnect():
    """Logout functionality route"""

    # Google logout functionality
    if login_session['provider'] == 'google':
        # Fetch access token from login session
        access_token = login_session.get('access_token')

        # Return error message if there is no access token
        if access_token is None:
            response = make_response(json.dumps(
                "Current user not connected."), 401)
            response.headers['Content-Type'] = 'application/json'
            return response
        print(access_token)

        # Send logout request and get status code
        url = ('https://accounts.google.com/o/oauth2/revoke?token=%s'
               % access_token)
        params = {'alt': 'json'}
        result = requests.get(url, params=params, headers={
                              'content-type':
                              'application/x-www-form-urlencoded'})
        status_code = getattr(result, 'status_code')

        # If status code is 200, delete login session data
        if status_code == 200:
            del login_session['gid']
            del login_session['username']
            del login_session['picture']
            del login_session['email']
            del login_session['user_id']
            del login_session['access_token']
            del login_session['state']
            del login_session['provider']
            # for i in login_session:
            #     print(i)

            # Message to display when the user logs out
            flash("Logged out Successfully!")
            # Redirect the user to home page
            return redirect('/')

        # If status code is not 200
        else:
            response = make_response(json.dumps(
                'Failed to revoke connection Google.'), 400)
            response.headers['Content-Type'] = 'application/json'
            return response

    # Facebook logout functionality
    if login_session['provider'] == 'facebook':
        # Fetch facebook id and access token from login session
        facebook_id = login_session['facebook_id']
        access_token = login_session['access_token']

        # If there is no access token, return error message
        if access_token is None:
            response = make_response(json.dumps(
                "Current user not connected."), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Send logout request
        url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (
            facebook_id, access_token)
        h = httplib2.Http()
        result = h.request(url, 'DELETE')[1].decode('utf-8')
        res = json.loads(result)
        print(res)

        # If response was successful, delete login session data
        if res['success'] is True:
            del login_session['username']
            del login_session['picture']
            del login_session['email']
            del login_session['user_id']
            del login_session['access_token']
            del login_session['state']
            del login_session['provider']
            del login_session['facebook_id']
            # for i in login_session:
            #     print(i)
            # Message to display when user logs out
            flash("Logged out Successfully!")

            # Redirect the user to home page
            return redirect('/')

        # If response was not successful
        else:
            response = make_response(json.dumps(
                'Failed to revoke connection Facebookb.'), 400)
            response.headers['Content-Type'] = 'application/json'
            return response


@app.route('/clearSession')
def clear_session():
    login_session.clear()
    return "session cleared"


@app.route('/')
@app.route('/cuisines/')
def index():
    """Index page route"""
    # Fetches the count of the recipes for each cuisine
    # stmt = session.query(Recipe.cuisine_id, func.count('*').
    #                      label('recipe_count')).\
    #     group_by(Recipe.cuisine_id).subquery()
    # cuisines = session.query(Cuisine, stmt.c.recipe_count,
    #                          Cuisine.id, Cuisine.name).\
    #     outerjoin(stmt, Cuisine.id == stmt.c.cuisine_id).\
    #      order_by(Cuisine.name)
    cuisines = session.query(Cuisine).\
        options(joinedload(Cuisine.recipes)).all()

    # Fetches the latest recipes added
    latestRecipes = []
    recipes = session.query(Recipe).order_by(
        Recipe.creationDate.desc()).limit(10).all()
    if recipes is not None:
        for recipe in recipes:
            latestRecipesDict = {'cuisine': '', 'recipe': ''}
            latestRecipesDict['recipe'] = recipe
            cuisine = session.query(Cuisine).\
                filter_by(id=recipe.cuisine_id).one()
            latestRecipesDict['cuisine'] = cuisine
            latestRecipes.append(latestRecipesDict)

    else:
        latestRecipes = None
    # Redirects to the publicIndex page if the user is not logged in
    if 'username' not in login_session:
        return render_template("publicIndex.html", cuisines=cuisines,
                               recipes=latestRecipes)

    return render_template("index.html", cuisines=cuisines,
                           recipes=latestRecipes)


@app.route('/cuisine/new', methods=['GET', 'POST'])
def newCuisine():
    """New Cuisine page route"""
    # Redirects to the login page if the user is not logged in
    if 'username' not in login_session:
        return redirect('/login')

    # Creates the new cuisine form
    form = CuisineForm()
    # POST method functionality
    if request.method == 'POST':
        # Checks if all the fields are valid
        if form.validate_on_submit():
            # Creates the new cuisine and commits the changes
            cuisine = Cuisine(name=form.name.data,
                              user_id=login_session['user_id'])
            session.add(cuisine)
            session.commit()
            flash('New Cuisine %s Successfully Created' % (cuisine.name))
            return redirect(url_for('showRecipes', cuisine_id=cuisine.id))
    return render_template("newCuisine.html", form=form)


@app.route('/cuisine/<int:cuisine_id>/edit/', methods=['GET', 'POST'])
def editCuisine(cuisine_id):
    """Edit Cuisine page route"""
    # Redirects to the login page if the user is not logged in
    if 'username' not in login_session:
        return redirect('/login')

    # Fetches the cuisine to edit it
    editedCuisine = session.query(
        Cuisine).filter_by(id=cuisine_id).one()

    # Checking authorization of the user
    if editedCuisine.user_id != login_session['user_id']:
        return """<script>function myFunction() {
        msg = 'You are not authorized to edit this Cuisine. ';
        msg += 'Please create your own Cuisine in order to edit.';
        alert(msg);
        window.location.replace('"""+url_for('index')+"""');}
        </script>
        <body onload='myFunction()''>"""
    # Creates the cuisine form
    form = CuisineForm()
    # POST method functionality
    if request.method == 'POST':
        # Checks if all the fields are valid
        if form.validate_on_submit():
            # Updates the cuisine and commits changes
            editedCuisine.name = form.name.data
            flash('Cuisine Successfully Edited To %s' % editedCuisine.name)
            return redirect(url_for('showRecipes',
                                    cuisine_id=editedCuisine.id))
    return render_template('editCuisine.html', form=form,
                           cuisine=editedCuisine)


@app.route('/cuisine/<int:cuisine_id>/delete/', methods=['GET', 'POST'])
def deleteCuisine(cuisine_id):
    """Delete Cuisine page route"""
    # Redirects to the login page if the user is not logged in
    if 'username' not in login_session:
        return redirect('/login')

    # Fetches the cuisine to delete it
    cuisineToDelete = session.query(
        Cuisine).filter_by(id=cuisine_id).one()

    # Checking authorization of the user
    if cuisineToDelete.user_id != login_session['user_id']:
        return """<script>function myFunction() {
        msg = 'You are not authorized to delete this Cuisine. ';
        msg += 'Please create your own Cuisine in order to delete.';
        alert(msg);
        window.location.replace('"""+url_for('index')+"""');
        }</script>
        <body onload='myFunction()'>"""
    # Creates the delete form
    form = DeleteForm()
    # POST method functionality
    if request.method == 'POST':
        # Checks if all the fields are valid
        if form.validate_on_submit():
            # Deletes the cuisine and commits the changes
            session.delete(cuisineToDelete)
            flash('%s Successfully Deleted' % cuisineToDelete.name)
            session.commit()
            return redirect(url_for('index'))
    return render_template('deleteCuisine.html', cuisine=cuisineToDelete,
                           form=form)


@app.route('/cuisine/<int:cuisine_id>/recipes')
def showRecipes(cuisine_id):
    """Show Recipes page route"""
    # Fetches the recipes that belong to the selected cuisine
    cuisine = session.query(
        Cuisine).filter_by(id=cuisine_id).one()
    creator = getUserInfo(cuisine.user_id)
    recipes = session.query(Recipe).filter_by(cuisine_id=cuisine_id).all()
    # Checking authorization of the user
    if ('username' not in login_session or
            creator.id != login_session['user_id']):
        return render_template('publicRecipes.html', recipes=recipes,
                               cuisine=cuisine, creator=creator)
    return render_template('recipes.html', cuisine=cuisine, recipes=recipes,
                           creator=creator)


@app.route('/cuisine/<int:cuisine_id>/recipe/new', methods=['GET', 'POST'])
def newRecipe(cuisine_id):
    """New Recipe page route"""
    # Redirects to the login page if the user is not logged in
    if 'username' not in login_session:
        return redirect('/login')
    # Fetches the cuisine to which the recipe belongs to
    cuisine = session.query(
        Cuisine).filter_by(id=cuisine_id).one()

    # Creates the new recipe form
    form = RecipeForm()
    # POST method functionality
    if request.method == 'POST':
        # Checks if all the fields are valid
        if form.validate_on_submit():
            # Creates the new recipe and commits the changes
            newRecipe = Recipe(name=form.name.data,
                               description=form.description.data,
                               cuisine_id=cuisine_id,
                               user_id=login_session['user_id'])
            session.add(newRecipe)
            session.commit()
            flash('New Recipe %s Successfully Created' % (newRecipe.name))
            return redirect(url_for('showRecipes', cuisine_id=cuisine_id))
    return render_template('newRecipe.html', form=form, cuisine=cuisine)


@app.route('/cuisine/<int:cuisine_id>/recipe/<int:recipe_id>/')
def showRecipe(cuisine_id, recipe_id):
    """Show Recipe page route"""
    # Fetches the selected recipe
    cuisine = session.query(
        Cuisine).filter_by(id=cuisine_id).one()
    creator = getUserInfo(cuisine.user_id)
    recipe = (session.query(Recipe).
              filter_by(cuisine_id=cuisine_id, id=recipe_id).one())
    # Checking authorization of the user
    if ('username' not in login_session or
            creator.id != login_session['user_id']):
        return render_template('publicRecipe.html', cuisine=cuisine,
                               recipe=recipe, creator=creator)
    return render_template('recipe.html', cuisine=cuisine, recipe=recipe,
                           creator=creator)


@app.route('/cuisine/<int:cuisine_id>/recipe/<int:recipe_id>/edit/',
           methods=['GET', 'POST'])
def editRecipe(cuisine_id, recipe_id):
    """Edit Recipe page route"""
    # Redirects to the login page if the user is not logged in
    if 'username' not in login_session:
        return redirect('/login')

    # Fetches the recipe to edit it
    cuisine = session.query(
        Cuisine).filter_by(id=cuisine_id).one()
    editedRecipe = session.query(
        Recipe).filter_by(id=recipe_id).one()

    # Checking authorization of the user
    if editedRecipe.user_id != login_session['user_id']:
        return """<script>function myFunction() {
        msg = 'You are not authorized to edit this Recipe. ';
        msg += 'Please create your own Recipe in order to edit.';
        alert(msg);
        window.location.replace('"""+(url_for('showRecipes',
                                              cuisine_id=cuisine.id))+"""')
         ;}</script>
         <body onload='myFunction()'>"""
    # Creates the recipe form
    form = RecipeForm()
    # POST method functionality
    if request.method == 'POST':
        # Checks if all the fields are valid
        if form.validate_on_submit():
            # Updates the recipe and commits changes
            editedRecipe.name = form.name.data
            editedRecipe.description = form.description.data
            flash('Recipe Successfully Edited to %s' % editedRecipe.name)
            return redirect(url_for('showRecipe', cuisine_id=cuisine_id,
                                    recipe_id=editedRecipe.id))
    return render_template('editRecipe.html', form=form, cuisine=cuisine,
                           recipe=editedRecipe)


@app.route('/cuisine/<int:cuisine_id>/recipe/<int:recipe_id>/delete/',
           methods=['GET', 'POST'])
def deleteRecipe(cuisine_id, recipe_id):
    """Delete Cuisine page route"""
    # Redirects to the login page if the user is not logged in
    if 'username' not in login_session:
        return redirect('/login')

    # Fetches the recipe to delete it
    cuisine = session.query(
        Cuisine).filter_by(id=cuisine_id).one()
    recipeToDelete = session.query(
        Recipe).filter_by(cuisine_id=cuisine_id, id=recipe_id).one()

    # Checking authorization of the user
    if recipeToDelete.user_id != login_session['user_id']:
        return """<script>function myFunction() {
        msg = 'You are not authorized to Delete this Recipe. ';
        msg += 'Please create your own Recipe in order to Delete.';
        alert(msg);window.location.replace('"""+(url_for('showRecipes',
                                                         cuisine_id=cuisine.id))+"""');
        }</script>
        <body onload='myFunction()'>"""
    # Creates the delete form
    form = DeleteForm()
    # POST method functionality
    if request.method == 'POST':
        # Checks if all the fields are valid
        if form.validate_on_submit():
            # Deletes the recipe and commits changes
            session.delete(recipeToDelete)
            flash('%s Successfully Deleted' % recipeToDelete.name)
            session.commit()
            return redirect(url_for('showRecipes', cuisine_id=cuisine_id))
    return render_template('deleteRecipe.html', recipe=recipeToDelete,
                           form=form, cuisine=cuisine)


# JSON APIs to view Cuisine Information
@app.route('/cuisines/all/JSON')
def allCuisinesJSON():
    # Fetches cuisines and related recipes
    cuisines = (session.query(Cuisine)
                .options(joinedload(Cuisine.recipes)).all())
    # Returning JSONified cuisines and related recipes
    return jsonify(Cuisine=[dict(cuisine.serialize,
                                 Recipes=[
                                     recipe.serialize
                                     for recipe in cuisine.recipes
                                 ])
                            for cuisine in cuisines])


@app.route('/cuisine/<int:cuisine_id>/recipes/JSON')
def cuisineRecipesJSON(cuisine_id):
    """JSON endpoint API route for all recipes of a cuisine"""
    cuisine = session.query(Cuisine).filter_by(id=cuisine_id).one()
    recipes = session.query(Recipe).filter_by(
        cuisine_id=cuisine_id).all()
    return jsonify(Recipe=[recipe.serialize for recipe in recipes])


@app.route('/cuisine/<int:cuisine_id>/recipe/<int:recipe_id>/JSON')
def recipeJSON(cuisine_id, recipe_id):
    """JSON endpoint API route for a recipe"""
    recipe = session.query(Recipe).filter_by(id=recipe_id).one()
    return jsonify(recipe=recipe.serialize)


@app.route('/cuisines/JSON')
def cuisinesJSON():
    """JSON endpoint API route for all cuisines"""
    cuisines = session.query(Cuisine).all()
    return jsonify(cuisines=[cuisine.serialize for cuisine in cuisines])

# Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handles 404 error"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handles 500 error"""
    # reset the session to a clean state
    session.rollback()
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = False
    app.run(host='0.0.0.0', port=5000, threaded=False)
