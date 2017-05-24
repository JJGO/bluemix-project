from server import app, init
import json

from services import load_credentials, get_database, get_watson_service

import pytest

app.config['CACHEDB'] = 'testcache'
app.config['VISITDB'] = 'visitcache'
app.config['TESTING'] = True


testapp = app.test_client()

init()


@pytest.fixture(scope="module")
def cacheDB():
    db, client = get_database(app.config['CACHEDB'])
    yield db


@pytest.fixture(scope="module")
def visitDB():
    db, client = get_database(app.config['VISITDB'])
    yield db
    db.delete()


@pytest.fixture(scope="module")
def text_request():
    response = testapp.post('/api/analyze-text',
                            data=json.dumps({'text': "Nada"}),
                            content_type='application/json'
                            )
    yield response


@pytest.fixture(scope="module")
def image_request():
    image_url = "http://jinja.pocoo.org/docs/2.9/_static/jinja-small.png"
    response = testapp.post('/api/analyze-image',
                            data=json.dumps({'text': image_url}),
                            content_type='application/json'
                            )
    yield response


def test_service_connection():
    load_credentials()
    get_watson_service('language_translator')
    get_watson_service('text_to_speech')
    get_watson_service('speech_to_text')
    get_watson_service('natural-language-understanding')
    get_watson_service('watson_vision_combined')


def test_index():
    response = testapp.get('/')
    assert response.status_code == 200
    assert b'Erittely' in response.data


def test_analyze_text(text_request, cacheDB):

    assert text_request.status_code == 200
    response_json = json.loads(text_request.data.decode())
    assert 'url' in response_json
    query_id = response_json['url'][len('/text/'):]
    print(query_id)
    assert query_id in [doc['id'] for doc in cacheDB]


def test_analyze_image(image_request, cacheDB):

    assert image_request.status_code == 200
    response_json = json.loads(image_request.data.decode())
    assert 'url' in response_json
    query_id = response_json['url'][len('/image/'):]
    print(query_id)
    assert query_id in [doc['id'] for doc in cacheDB]


def test_analyze_text_output(text_request):
    response_json = json.loads(text_request.data.decode())
    url = response_json['url']

    response = testapp.get(url, follow_redirects=True)
    print(response.data)
    assert response.status_code == 200

    assert b'Spanish' in response.data
    assert b'Nothing' in response.data
    assert b'Tristeza' in response.data


def test_analyze_image_output(image_request):
    response_json = json.loads(image_request.data.decode())
    url = response_json['url']

    response = testapp.get(url, follow_redirects=True)
    print(response.data)
    assert response.status_code == 200

    assert b'Framework' in response.data
