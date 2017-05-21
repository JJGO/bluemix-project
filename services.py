import os
import json

from cloudant import Cloudant

from watson_developer_cloud import LanguageTranslatorV2
from watson_developer_cloud import TextToSpeechV1
from watson_developer_cloud import SpeechToTextV1
from watson_developer_cloud import VisualRecognitionV3
from watson_developer_cloud import NaturalLanguageUnderstandingV1

service_dict = {
    'language_translator': LanguageTranslatorV2,
    'text_to_speech': TextToSpeechV1,
    'speech_to_text': SpeechToTextV1,
    'natural-language-understanding': NaturalLanguageUnderstandingV1,
    'watson_vision_combined': VisualRecognitionV3,
}


vcap = {}

connected_services = {}

databases = {}

client = None


def load_credentials():
    if 'VCAP_SERVICES' in os.environ:
        loaded_vcap = json.loads(os.getenv('VCAP_SERVICES'))
    elif os.path.isfile('vcap-local.json'):
        with open('vcap-local.json') as f:
            loaded_vcap = json.load(f)
            loaded_vcap = loaded_vcap['services']
    return vcap.update(loaded_vcap)


def get_database(dbname):
    global client
    if dbname not in databases:
        assert 'cloudantNoSQLDB' in vcap

        creds = vcap['cloudantNoSQLDB'][0]['credentials']

        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        if client is None:
            client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(dbname, throw_on_exists=False)

        databases[dbname] = (db, client)

    return databases[dbname]


def get_watson_service(name):

    if name == 'visual-recognition':
        name = 'watson_vision_combined'

    if name not in connected_services:
        cls = service_dict[name]

        creds = vcap[name][0]['credentials']

        if name in ['watson_vision_combined']:
            api_key = creds["api_key"]
            handler = cls(cls.latest_version, api_key=api_key)
        else:
            user = creds['username']
            password = creds['password']
            url = cls.default_url
            if name in ['natural-language-understanding']:
                handler = cls(cls.latest_version, username=user, password=password, url=url)
            else:
                handler = cls(username=user, password=password, url=url)

        connected_services[name] = handler

    return connected_services[name]


def reset_services():
    load_credentials()
    connected_services.clear()


def teardown_databases():
    client.disconnect()
