from flask import Flask, render_template, request, jsonify, session
import cf_deployment_tracker
import os
import random
from services import get_credentials, get_database, get_watson_service
import sys

# Emit Bluemix deployment event
cf_deployment_tracker.track()

app = Flask(__name__)

app.config['DATABASE'] = 'mydb'
app.secret_key = "\xfd4\xadtJ\x1a'\xed\xe9\x0e`{\xd4\x8a\x11.ah\x87j\t\xad\x9e\xac"

vcap = get_credentials()


def get_user():
    if 'username' not in session:
        user = str(random.randint(1, 10000))
        session['username'] = user
        print('User {0} created'.format(user))
    return session['username']


# On Bluemix, get the port number from the environment variable PORT
# When running this app on the local machine, default the port to 8080
port = int(os.getenv('PORT', 8080))


@app.route('/')
def home():
    return render_template('index.html')

# /* Endpoint to greet and add a new visitor to database.
# * Send a POST request to localhost:8080/api/visitors with body
# * {
# * 	"name": "Bob"
# * }
# */


@app.route('/api/visitors', methods=['GET'])
def get_visitor():
    user = get_user()

    db, client = get_database(vcap, app.config['DATABASE'])

    return jsonify([doc['name'] for doc in db if doc['user'] == user])

# /**
#  * Endpoint to get a JSON array of all the visitors in the database
#  * REST API example:
#  * <code>
#  * GET http://localhost:8080/api/visitors
#  * </code>
#  *
#  * Response:
#  * [ "Bob", "Jane" ]
#  * @return An array of all the visitor names
#  */


@app.route('/api/visitors', methods=['POST'])
def put_visitor():
    name = request.json['name']
    # Translate
    db, client = get_database(vcap, app.config['DATABASE'])
    translator = get_watson_service(vcap, 'language_translator')

    translated_name = translator.translate(name, source='es', target='en')

    user = get_user()

    data = {'name': translated_name, 'user': user}
    db.create_document(data)

    return 'La traduccion de {0} es {1}'.format(name, translated_name)


if __name__ == '__main__':
    debug = False
    if len(sys.argv) > 1:
        if '--debug' in sys.argv:
            debug = True

    init_services()

    app.run(host='0.0.0.0', port=port, debug=debug)
