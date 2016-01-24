# import the Flask class from the flask module
import os
import boto.dynamodb2
from boto.dynamodb2.fields import HashKey, RangeKey, KeysOnlyIndex, GlobalAllIndex
from boto.dynamodb2.table import Table
from boto.dynamodb2.types import NUMBER
from flask import Flask, render_template, redirect, url_for, request, session, json
from flask.ext.dynamo import Dynamo
from werkzeug import generate_password_hash, check_password_hash
import datetime


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
	if session.get('userid'):
		return render_template('newsfeed.html')
	else:
		return render_template('index.html')

# logout
@app.route('/logout')
def logout():
	session.pop('userid',None)
	return redirect('/')

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
			return redirect('/')
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
	
@app.route('/getRequests')
def getRequests():
	try:
		if session.get('userid'):
			print "got the userid"
			_email = session.get('userid')
			print "email is ",_email
			active_requests = dynamo.requests.scan()
			print "active_requests: ",active_requests
			requests_dict = []
			for req in active_requests:
				req_dict = {
				'email':req['requester_email'],
				'subject':req['subject'],
				'price':req['price'],
				'timestamp':req['timestamp'],
				'status':req['status']
				}
				requests_dict.append(req_dict)
			return json.dumps(requests_dict)

		else:
		    return render_template('error.html', error = 'Unauthorized Access')
	except Exception as e:
		return render_template('error.html', error = str(e))

@app.route('/getIncomingRequests')
def getIncomingRequests():
	try:
		if session.get('userid'):
			_email = session.get('userid')
			incoming_requests = dynamo.requests.scan(requester_email__eq=_email)
			print incoming_requests
			incoming_requests_dict = []
			for req in incoming_requests:
				req_dict = {
				'email':req['requester_email'],
				'subject':req['subject'],
				'timestamp':req['timestamp']
				}
				incoming_requests_dict.append(req_dict)
			return json.dumps(incoming_requests_dict)
		else:
			return render_template('error.html', error="Unauthorized Access")
	except Exception as e:
		return render_template('error.html',error=str(e))

@app.route('/getOutgoingRequests')
def getOutgoingRequests():
	try:
		if session.get('userid'):
			_email = session.get('userid')
			outgoing_requests = dynamo.requests.scan(acceptor_email__eq=_email)
			outgoing_requests_dict = []
			for req in outgoing_requests:
				req_dict = {
				'email':req['acceptor_email'],
				'subject':req['subject'],
				'timestamp':req['timestamp']
				}
				outgoing_requests_dict.append(req_dict)
			print json.dumps(outgoing_requests_dict)
			return json.dumps(outgoing_requests_dict)
		else:
			return render_template('error.html', error="Unauthorized Access")
	except Exception as e:
		return render_template('error.html',error=str(e))

@app.route('/createRequest',methods=['POST'])
def createRequest():
	try:
		if session.get('userid'):
			i = datetime.datetime.now()
			rows = dynamo.requests.scan()
			count = 0
			for r in rows:
				count = count + 1
			count = count + 1

			# parameters
			_requesteremail = session.get('userid')
			_subject = request.form['request']
			_status = "Available"
			_timestamp = i.strftime('%Y/%m/%d %H:%M:%S')
			_price = str(request.form['price'])
			_id = str(count)

			# add it to requests
			dynamo.requests.put_item(data={
				'request_id':_id,
				'acceptor_email':"true",
				'price':_price,
				'requester_email':_requesteremail,
				'status':_status,
				'subject':_subject,
				'timestamp':_timestamp
			})
			return redirect('/newsfeed')


		else:
			return json.dumps({'html':'<span>Please enter the required fields.</span>'})
	except Exception as e:
		return json.dumps({'error':str(e)}) 

@app.route('/getAllUserRequests')
def getAllUserRequests():
	# get all requests for a particular user
	try:
		if session.get('userid'):
			_email = session.get('userid')
			incoming_requests = dynamo.requests.scan(requester_email__eq=_email)
			outgoing_requests = dynamo.requests.scan(acceptor_email__eq=_email)

			requests_dict = []
			for req in incoming_requests:
				req_dict = {'requester':req['requester_email'],'subject':req['subject'],'price':req['price'],'acceptor':req['acceptor_email'], 'timestamp':req[timestamp]}
				requests_dict.append(req_dict)		
			for req in outgoing_requests:
				req_dict = {'requester':req['requester_email'],'subject':req['subject'],'price':req['price'],'acceptor':req['acceptor_email'], 'timestamp':req[timestamp]}
				requests_dict.append(req_dict)	
			return json.dumps(requests_dict)
		else:
			return render_template('error.html', error='Unauthorized Access')
	except Exception as e:
		return render_template('error.html', error=str(e))


# render profile page
@app.route('/profile')
def profile():
	if session.get('userid'):
		return render_template('profile.html')
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