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


def get_credentials():
    if 'VCAP_SERVICES' in os.environ:
        vcap = json.loads(os.getenv('VCAP_SERVICES'))
    elif os.path.isfile('vcap-local.json'):
        with open('vcap-local.json') as f:
            vcap = json.load(f)
            vcap = vcap['services']
    return vcap


def get_database(vcap, dbname):
    assert 'cloudantNoSQLDB' in vcap

    creds = vcap['cloudantNoSQLDB'][0]['credentials']

    user = creds['username']
    password = creds['password']
    url = creds['host']

    client = Cloudant(user, password, url=url, connect=True)
    db = client.create_database(dbname, throw_on_exists=False)

    return db, client


def get_watson_service(vcap, name):

    if name == 'visual-recognition':
        name = 'watson_vision_combined'

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

    return handler
