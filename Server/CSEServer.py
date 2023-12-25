import ProjectSettings
ProjectSettings.Init()
import CSECommon
import requests
import webbrowser
import json
import CSEMapModel
import CSEScraper
import asyncio
import aiohttp
import multiprocessing
import CSEServerLoop
import CSELogging
from flask import Flask, request
from base64 import b64encode
from telnetlib import NOP
app = Flask(__name__)

CLIENT_ID = 'ba636c6aeae54c8386770bc919ef2bca'
CLIENT_SECRET = 'EfdmhqJg7vncmfAEshRANS4wMtcawguFLGZSyJ9Z'
REFRESH_RATE = 1
EVE_SERVER_ROOT = 'https://esi.evetech.net/dev/'

access_token = 'INVALID'
refresh_token = 'INVALID'

class CSEServer:
    def __init__(self) -> None:
        self.m_Scrape = CSEScraper.ScrapeFileFormat()
        self.m_LoopQueue = None

server = CSEServer()

@app.route(CSECommon.FULL_SCRAPE, methods=['POST'])
def RecieveFullScrape():
    server.m_Scrape = server.m_LoopQueue.get()
    print(__file__ + "RecieveFullScrape")
    return "", CSECommon.OK_CODE

@app.route("/auth")
def Auth():
    code = request.args.get('code')
    url_encoded = {'grant_type' : 'authorization_code', 'code' : code}
    user_and_pass = CLIENT_ID + ':' + CLIENT_SECRET
    user_and_pass = user_and_pass.encode("utf-8")
    user_and_pass_param = b64encode(user_and_pass).decode("ascii")
    header_params = {'Authorization' : 'Basic %s' % user_and_pass_param, 'Content-Type' : 'application/x-www-form-urlencoded', 'Host' : 'login.eveonline.com'}
    res = requests.post('https://login.eveonline.com/v2/oauth/token', data=url_encoded, headers=header_params)
    json_content = json.loads(res.content)
    access_token = json_content['access_token']
    refresh_token = json_content['refresh_token']
    return ""

if CSECommon.SHOULD_AUTHORIZE:
    webbrowser.open('https://login.eveonline.com/v2/oauth/authorize?response_type=code&redirect_uri=http://127.0.0.1:5000/auth&client_id=' + CLIENT_ID + '&scope=publicData&state=KomissarTest')

server.m_LoopQueue = multiprocessing.Queue()
server.m_LoopProcess = multiprocessing.Process(target=CSEServerLoop.Main, args=(server.m_LoopQueue,))
server.m_LoopProcess.start()
print("CSEServer STARTED SERVER LOOP")

#CSEScraper.Init()
#g_MapModel = CSEMapModel.CSEMapModel()
#g_MapModel.CreateFromScrape(CSEScraper.CurrentScrape)
#print("Server Init Done")