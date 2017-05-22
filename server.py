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


@app.route('/api/analyze-text', methods=['POST'])
def analyze_text():
    text = request.json['text']
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
    show_piechart = any( value > 0 for key, value in emotions.items() )
    s = render_template('output-text.html', text=text, english_text=english_text, 
        audiourl=audiourl, emotions=emotions, show_piechart=show_piechart)
    #with open('text.html', 'w') as f:
    #    print(s, file=f)
    return s

@app.route('/api/analyze-image', methods=['POST'])
def analyze_image():
    visual_recognition = get_watson_service('watson_vision_combined')
    
    url = request.json['text']
    vr_output = visual_recognition.classify(images_url=url)

    vr_long = str(vr_output)
    vr_short=''
    
    content=vr_output['images'][0]

    show_bars=False
    concepts=None

    for i in content:
        if(i=='classifiers'):
            show_bars=True
            concepts
            aux=content[i][0]['classes']
            vr_short = vr_short+'La imagen representa:'
            for j in aux:
                vr_short = vr_short+' '+j['class']+' ('+str(j['score'])+'),'
            concepts = [ (item['class'], item['score']) for item in aux ]
            concepts = sorted(concepts, key=lambda k: k[1], reverse=True)
        elif(i=='faces'):
            vr_short = vr_short+'\nLa imagen es una cara.\n'
            aux=content[i][0]
            for j in aux:
                if(j!='face_location'):
                    vr_short = vr_short+j+': '
                    vr_short = vr_short+str(aux[j])+'\n'
        elif(i=='text'):
            vr_short = vr_short+'\nEl texto de la imagen es: \n'+content[i]

    s = render_template('output-image.html', url_img=url, vr_short=vr_short, vr_long=vr_long, concepts=concepts, show_bars=show_bars)
    #with open('text.html', 'w') as f:
    #    print(s, file=f)
    return s


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
