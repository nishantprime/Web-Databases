from flask import Flask

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
