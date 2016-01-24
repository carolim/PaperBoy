# import the Flask class from the flask module
import os
import boto.dynamodb2
from boto.dynamodb2.fields import HashKey, RangeKey, KeysOnlyIndex, GlobalAllIndex
from boto.dynamodb2.table import Table
from boto.dynamodb2.types import NUMBER
from flask import Flask, render_template, redirect, url_for, request, session, json
from flask.ext.dynamo import Dynamo
from werkzeug import generate_password_hash, check_password_hash

# create environment variables
os.environ['AWS_SECRET_ACCESS_KEY'] = "UVMvkydy6RT0VthqxtG/qWwnd2WBd+IVqKvLQOOt"
os.environ['AWS_ACCESS_KEY_ID'] = "AKIAIYIZFUIROGPQQLYQ"

# create the application object
app = Flask(__name__)
app.config['DYNAMO_TABLES'] = [
	Table('users', schema=[HashKey('email')]), 
	Table('requests_incoming', schema=[HashKey('user_id')]), 
	Table('requests_outgoing', schema=[HashKey('user_id')]), 
	Table('requests', schema=[HashKey('request_id')])
]
app.secret_key = 'itissnowingreallyhard'

# create dynamo object
dynamo = Dynamo(app)

# home page
@app.route('/')
def home():
	return render_template('index.html')

# form submit
@app.route('/formSubmit',methods=['POST'])
def formSubmit():
	_name = request.form['inputName']
	_email = request.form['inputEmail']
	_password = request.form['inputPassword']

	_field = request.form['field']
	print _field
	if _field == "btn-login":
		return validate_login(_email,_password)
	else:
		return create_user(_name,_email,_password)


# create a new user
# @app.route('/create_user', methods=['POST'])
def create_user(name, email,password):
	print "creating user..."
	try:
		_name = request.form['inputName']
		_email = request.form['inputEmail']
		_password = request.form['inputPassword']

		print "this is getting here"
		print "name: {}, email: {}, password: {}".format(_name, _email, _password)

		# validate values
		if _name and _email and _password:
			# put values into database
			print "putting item in db"
			dynamo.users.put_item(data={
					'email': _email,
					'name': _name,
					'password': generate_password_hash(_password)
				})
			print "put item in db"
			return json.dumps({'message': 'User created successfully!'})
		else:
			return json.dumps({'html':'<span>Please enter the required fields.</span>'})
	except Exception as e:
		return json.dumps({'error':str(e)})


# validate login
# @app.route('/validate_login', methods=['POST'])
def validate_login(email,password):
	try:
		_email = request.form['inputEmail']
		_password = request.form['inputPassword']

		user = dynamo.users.get_item(email=_email)
		if check_password_hash(user['password'], _password):
			session['userid'] = user['email']
			print "name: {}".format(session['name'])
			print "redirecting to newsfeed...."
			return redirect('/newsfeed')
		else:
			return render_template('error.html', error='Wrong email address or password.')
	except Exception as e:
		return json.dumps({'error':str(e)})

# newsfeed
@app.route('/newsfeed')
def newsfeed():
	if session.get('userid'):
		return render_template('newsfeed.html')
	else:
		return render_template('error.html',error = 'Unauthorized Access')
	

# TODO:
# newsfeed page that loads and displays all active requests 
# personal page that shows person's profile
# create a request
# delete a request
# accept a request

# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(debug=True)