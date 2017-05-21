from server import app
import json

from services import load_credentials, get_database, get_watson_service

import pytest

app.config['DATABASE'] = 'testdb'
app.config['TESTING'] = True


testapp = app.test_client()


@pytest.fixture(scope="module")
def db():
    db, client = get_database(app.config['DATABASE'])
    yield db
    print("teardown db")
    print(type(db))
    db.delete()


def test_index(db):
    response = testapp.get('/')
    assert response.status_code == 200
    assert b'App Minima' in response.data


def test_ajax(db):
    response = testapp.post('/api/visitors',
                            data=json.dumps({'name': "Jose"}),
                            content_type='application/json'
                            )
    assert response.status_code == 200
    assert b'Jose' in response.data


def test_translation(db):
    response = testapp.post('/api/visitors',
                            data=json.dumps({'name': "perro"}),
                            content_type='application/json'
                            )
    assert response.status_code == 200
    assert b'Dog' in response.data


def test_service_connection():
    load_credentials()
    get_watson_service('language_translator')
    get_watson_service('text_to_speech')
    get_watson_service('speech_to_text')
    get_watson_service('natural-language-understanding')
    get_watson_service('watson_vision_combined')
