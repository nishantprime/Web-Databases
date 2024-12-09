import pymongo
import os

mongo_client = pymongo.MongoClient(os.getenv('mongodb'))
