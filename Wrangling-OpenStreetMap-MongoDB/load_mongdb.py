# -*- coding: utf-8 -*-
"""
Load MongoDB

@author: DWolf
"""

from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27017")
db = client.examples

with open('atlanta_buckhead_georgia.osm.json') as f:
    data = json.loads(f.read())
    db.atlanta.insert(data)
    

