import base64
import boto3
import json
import time
import logging
from bottle import Bottle
from bottle import request
from bottle import post
from bottle import get
from bottle import response
from bottle import HTTPResponse
from datetime import datetime
from datetime import timedelta
from models import Token


__version__ = '0.1'
__app_name__ = 'Metadata Service(Serverless)'
__author__ = 'Jose Lopez'
__copyright__ = 'Copyright 2017,2018 SavingStar'
__credits__ = ["Jose Lopez"]
__maintainer__ = 'Jose Lopez'
__email__ = 'jlopez@savingstar.com'

# we need to instantiate the logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

app = Bottle(__name__)
s3 = boto3.resource('s3')
BUCKET_NAME = 'savingstar-dev-jlopez'


def newToken(ts, member):
    t = Token.Token(str(member))
    generated_token = t.getToken('POST', 'update', ts)
    return generated_token

def writeToS3(KEY, message):
    s3.Bucket(BUCKET_NAME).put_object(
    Key=KEY,
    Body=json.dumps(message))

def readFromS3(KEY):
    return json.loads(s3.Object(BUCKET_NAME, KEY).get()['Body'].read()) 

def validTokenAndTs(ts, token, member):
    timelimitvalid = time.time()-int(ts) < 5 
    validToken = str(newToken(ts, member)) == str(token)
    return timelimitvalid and validToken

@app.route('/hello')
def index():
    # return "Hola caracola!", 200
    return "Hola caracola"


# @app.route('/update', methods=['POST'])
@app.post('/update')
def upload_metadata():

    content = request.json

    # We check we are getting the right data
    if 'ts' not in content or 'token' not in content or 'member_id' not in content:
        return HTTPResponse(status=500, body=json.dumps('Invalid data'))
    requestData = content['data']
    requestDate = time.time()
    requestTs = content['ts']
    requestToken = content['token']
    requestMember = content['member_id']
    S3_KEY = str(requestMember) + '.json'
    update_advIds = False
    update_gps = False
    if 'ad_id' in requestData:
        requestAdvid = requestData['ad_id']
        update_advIds = True        
    elif 'gps' in requestData:
        requestGPS = requestData['gps']
        requestLng = requestGPS['lat']
        requestLat = requestGPS['lng']
        update_gps = True
    else:
        return HTTPResponse(status=500, body=json.dumps('Invalid data'))
    
    
    # We check if the the token and ts are correct

    if not validTokenAndTs(requestTs, requestToken, requestMember):
        return HTTPResponse(status=401, body=json.dumps('You shall not pass'))
    
        
    newMember = False
    try:
        existingData = readFromS3(S3_KEY)
    except Exception as e:
        newMember = True
        logger.info("Member does not exist in s3")

    # Updating the new or existing file
    if newMember:
        if update_advIds:
            result = {'adv_ids': [{'ad_id':requestAdvid,'ts':requestDate}], 'gps_loc':[]}
        elif update_gps:
            result = {'adv_ids':[],'gps_loc': [{'lat':requestLat, 'lng':requestLng, 'ts':requestDate}]}
    else:
        existingAdvIds = existingData['adv_ids']
        existingGps = existingData['gps_loc']
        if update_advIds:
            existingAdvIds.append({'ad_id':requestAdvid,'ts':requestDate})
        if update_gps:
            existingGps.append({'lat':requestLat, 'lng':requestLng, 'ts':requestDate})
        
        result = {'adv_ids': existingAdvIds,'gps_loc': existingGps}
    
    writeToS3(S3_KEY, result)

    return HTTPResponse(status=200, body=json.dumps('Info uploaded as expected'))
        

@app.post('/read')
def read_metadata():

    content = request.json

    if 'ts' not in content or 'token' not in content or 'member_id' not in content:
        return HTTPResponse(status=500, body=json.dumps('Invalid data'))

    requestTs = content['ts']
    requestToken = content['token']
    requestMember = content['member_id']

    if not validTokenAndTs(requestTs, requestToken, requestMember):
        return HTTPResponse(status=401, body=json.dumps('You shall not pass'))
    
    S3_KEY = str(requestMember) + '.json'

    try:
        existingData = readFromS3(S3_KEY)
    except Exception as e:
        return HTTPResponse(status=404, body=json.dumps('Unknown member'))

    return HTTPResponse(status=200, body=json.dumps(existingData))





    # We only need this for local development.
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    run(app, reloader=True, host='0.0.0.0') #, port=port)