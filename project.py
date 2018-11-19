from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem, User

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

engine = create_engine('sqlite:///restaurants.db', connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
@app.route('/catalog')
def showCatalog():
    categories = session.query(Category).order_by(asc(Category.name))
    if 'username' not in login_session:
        return render_template('publicIndex.html',categories = categories)
    return render_template('index.html', categories = categories)

@app.route('\login')
def showLogin():
    pass

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
                                                      auhor = auhor)
    else:
        return render_template('category.html', items = items,
                                                category = category,
                                                auhor = auhor)

@app.route('/catalog/new',methods = ['GET','POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect ('/login')

    if request.method == 'POST'
        newCategory = Category(user_id=login_session['user_id'],
                               name=request.form['name'])
        session.add(newCategory)
        session.commit()
        flash('New category %s succesfuly created' % newCategory.name)

        return rendirect(url_for('showCatalog'))
    else:
        return render_template('newCategory.html')

@app.route('/catalog/<int:category_id>/edit',methods = ['GET','POST'])
def editCategory(category_id):
    if 'username' not in login_session or author.id != login_session['user_id']:
        return redirect ('/login')

    categoryToEdit = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST'
        if request.form['name']:
            categoryToEdit.name = request.form['name']
            flash('Category succesfuly edited')
            return redirect(url_for('showCatalog'))
    else:
        return render_template('editCategory.html',category=categoryToEdit)

@app.route('/catalog/<int:category_id>/delete',methods = ['GET','POST'])
def deleteCategory():
    if 'username' not in login_session or author.id != login_session['user_id']:
        return redirect ('/login')

    categoryToDelete = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST'
        session.delete(categoryToDelete)
        flash('%s category succesfuly deleted' % categoryToDelete.name)
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteCategory.html',category=categoryToDelete)

##############
# CRUD Items #
##############
@app.route('/catalog/<int:category_id>/category/<int:item_id>/item')
def showItem(item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(id=item_id).one()
    author = session.query(User).filter_by(id = category.user_id).one()

    if 'username' not in login_session or author.id != login_session['user_id']:
        return render_template('publicItem.html', item = item,
                                                  category = category,
                                                  auhor = auhor)
    return render_template('item.html', item = item,
                                        category = category,
                                        auhor = auhor)

@app.route('/catalog/<int:category_id>/category/new',methods = ['GET','POST'])
def newItem(category_id):
    if 'username' not in login_session:
        return redirect ('/login')

    category = session.query(Category).filter_by(id = category_id).one()
    if request.method == 'POST'
        newItem = Item(category_id=category_id,
                       user_id=login_session['user_id'],
                       name=request.form['name'],
                       description=request.form['description'])
        session.add(newItem)
        session.commit()
        flash('New item %s succesfully created' % newItem.name)

        return redirect(url_for('showCategory',category_id=category_id))
    else:
        return render_template('newItem.html',item=itemToEdit)

@app.route('/catalog/<int:category_id>/category/<int:item_id>/edit',methods = ['GET','POST'])
def editItem(category_id,item_id):
    if 'username' not in login_session or author.id != login_session['user_id']:
        return redirect ('/login')

    itemToEdit = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST'
        if request.form['name']:
            itemToEdit.name = request.form['name']
        if request.form['description']:
            itemToEdit.description = request.form['description']

        session.add(itemToEdit)
        session.commit()
        flash('Item succesfuly edited')

        return redirect(url_for('showCategory',category_id=category_id))
    else:
        return render_template('editItem.html',item=itemToEdit)

@app.route('/catalog/<int:category_id>/category/<int:item_id>/delete',methods = ['GET','POST'])
def deleteItem(category_id,item_id):
    if 'username' not in login_session or author.id != login_session['user_id']:
        return redirect ('/login')

    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST'
        session.delete(itemToDelete)
        session.commit()
        flash('Item %s succesfuly deleted' % itemToDelete.name)

        return redirect(url_for('showCategory',category_id=category_id))
    else:
        return render_template('deleteItem.html',item=itemToDelete)

if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 5000)
