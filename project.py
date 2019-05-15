#!/usr/bin/env python3
import random
import string
import httplib2
import json
import requests

from flask import Flask, render_template, request, redirect, url_for, flash
from flask import session as login_session
from flask import make_response
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from sqlalchemy import create_engine, asc, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.functions import coalesce


from database_setup import Base, User, Cuisine, Recipe
from forms import CuisineForm, DeleteForm, RecipeForm

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///catalogwithuserdb.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']


@app.route('/login')
def showLogin():
    """Login page route"""
    # Redirect to login page if user is not logged in
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
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
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
    print(h.request(url, 'GET')[1].decode("UTF-8"))
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

    stored_access_token = login_session.get('access_token')
    stored_gid = login_session.get('gid')
    if stored_access_token is not None and gid == stored_gid:
        response = make_response(json.dumps('Current user is already connected.'),
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
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
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
    # Fetching short-time access token from client,
    # app id and app secret from stored json file
    access_token = request.data.decode('utf-8')
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

    # If user not present create user
    # try:
    #     user = session.query(User).filter_by(email=login_session['email']).one()
    #     user = user.id
    # except Exception as e:
    #     user = None

    user = getUserId(login_session['email'])
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
    print("inside disconnect")
    # Google logout functionality
    if login_session['provider'] == 'google':
        print("inside if Google")
        # Fetch access token from login session
        access_token = login_session.get('access_token')

        # Return error message if no access token
        if access_token is None:
            response = make_response(json.dumps(
                "Current user not connected."), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Sending logout request and getting status code
        url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
        params = {'alt': 'json'}
        result = requests.get(url, params=params, headers={
                              'content-type':
                              'application/x-www-form-urlencoded'})
        status_code = getattr(result, 'status_code')

        # token = login_session['access_token']
        # url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % token
        # h = httplib2.Http()
        # result = h.request(url, 'GET')[0]

        # If status code is 200, deleting login session data
        if status_code == 200:
            del login_session['gid']
            del login_session['username']
            del login_session['picture']
            del login_session['email']
            del login_session['user_id']
            del login_session['access_token']
            del login_session['state']
            # Message to display when the user logs out
            flash("Logged out Successfully!")
            # Redirecting to home page
            return redirect('/')

        # If status code is not 200
        else:
            response = make_response(json.dumps(
                'Failed to revoke connection Google.'), 400)
            response.headers['Content-Type'] = 'application/json'
            return response

    # Facebook logout functionality
    if login_session['provider'] == 'facebook':
        # Fetching facebook id and access token from login session
        facebook_id = login_session['facebook_id']
        access_token = login_session['access_token']

        # If no access token, returning error message
        if access_token is None:
            response = make_response(json.dumps(
                "Current user not connected."), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Sending logout request
        url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (
            facebook_id, access_token)
        h = httplib2.Http()
        result = h.request(url, 'DELETE')[1].decode('utf-8')
        res = json.loads(result)
        print(res)

        # If response contains success, deleting login session data
        if res['success'] is True:
            del login_session['username']
            del login_session['picture']
            del login_session['email']
            del login_session['user_id']
            del login_session['access_token']
            del login_session['state']
            # Message to display when user logs out
            flash("Logged out Successfully!")
            # Redirect to home page
            return redirect('/')

        # If response doesn't contains success
        else:
            response = make_response(json.dumps(
                'Failed to revoke connection fb.'), 400)
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
    stmt = session.query(Recipe.cuisine_id, func.count('*').
                         label('recipe_count')).\
        group_by(Recipe.cuisine_id).subquery()
    cuisines = session.query(Cuisine, stmt.c.recipe_count, Cuisine.id, Cuisine.name).\
        outerjoin(stmt, Cuisine.id == stmt.c.cuisine_id).order_by(Cuisine.name)

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

    if 'username' not in login_session:
        return render_template("publicIndex.html", cuisines=cuisines, recipes=latestRecipes)

    return render_template("index.html", cuisines=cuisines, recipes=latestRecipes)


@app.route('/cuisine/new', methods=['GET', 'POST'])
def newCuisine():
    if 'username' not in login_session:
        return redirect('/login')
    form = CuisineForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            cuisine = Cuisine(name=form.name.data, user_id=login_session['user_id'])
            session.add(cuisine)
            session.commit()
            return redirect(url_for('index'))
    else:
        return render_template("newCuisine.html", form=form)


@app.route('/cuisine/<int:cuisine_id>/edit/', methods=['GET', 'POST'])
def editCuisine(cuisine_id):
    editedCuisine = session.query(
        Cuisine).filter_by(id=cuisine_id).one()

    if 'username' not in login_session:
        return redirect('/login')
    if editedCuisine.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this Cuisine. Please create your own Cuisine in order to edit.');}</script><body onload='myFunction()''>"

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
    if 'username' not in login_session:
        return redirect('/login')
    if restaurantToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this restaurant. Please create your own restaurant in order to delete.');}</script><body onload='myFunction()''>"
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
    creator = getUserInfo(cuisine.user_id)
    recipes = session.query(Recipe).filter_by(cuisine_id=cuisine_id).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicrecipes.html', recipes=recipes, cuisine=cuisine, creator=creator)
    return render_template('recipes.html', cuisine=cuisine, recipes=recipes, creator=creator)


@app.route('/cuisine/<int:cuisine_id>/recipe/new', methods=['GET', 'POST'])
def newRecipe(cuisine_id):
    if 'username' not in login_session:
        return redirect('/login')

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
    creator = getUserInfo(cuisine.user_id)
    recipe = session.query(Recipe).filter_by(cuisine_id=cuisine_id, id=recipe_id).one()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicRecipe.html', cuisine=cuisine, recipe=recipe, creator=creator)
    return render_template('recipe.html', cuisine=cuisine, recipe=recipe, creator=creator)


@app.route('/cuisine/<int:cuisine_id>/recipe/<int:recipe_id>/edit/', methods=['GET', 'POST'])
def editRecipe(cuisine_id, recipe_id):
    cuisine = session.query(
        Cuisine).filter_by(id=cuisine_id).one()
    editedRecipe = session.query(
        Recipe).filter_by(id=recipe_id).one()

    if 'username' not in login_session:
        return redirect('/login')
    if editedRecipe.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this Recipe. Please create your own Recipe in order to edit.');}</script><body onload='myFunction()''>"

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

    if 'username' not in login_session:
        return redirect('/login')
    if recipeToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to Delete this Recipe. Please create your own Recipe in order to Delete.');}</script><body onload='myFunction()''>"

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
