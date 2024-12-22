from flask import Flask, request, session, render_template, jsonify
from helper.database import mongo_client
from bson import ObjectId
import os

app = Flask(__name__)
app.secret_key = 'top_secret_key'

password = os.getenv('password')

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

db_collection_map = fetch_dbs(mongo_client)

default_db = 'chat'
#{next(iter(db_collection_map))}
default_collection = 'log'
#{list(db_collection_map[default_db])[0]}

@app.route('/', methods = ['GET'])
def home():
        
    if selected_db_collection not in session:
        session['selected_db_collection'] = f"{default_db}/{default_collection}"

    if request.method == 'POST':
        db, collection = request.form.get('db_collection').split('/')

        if db in selected_db_collection and collection in selected_db_collection[db]:
            session['selected_db_collection'] = f'{db}/{collection}'
        else:
            session['selected_db_collection'] = f"{default_db}/{default_collection}"
            
    db, collection = session['selected_db_collection'].split('/')
        
    documents = mongo_client[db][collection].find()
    documents_list = list(documents)
    
    return render_template('database.html', db_collection_map=db_collection_map, selected_db=db, selected_collection=collection, documents=documents_list)

@app.route('/delete/<string:document_id>', methods = ['DELETE'])
def delete_document(document_id):
    document_object_id = ObjectId(document_id)
    
    db, collection = session['selected_db_collection'].split('/')
    mongo_client[db][collection].delete_one({'_id':document_object_id})
    return jsonify({'success':True})

if __name__ == '__main__':
    app.run(debug=True)
