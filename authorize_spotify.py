import base64
import datetime
import json
import random
import re
import requests
import string
from credentials import spotify_credentials


def generate_state():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))


def get_authorization():
    state_val = generate_state()

    base_url = 'https://accounts.spotify.com/authorize'
    client_id = 'client_id=' + spotify_credentials.CLIENT_ID
    response_type = 'response_type=code'
    redirect_uri = 'redirect_uri=https://localhost:8888/callback'
    state = 'state=' + state_val
    scope = 'scope=playlist-modify-public+playlist-read-private'

    print(base_url + '?' + client_id + '&' +
          response_type + '&' + redirect_uri + '&' + scope)
    response_url = input('Enter response url: ')
    get_tokens(response_url)


def get_tokens(auth_url):
    base_url = 'https://accounts.spotify.com/api/token'

    client_string = base64.b64encode(
        (spotify_credentials.CLIENT_ID + ':' + spotify_credentials.CLIENT_SECRET).encode()).decode("utf-8")

    headers = {
        'Authorization': 'Basic ' + client_string,
        'content-type': 'application/x-www-form-urlencoded'
    }

    body = {
        'grant_type': 'authorization_code',
        'code':  get_auth_code(auth_url),
        'redirect_uri': 'https://localhost:8888/callback'
    }

    response = requests.request(
        'POST', base_url, params=body, headers=headers).json()

    print('Access Token: ' + response['access_token'])
    print('Refresh Token: ' + response['refresh_token'])
    print('Expires At: ' + str(int(round(datetime.datetime.utcnow().timestamp()
                                         * 1000)) + response['expires_in']))


def get_auth_code(url):
    return (re.findall(r'(?<=code=)[^\s?]*', url)[0])


get_authorization()


# get_tokens('https://localhost:8888/callback?code=AQCTUbps_scjGkAAsFuSRyecNTg6C0hs3knWGbIdA_8ef9UIGfbiIOKyg_Qj97WnEficeoKIe0QYIx-_91Yj92nHEtRdvTPz6DdIpOnQgsUwcJimA_bgIMT7NXfo0trlKFXwhkBrW2bjSF_dhph8exCaSbC6mJhG7jR-9j4JbB6h6rKcHWZ9C88jqkNYshCYOKhMgsj9nxUm9VHGRLydpkFglNrc6X-Dhi31PN2E0w&state=s99ObpmZvEP8jset')
