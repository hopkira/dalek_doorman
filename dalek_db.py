from cloudant.client import Cloudant
import json
import time

def get_connection():
    with open('vcap-local.json') as f:
        vcap = json.load(f)
    print('Found local VCAP_SERVICES')
    creds = vcap['services']['cloudantNoSQLDB'][0]['credentials']
    user = creds['username']
    password = creds['password']
    url = 'https://' + creds['host']
    connection = Cloudant(user, password, url=url, connect=True)
    return connection

def db_create(connection,name):
    connection.create_database(name, throw_on_exists=False)

def db_read(connection,name):
    db = connection[name]
    return db

def create_doc(db,json_str):
    db.create_document(json_str)

def read_doc(db,_id):
    document = db[_id]
    return document

def update_doc(doc,key,value):
    doc[key]=value    
    
def save_doc(doc):
    doc.save()