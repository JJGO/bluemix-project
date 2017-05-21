import datetime
import atexit
import os
import random
import shutil
import string
import sys

import cf_deployment_tracker

from flask import Flask, render_template, request, jsonify, session, url_for
from services import load_credentials, get_database, get_watson_service, teardown_databases, get_speech_voices
import watson_developer_cloud.natural_language_understanding.features.v1 as features


# Emit Bluemix deployment event
cf_deployment_tracker.track()

app = Flask(__name__)

app.config['DATABASE'] = 'mydb'
app.config['TMPFOLDER'] = 'tmp'
app.secret_key = "\xfd4\xadtJ\x1a'\xed\xe9\x0e`{\xd4\x8a\x11.ah\x87j\t\xad\x9e\xac"

vcap = load_credentials()


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


@app.route('/api/recent')
def recent_searches():
    user = get_user()
    db, client = get_database(app.config['DATABASE'])

    past_searches = [(doc['name'], doc['timestamp']) for doc in db if doc['user'] == user][::-1]

    sorted_searches = [name for (name, timestamp) in sorted(past_searches, key=lambda x: x[1], reverse=True)]

    return jsonify(sorted_searches)


@app.route('/api/analyze-text', methods=['POST', 'GET'])
def analyze_text():
    # text = request.json['text']
    text = "No pienso comer ensalada, es un plato asqueroso e insípido"
    translator = get_watson_service('language_translator')
    nlu = get_watson_service('natural-language-understanding')
    text_to_speech = get_watson_service('text_to_speech')
    voices = get_speech_voices()

    source_lang = translator.identify(text)['languages'][0]['language']
    english_text = translator.translate(text, source=source_lang, target='en')

    audioEN = text_to_speech.synthesize(english_text, accept='audio/ogg', voice="en-GB_KateVoice")

    audiofile = ''.join(random.choice(string.ascii_lowercase) for i in range(20)) + '.ogg'
    audiofile = os.path.join(app.config['TMPFOLDER'], audiofile)

    with open(os.path.join('static', audiofile), 'wb') as f:
        f.write(audioEN)

    emotions = nlu.analyze(text=english_text, features=[features.Emotion()])
    emotions = emotions['emotion']['document']['emotion']

    audiourl = url_for('static', filename=audiofile)

    s = render_template('output-text.html', audiourl=audiourl, emotions=emotions)

    with open('test.html', 'w') as f:
        print(s, file=f)

    return s


@app.route('/api/visitors', methods=['GET'])
def get_visitor():
    user = get_user()

    db, client = get_database(app.config['DATABASE'])

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
    db, client = get_database(app.config['DATABASE'])
    translator = get_watson_service('language_translator')

    translated_name = translator.translate(name, source='es', target='en')

    user = get_user()

    timestamp = datetime.datetime.now().isoformat()

    data = {'name': translated_name, 'user': user, 'timestamp': timestamp}
    db.create_document(data)

    return 'La traduccion de {0} es {1}'.format(name, translated_name)


@atexit.register
def shutdown():
    teardown_databases()


if __name__ == '__main__':
    debug = False
    if len(sys.argv) > 1:
        if '--debug' in sys.argv:
            debug = True

    tmpfolder = os.path.join('static', app.config['TMPFOLDER'])
    if os.path.isdir(tmpfolder):
        shutil.rmtree(tmpfolder)
    os.mkdir(tmpfolder)

    app.run(host='0.0.0.0', port=port, debug=debug)
