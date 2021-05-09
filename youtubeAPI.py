import requests
import urllib.parse
from config import config

def youtubeAPI(endpoint, params):
    params['key'] = config['APIKey'] # on ajoute la clé de l'API youtube dans les paramètres URL
    url = 'https://www.googleapis.com/youtube/v3/' + endpoint + '?' + urllib.parse.urlencode(params) # on construit l'URL
    r = requests.get(url)
    return r.json()