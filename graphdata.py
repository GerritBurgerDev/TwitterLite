from py2neo import *
from flask import *
import json
import os

db = Graph('bolt://127.0.0.1:11001', username='neo4j', password='lol')
UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def run():
    nodes = []
    links = []
    data = {}

    results = db.run("match (n:User) return n")
    id = 1

    

    for row in results:      
        username = row.get("n").get("username")
        d = {}
        d['name'] = username
        d['label'] = count_likes_for_user(username)
        d['id'] = id
        id += 1
        nodes.append(d)

    for node in nodes:
        following = get_following(node['name'])
        for follow in following:
            d = {}
            d['source'] = node['id']
            d['type'] = "follows"
            for user in nodes:
                if (follow == user['name']):
                    d['target'] = user['id']
            links.append(d)

    data["nodes"] = nodes
    data["links"] = links
    j = json.dumps(data)

    filename = os.path.join(UPLOAD_FOLDER, 'static/data.json')
    fp = open(filename, 'w')
    print(j, file=fp)    

def get_following(username):
    users = []    

    p = db.run("match (n:User)-[f:follows]->(p:User) where n.username = \"%s\" return p" % (username))

    for row in p:
        users.append(row.get("p").get("username"))

    return users

def count_likes_for_user(username):
    num = db.evaluate("Match (p:User)-[n:like]->(q:Tweet) where q.username = \"%s\" return count(n)" % (username))
    return num

