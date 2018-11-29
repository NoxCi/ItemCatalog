# Item Catalog
This is my second proyect of the course, an Item Catalog made with python 2.7.1

## Setup
In order to work with this project you need to install Virtual Machine(VM),
Vagrant and get newsdata.sql to populate the database news

To setup the VM and Vagrant, execute the next
```
vagrant init ubuntu/trusty64
vagrant up
```
and get in with
```
vagrant up && vagrant ssh
```

Also you need to install the next modules from pip
- sqlalchemy
- flask
- requests
- oauth2client
- json
you can install them with
```
sudo pip install module
```

You also need to have a google account to login

## Running the app
To run the app you need to be in your virtual machine and in the root folder of
the proyect in a terminal an execute with
```
python project.py
```
then open a browser and go to
```
localhost:5000
```
