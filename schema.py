import requests
import json
import os

API_DIR = 'api-docs/'
API_URL = "https://api.glowmarkt.com/api-docs/v0-1/"

API_LIST = [
    'dmssys',
    'resourcesys',
    'vesys',
    'usersys/usertypes',
]


def parseResponse(text):
    lines = text.splitlines()
    START_TAG = '<div id="swagger-options" style="display:none">'
    END_TAG = '</div>'
    for line in lines:
        if line.startswith(START_TAG):
            return line[len(START_TAG):len(line)-len(END_TAG)]
    return None


session = requests.Session()
for api in API_LIST:
    print("Fetching ", api)
    resp = session.get(API_URL + api)
    schema = parseResponse(resp.text)
    if schema is None:
        print(resp.text)
    else:
        schema = json.loads(schema)
        filename = API_DIR + api
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename + '.json', "w") as f:
            json.dump(schema, f, indent=2)
