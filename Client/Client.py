import ProjectSettings
ProjectSettings.Init()
import requests
import CSECommon
import webbrowser
import urllib.parse

# Log the user in
redirect_uri = urllib.parse.quote_plus(CSECommon.SERVER_URL + CSECommon.AUTH)
scope = urllib.parse.quote_plus("publicData esi-location.read_location.v1")
param_string = f'response_type=code&redirect_uri={redirect_uri}&client_id={CSECommon.CLIENT_ID}&scope={scope}&state={CSECommon.STATE_STRING}'
webbrowser.open("https://login.eveonline.com/v2/oauth/authorize/?"+param_string)