from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
app = Flask(__name__)

from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from model.database_setup import Base, User, Category, Item

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(
    open('secrets/client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///model/catalog.db', connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
@app.route('/catalog')
def showCatalog():
    categories = session.query(Category).order_by(asc(Category.name))
    recentItems = session.query(Item).order_by(desc(Item.id)).limit(10)
    if 'username' not in login_session:
        return render_template('publicIndex.html',categories = categories, recentItems = recentItems)
    return render_template('index.html', categories = categories, recentItems = recentItems)

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
               for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

def createUser(login_session):
    newUser = User(name=login_session['username'],
                    email=login_session['email'],
                    picture=login_session['picture'])
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
    print "......"
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('secrets/client_secrets.json', scope='')
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
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
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
    print "Done"
    return output

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        return redirect(url_for('showCatalog'))
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
    return redirect(url_for('showCatalog'))

###################
# CRUD Categories #
###################
@app.route('/catalog/<int:category_id>/category')
def showCategory(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    author = session.query(User).filter_by(id = category.user_id).one()

    if 'username' not in login_session:
        return render_template('publicCategory.html', items = items,
                                                      category = category,
                                                      author = author)
    else:
        return render_template('category.html', items = items,
                                                category = category,
                                                author = author)

@app.route('/catalog/new',methods = ['GET','POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect ('/login')

    if request.method == 'POST':
        newCategory = Category(user_id=login_session['user_id'],
                               name=request.form['name'])
        session.add(newCategory)
        session.commit()
        flash('New category %s succesfuly created' % newCategory.name)

        return redirect(url_for('showCatalog'))
    else:
        return render_template('newCategory.html')

@app.route('/catalog/<int:category_id>/edit',methods = ['GET','POST'])
def editCategory(category_id):
    categoryToEdit = session.query(Category).filter_by(id=category_id).one()
    author = session.query(User).filter_by(id = categoryToEdit.user_id).one()

    if 'username' not in login_session or author.id != login_session['user_id']:
        return redirect ('/login')

    if request.method == 'POST':
        if request.form['name']:
            categoryToEdit.name = request.form['name']
            flash('Category succesfuly edited')
            return redirect(url_for('showCatalog'))
    else:
        return render_template('editCategory.html',category=categoryToEdit)

@app.route('/catalog/<int:category_id>/delete',methods = ['GET','POST'])
def deleteCategory(category_id):
    categoryToDelete = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    author = session.query(User).filter_by(id = categoryToDelete.user_id).one()

    if 'username' not in login_session or author.id != login_session['user_id']:
        return redirect ('/login')

    if request.method == 'POST':
        for item in items:
            session.delete(item)
        session.delete(categoryToDelete)
        session.commit()
        flash('%s category succesfuly deleted' % categoryToDelete.name)
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteCategory.html',category=categoryToDelete)

##############
# CRUD Items #
##############
@app.route('/catalog/<int:category_id>/category/<int:item_id>/item')
def showItem(category_id,item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(id=item_id).one()
    author = session.query(User).filter_by(id = category.user_id).one()

    if 'username' not in login_session or author.id != login_session['user_id']:
        return render_template('publicItem.html', item = item,
                                                  category = category,
                                                  author = author)
    return render_template('item.html', item = item,
                                        category = category,
                                        author = author)

@app.route('/catalog/<int:category_id>/category/new',methods = ['GET','POST'])
def newItem(category_id):
    if 'username' not in login_session:
        return redirect ('/login')

    category = session.query(Category).filter_by(id = category_id).one()
    if request.method == 'POST':
        newItem = Item(category_id=category_id,
                       user_id=login_session['user_id'],
                       name=request.form['name'],
                       description=request.form['description'])
        session.add(newItem)
        session.commit()
        flash('New item %s succesfully created' % newItem.name)

        return redirect(url_for('showCategory',category_id=category_id))
    else:
        return render_template('newItem.html', category_id = category_id)

@app.route('/catalog/<int:category_id>/category/<int:item_id>/edit',methods = ['GET','POST'])
def editItem(category_id,item_id):
    itemToEdit = session.query(Item).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(id=category_id).one()
    author = session.query(User).filter_by(id = itemToEdit.user_id).one()

    if 'username' not in login_session or author.id != login_session['user_id']:
        return redirect ('/login')

    if request.method == 'POST':
        if request.form['name']:
            itemToEdit.name = request.form['name']
        if request.form['description']:
            itemToEdit.description = request.form['description']

        session.add(itemToEdit)
        session.commit()
        flash('Item succesfuly edited')

        return redirect(url_for('showCategory',category_id=category_id))
    else:
        return render_template('editItem.html',category=category,item=itemToEdit)

@app.route('/catalog/<int:category_id>/category/<int:item_id>/delete',methods = ['GET','POST'])
def deleteItem(category_id,item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    author = session.query(User).filter_by(id = itemToDelete.user_id).one()

    if 'username' not in login_session or author.id != login_session['user_id']:
        return redirect ('/login')

    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Item %s succesfuly deleted' % itemToDelete.name)

        return redirect(url_for('showCategory',category_id=category_id))
    else:
        return render_template('deleteItem.html',category = category, item=itemToDelete)

########
# JSON #
########
@app.route('/catalog/JSON')
def catalogJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])

@app.route('/catalog/<int:category_id>/category/JSON')
def categoryJSON(category_id):
    items = session.query(Item).filter_by(category_id=category_id).all()
    return jsonify(items=[i.serialize for i in items])

@app.route('/catalog/<int:category_id>/category/<int:item_id>/item/JSON')
def itemJSON(category_id,item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(item=item.serialize)

if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 5000)
