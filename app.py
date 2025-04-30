from flask import Flask, request, session, render_template, jsonify, redirect,  Response
import pymongo
import os
from bson import ObjectId, json_util
import time
import json

mongo_client = pymongo.MongoClient(os.getenv('mongodb'))

app = Flask(__name__)
app.secret_key = os.urandom(16)

password = os.getenv('password')
login_timeout = 300

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

default_db = next(iter(db_collection_map))
default_collection = db_collection_map[default_db][0]


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return """<!DOCTYPE html>
                <html>
                <head>
                    <title>Login</title>
                </head>
                <body>
                    <form method="POST">
                        <label for="password">Password:</label>
                        <input type="password" id="password" name="password"><br><br>
                        <input type="submit" value="Submit">
                    </form>
                </body>
                </html>"""
    elif request.method == 'POST': # Use elif here!
        if 'password' in request.form:
            if request.form['password'] == password:
                session['password'] = password
                session['last_login'] = time.time()
                global db_collection_map, default_db, default_collection
                db_collection_map = fetch_dbs(mongo_client)
                default_db = next(iter(db_collection_map))
                default_collection = db_collection_map[default_db][0]

                return redirect('/')
            else:
                return 'invalid password'
        else: # Handle the case when the password is not in the form
            return "No password provided"
    return "Something went wrong" # fallback return


@app.route('/', methods = ['GET', 'POST'])
def home():
    if 'password' not in session or 'last_login' not in session:
        return redirect('/login')
    if 'last_login' in session and time.time() - session['last_login'] > login_timeout:
        del session['password']
        return 'session timed out'
        
    if 'selected_db_collection' not in session:
        session['selected_db_collection'] = f"{default_db}/{default_collection}"

    if request.method == 'POST':
        db, collection = request.form.get('db_collection').split('/')

        if db in db_collection_map and collection in db_collection_map[db]:
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


@app.route('/download/<string:db_name>/<string:collection_name>')
def download_collection(db_name, collection_name):
    if 'password' not in session or 'last_login' not in session:
        return redirect('/login')
    if 'last_login' in session and time.time() - session['last_login'] > login_timeout:
        del session['password']
        return 'session timed out'
    # Validate db_name and collection_name against current map
    if db_name not in db_collection_map or collection_name not in db_collection_map.get(db_name,[]):
        return "Invalid database or collection specified.", 404

    try:
        documents = list(mongo_client[db_name][collection_name].find())
        # Use json_util to handle BSON types like ObjectId, DateTimes etc. correctly
        json_data = json_util.dumps(documents, indent=2) # indent for readability

        # Create filename
        filename = f"{db_name}_{collection_name}.json"

        return Response(
            json_data,
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    except Exception as e:
        return f"Error fetching or processing data for download: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)
