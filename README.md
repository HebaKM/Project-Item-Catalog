# Project: Item Catalog
Udacity Full Stack Web Developer Nanodegree
##  Project Overview
You will develop an application that provides a list of items within a variety of categories as well as provide a user registration and authentication system. Registered users will have the ability to post, edit and delete their own items.

## Requirements
* [Vagrant](https://www.vagrantup.com/downloads.html)
* [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
* [Python3](https://www.python.org/downloads/)
* [Flask](http://flask.pocoo.org/)
* [Flask-WTF](https://flask-wtf.readthedocs.io/en/stable/)
* [httplib2](https://github.com/httplib2/httplib2)
* [oauth2client](https://github.com/googleapis/oauth2client)
* [requests](https://2.python-requests.org/en/master/)
* [SQLAlchemy](https://www.sqlalchemy.org/)
* Unix-style terminal

## Setup Instructions
### Vagrant VM setup
1. Install Vagrant, VirtualBox, and Python3
2. If you are using a Mac or Linux system, your regular terminal program will do just fine. On Windows, it is recommend to use the Git Bash terminal that comes with the [Git software](https://git-scm.com/downloads).
3. Clone or download the [Vagrant VM configuration file](https://github.com/udacity/fullstack-nanodegree-vm)
4. Clone Or download this repository. Then, Paste the files from this project into the vagrant/Item Catalog directory

### Set up new OAuth2 client ID and secret
This projects uses Third Party [OAuth 2.0](https://oauth.net/2/) authentication (Google and Facebook). The following steps explain how to set up a client ID and secret in Google and Facebook.

#### Google OAuth
1. First, login to your Google account. Then visit [Google Developers Console](https://console.developers.google.com/).
2. Choose credentials from the menu on the left.
3. Click on the **Create credentials** drop down menu and choose **OAuth client id**.
4. When presented with list of application types, choose web application.
5. Next, type a name for the app and set the following:
   * The authorized JavaScript origins:
     http://localhost:5000
   * And the authorized redirect URIs:
     http://localhost:5000/gconnect
6. After clicking **Create**, You should now be able to get the client ID and client secret.
7. Download the OAuth 2.0 client ID and save it as "client_secrets.json" to the root project folder.

#### Facebook OAuth
1. First, login to your Facebook account. Then visit [Facebook Developers page](https://developers.facebook.com).
2. Next, create a new application. And choose a name for the app and type a contact email.
3. Click **Add Platform** at the bottom of the basic settings, select website.
4. Configure the URL site as: `http://localhost:5000/`.
5. Click the plus icon in the left menu to add a new product.
6. Choose **Facebook Login**.
7. Finally, save the app ID and secret in a file called "fb_client_secret.json" to the root project folder. Use the following format in the file:
     ```json
     {
        "web" : {
            "app_id": "YOUR_APP_ID",
            "app_secret" : "YOUR_APP_SECRET"
        }
    }
     ```

### Required Packages
Run the command `pip3 install –r requirements.txt` to install all the required packages.

## Steps to run this project
1. Open terminal and navigate to the FSND-Virtual-Machine directory, then run the command: `cd vagrant`.
2. Inside the vagrant subdirectory, run the command `vagrant up`. This will cause Vagrant to download the Linux operating system and install it.
3. Next, log into the virtual machine: `vagrant up` `vagrant ssh`
4. Inside the VM, change directory to /vagrant/Item Catalog: `cd /vagrant/'Item Catalog'`
5. Run the command `python3 database_setup.py` to create the database.
6. Run the command `python3 lotsofitemswithusers.py` to populate the database with initial values.
7. Next, run the command `python3 project.py` to run the application.
8. Finally, access the application by visiting [http://localhost:5000](http://localhost:5000).
    Note: If you are using Windows you might need to change the line ending of the project.py and database_setup.py from CRLF to LF.

## API Endpoints
1. JSON endpoint API route for all cuisines
    `/cuisines/JSON`
2. JSON endpoint API route for all recipes of a cuisine
    `/cuisine/cuisine_id/recipes/JSON`
3. JSON endpoint API route for a recipe
    `/cuisine/cuisine_id/recipe/recipe_id/JSON`
## Credits
Logo Image [credit](https://www.freepik.com/free-vector/kitchen-icons-set_893796.htm).
User Image [credit](https://www.flaticon.com/free-icon/user_1177568).
Google Icon [credit](https://www.flaticon.com/free-icon/search_281764#term=google&page=1&position=8).
