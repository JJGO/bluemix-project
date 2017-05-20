from flask import Flask, render_template, request, jsonify
import atexit
import cf_deployment_tracker
import os
from services import get_credentials, get_database, get_watson_service
import sys

# Emit Bluemix deployment event
cf_deployment_tracker.track()

app = Flask(__name__)

vcap = get_credentials()

db_name = 'mydb_translate'
db, client = get_database(vcap, db_name)

translator = get_watson_service(vcap, 'language_translator')
text_to_speech = get_watson_service(vcap, 'text_to_speech')
speech_to_text = get_watson_service(vcap, 'speech_to_text')
nlu = get_watson_service(vcap, 'natural-language-understanding')
visual_recognition = get_watson_service(vcap, 'watson_vision_combined')

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
    return jsonify(list(map(lambda doc: doc['name'], db)))

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
    translated_name = translator.translate(name, source='es', target='en')

    data = {'name': translated_name}
    db.create_document(data)
    return 'La traduccion de {0} es {1}'.format(name, translated_name)


@atexit.register
def shutdown():
    client.disconnect()


if __name__ == '__main__':
    debug = False
    if len(sys.argv) > 1:
        if sys.argv[1] == 'debug':
            debug = True
    app.run(host='0.0.0.0', port=port, debug=debug)
