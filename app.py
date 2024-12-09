from flask import Flask, request
from helper import mongo_client

app = Flask(__name__)

def fetch_dbs(mongo_client): 
    db_collections = {}
    system_dbs = ['admin', 'local', 'config']
    dbs = []
    for db in mongo_client.list_database_names():
        if db not in system_dbs:
            dbs.append(db)
    for db in dbs:
        db_collections[db] = mongo_client[db].list_collection_names()
    return db_collections

my_dbs = fetch_dbs(mongo_client)

first_db = next(iter(my_dbs))
last_db_collection = {first_db:my_dbs[first_db][0]}

@app.route('/', methods = ['GET'])
def home():
    global last_db_collection
    if request.method == 'GET':
        db = list(last_db_collection)[0]
        collection = last_db_collection[db]

        documents = mongo_client[db][collection].find()
        documents_list = list(documents)
        
        return documents_list
