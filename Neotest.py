from flask import Flask
from generation import RandomUserGeneration
from py2neo import *
from passlib.hash import bcrypt
import random
import names
import time
from datetime import *
from hashlib import md5
from werkzeug import secure_filename
import os
import json
import re

db = Graph('bolt://127.0.0.1:11001', username='neo4j', password='lol')

def delete_all():
    db.delete_all()

def new_search():
    usernames = []

    results = db.run("match (n) return n")

    for row in results:
        usernames.append(row.get("n").get("username"))

    return usernames

def register_user(username, fullname, password, email, phone, answer, bio):

    digest = md5(email.lower().encode('utf-8')).hexdigest()
    avatar = 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, 200)
    user = Node("User", username=username, fullname=fullname, password=bcrypt.encrypt(password), email=email, phone=phone, answer=answer, bio=bio, avatar=avatar)

    db.create(user)

def update_avatar(username,avatar):
    db.run("Match(n:User) where n.username = \"%s\" SET n.avatar = \"%s\"" % (username, avatar))

def create_tweet(username,message):
    hash_arr = re.findall(r"#+(?:\s|$)?[A-Za-z0-9\-\.\_]*", message)
    for i in range(len(hash_arr)):
        hash_string = hash_arr[i][1:]
        if db.nodes.match("Hashtag", hashtag=hash_string).first() is None:
            hash_node = Node("Hashtag", hashtag=hash_string, likes=0, tweets=1)
            db.create(hash_node)
        else:
            db.run("Match (h:Hashtag) where h.hashtag = \"%s\" SET h.tweets=h.tweets+1 " % (hash_string))

    tweet = Node("Tweet",username=username, message=message,time = datetime.now(), hashtags=hash_arr)
    db.create(tweet)
    relationship(username,message,"tweet")
    for j in range(len(hash_arr)):
        hash_link = hash_arr[j][1:]
        relationship(hash_link, message, "hashtag")

def relationship(fr,to,re):
    if re == "tweet":
        a = db.nodes.match("User",username=fr).first()
        b = db.nodes.match("Tweet",message=to).first()
    elif re == "hashtag":
        a = db.nodes.match("Hashtag", hashtag=fr).first()
        b = db.nodes.match("Tweet", message=to).first()
    db.create(Relationship(a,re,b))

def follow(fr,to):
    a = db.nodes.match("User", username=fr).first()
    b = db.nodes.match("User", username=to).first()
    db.create(Relationship(a, "follows", b))

def like(fr,tw):
    db.run("MATCH (t:Tweet), (n:User) where ID(t) = %s AND n.username = \"%s\" create (n)-[:like]->(t)" % (tw, fr))

def update_likes(id):
    all_hashtags = db.run("Match (t:Tweet)<-[r:hashtag]-(h:Hashtag) where ID(t) = %s return h" % (id))

    for row in all_hashtags:
        name = row.get("h").get("hashtag")
        db.run("Match (h:Hashtag) where h.hashtag = \"%s\" SET h.likes=h.likes+1 " % (name))

def retweet(fr,tw):
    db.run("MATCH (t:Tweet), (n:User) where ID(t) = %s AND n.username = \"%s\" create (n)-[:retweet]->(t)" % (tw, fr))

def get_retweet_users(username):
    usernames = []
    avatars = []

    users = db.run("MATCH (m:User)-[r:retweet]->(t:Tweet)<-[:tweet]-(n:User) where n.username = \"%s\" return m" % (username))

    for row in users:
        usernames.append(row.get("m").get("username"))
        avatars.append(row.get("m").get("avatar"))

    return usernames,avatars

def get_tweet_user(message):
    username = db.evaluate("Match (q:Tweet) where q.message = \"%s\" return (q.username)" % (message))
    return username

def get_retweets(username):
    user = db.evaluate("Match (p:User)-[n:retweet]->(q:Tweet) where p.username = \"%s\" return (q.username)" % (username))
    return user

def uniqueness(label,property):
    db.run("CREATE CONSTRAINT ON (n:User) ASSERT n.email IS UNIQUE")
    db.run("CREATE CONSTRAINT ON (n:User) ASSERT n.phone IS UNIQUE")

def login(username, password):
    str = "MATCH (n:User) where n.username = \"%s\" return n.password" % (username)
    get_password = db.evaluate(str)

    return bcrypt.verify(password, get_password)

def get_followers(username):
    users = []
    avatars = []

    p = db.run("match (n:User)<-[f:follows]-(p:User) where n.username = \"%s\" return p" % (username))

    for row in p:
        users.append(row.get("p").get("username"))

    for user in users:
        avatar = get_avatar(user)
        avatars.append(avatar)

    return users, avatars

def get_following(username):
    users = []
    avatars = []

    p = db.run("match (n:User)-[f:follows]->(p:User) where n.username = \"%s\" return p" % (username))

    for row in p:
        users.append(row.get("p").get("username"))

    for user in users:
        avatar = get_avatar(user)
        avatars.append(avatar)

    return users, avatars

def count_tweets(username):
    num = db.evaluate("Match (p:User)-[n:tweet]->(q:Tweet) where p.username = \"%s\" return count(n)" % (username))
    return num

def count_likes(id):
    num = db.evaluate("Match (p:User)-[n:like]->(q:Tweet) where ID(q) = %s return count(n)" % (id))
    return num

def check_follow(username, other_user):
    num = db.evaluate("Match (p:User)-[n:follows]->(o:User) where p.username = \"%s\" and o.username = \"%s\" return count(p)" % (username, other_user))
    return num

def count_likes_for_user(username):
    num = db.evaluate("Match (p:User)-[n:like]->(q:Tweet) where q.username = \"%s\" return count(n)" % (username))
    return num

def count_retweets(username):
    num = db.evaluate("Match (p:User)-[n:retweet]->(q:Tweet) where q.username = \"%s\" return count(n)" % (username))
    return num

def unlike(username, id):
    all_hashtags = db.run("Match (t:Tweet)<-[r:hashtag]-(h:Hashtag) where ID(t) = %s return h" % (id))

    for row in all_hashtags:
        name = row.get("h").get("hashtag")
        db.run("Match (h:Hashtag) where h.hashtag = \"%s\" SET h.likes=h.likes-1 " % (name))
    num = db.evaluate("Match (p:User)-[n:like]->(q:Tweet) where ID(q) = %s and p.username = \"%s\" delete (n)" % (id, username))

    return num

def check_for_like(username, id):
    num = db.evaluate("Match (p:User)-[n:like]->(q:Tweet) where ID(q) = %s and p.username = \"%s\" return count(n)" % (id, username))
    return num

def count_followers(username):
    num = db.evaluate("MATCH (n)<-[r:follows]-() WHERE n.username = \"%s\" RETURN Count(r)" % (username))
    return num

def count_following(username):
    num = db.evaluate("MATCH (n)-[r:follows]->() WHERE n.username = \"%s\" RETURN Count(r)" % (username))
    return num

def get_user(username):
    str = "MATCH (n:User) where n.username = \"%s\" return n" % (username)
    user = db.evaluate(str)
    return user

def update_user(username, new_username, bio, fullname, phone, email, password):
    str = "MERGE (n:User {username: \"%s\"}) SET n.username = \"%s\", n.bio = \"%s\", n.fullname = \"%s\", n.phone = \"%s\", n.email = \"%s\", n.password = \"%s\"" % (username, new_username, bio, fullname, phone, email, password)
    user = db.evaluate(str)
    return user

def get_email(username):
    str = "MATCH (n:User) where n.username = \"%s\" return n.email" % (username)
    user_email = db.evaluate(str)
    return user_email

def get_avatar(username):
    str = "MATCH (n:User) where n.username = \"%s\" return n.avatar" % (username)
    avatar = db.evaluate(str)
    return avatar

def get_bio(username):
    str = "MATCH (n:User) where n.username = \"%s\" return n.bio" % (username)
    user_bio = db.evaluate(str)
    return user_bio

def get_phone(username):
    str = "MATCH (n:User) where n.username = \"%s\" return n.phone" % (username)
    user_phone = db.evaluate(str)
    return user_phone

def get_pass(username):
    str = "MATCH (n:User) where n.username = \"%s\" return n.password" % (username)
    user_pass = db.evaluate(str)
    return user_pass

def get_fullname(username):
    str = "MATCH (n:User) where n.username = \"%s\" return n.fullname" % (username)
    user_fullname = db.evaluate(str)
    return user_fullname

def get_retweets(username):
    tweets = []
    users = []
    times = []
    days = []
    hours = []
    mins = []
    avatars = []
    fullnames = []
    ids = []
    c = db.evaluate("return datetime({timezone: 'Africa/Johannesburg'})")

    tweet = db.run("Match (t:Tweet)<-[a:retweet]-(n:User) where n.username = \"%s\" return (t) Order by t.time DESC" % (username))

    tweet_ids = db.run("Match (t:Tweet)<-[a:retweet]-(n:User) where n.username = \"%s\" return ID(t) Order by t.time DESC" % (username))

    for i in tweet_ids:
        ids.append(i.get("ID(t)"))

    for row in tweet:
        tweets.append(row.get('t').get('message'))
        users.append(row.get('t').get("username"))
        times.append(row.get("t").get("time"))
        time = row.get("t").get("time")
        res = c - time
        hours.append(abs(res.seconds // 3600))
        days.append(abs(res.days))
        mins.append(abs(res.seconds % 3600 // 60))

    for user in users:
        fullname = get_fullname(user)
        fullnames.append(fullname)
        avatar = get_avatar(user)
        avatars.append(avatar)

    return tweets, users, times, days, hours, mins, avatars, fullnames, ids

def get_tweets(username):
    tweets = []
    tweets_users = []
    times = []
    full_names = []
    days = []
    hours = []
    mins = []
    avatars = []
    id = []

    tweet = db.run("match (t:Tweet)<-[a:tweet]-(n:User)<-[r:follows]-(m:User) where m.username = \"%s\" return t Order by t.time DESC" % (username))
    tweet_user = db.run("match (t:Tweet)<-[a:tweet]-(n:User)<-[r:follows]-(m:User) where m.username = \"%s\" return n Order by t.time DESC" % (username))
    tweet_ids = db.run("match (t:Tweet)<-[a:tweet]-(n:User)<-[r:follows]-(m:User) where m.username = \"%s\" return ID(t) Order by t.time DESC" % (username))
    c = db.evaluate("return datetime({timezone: 'Africa/Johannesburg'})")

    for row in tweet_ids:
        id.append(row.get("ID(t)"))

    for row in tweet:
        tweets.append(row.get("t").get("message"))
        times.append(row.get("t").get("time"))
        time = row.get("t").get("time")
        res = c - time
        hours.append(abs(res.seconds // 3600))
        days.append(abs(res.days))
        mins.append(abs(res.seconds % 3600 // 60))

    for row in tweet_user:
        tweets_users.append(row.get("n").get("username"))
        full_names.append(row.get("n").get("fullname"))
        avatars.append(row.get("n").get("avatar"))


    return tweets, tweets_users, times, full_names, days, hours, mins, avatars, id

def get_tweet_id(message):
    i = db.evaluate("match (t:Tweet)<-[a:tweet]-(N:User) where t.message = \"%s\" return ID(t)" % (message))
    return i

def get_suggested_users(username):
    usernames = []
    avatars = []

    p = db.run("match (n:User)-[f:follows]->(p:User)-[g:follows]->(z:User) where n.username = \"%s\" AND not (n)-[:follows]->(z) AND not z.username = \"%s\" return z, size((z)-[:tweet]->(:Tweet)) as tweets, size((z)-[:tweet]->(:Tweet)<-[:like]-(:User)) as likes ORDER by likes DESC, tweets DESC" % (username,username))

    for row in p:
        name = row.get("z").get("username")
        if name not in usernames:
            usernames.append(name)
            avatars.append(row.get("z").get("avatar"))

    return usernames, avatars

def get_own_tweets(username):
    tweets = []
    days = []
    hours = []
    mins = []
    ids = []
    c = db.evaluate("return datetime({timezone: 'Africa/Johannesburg'})")

    tweet_ids = db.run("match (t:Tweet)<-[a:tweet]-(n:User) where n.username = \"%s\" return ID(t)" % (username))

    tweet = db.run("match (n:User)-[r:tweet]->(t:Tweet) where n.username = \"%s\" return t" % (username))

    for row in tweet_ids:
        ids.append(row.get("ID(t)"))

    for t in tweet:
        tweets.append(t.get("t").get("message"))
        time = t.get("t").get("time")
        res = c - time
        hours.append(abs(res.seconds // 3600))
        days.append(abs(res.days))
        mins.append(abs(res.seconds % 3600 // 60))

    return tweets, days, hours, mins, ids

def search_user(str):
    h = db.evaluate("match(n:User) where n.username =~ \".*%s.*\" return n" % (str))
    
    if h is None:
        return None
    
    return h.get('username')

def get_hashtag_tweets(hashtag):
    messages = []
    users = []
    days = []
    hours  = []
    mins = []
    likes = []
    get_ids = []

    h = db.run("match (h:Hashtag)-[:hashtag]->(t:Tweet) where h.hashtag = \"%s\" return t order by t.time DESC" % (hashtag))

    ids = db.run("match (h:Hashtag)-[:hashtag]->(t:Tweet) where h.hashtag = \"%s\" return ID(t) order by t.time DESC" % (hashtag))

    c = db.evaluate("return datetime({timezone: 'Africa/Johannesburg'})")

    for row in h:
        messages.append(row.get("t").get("message"))
        users.append(row.get("t").get("username"))
        time = row.get("t").get("time")
        res = c - time
        hours.append(abs(res.seconds // 3600))
        days.append(abs(res.days))
        mins.append(abs(res.seconds % 3600 // 60))

    for i in ids:
        likes.append(count_likes(i.get("ID(t)")))
        get_ids.append(i.get("ID(t)"))

    return messages, users, days, hours, mins, likes, get_ids

def get_trending_hashtag():
    count = 0
    hashtags = []

    all_hastags = db.run("Match (h:Hashtag) return h ORDER BY h.likes desc, h.tweets desc LIMIT 5")

    for hashtag in all_hastags:
        hashtags.append(hashtag.get("h").get("hashtag"))

    return hashtags

def update_tweet_username(username):
    db.run("match (n:User)-[:tweet]->(t:Tweet) where n.username = \"%s\" SET t.username = \"%s\"" % (username,username))

def run():

    nouns = [
        'people',
        'history',
        'way',
        'art',
        'world',
        'information',
        'map',
        'two',
        'family',
        'government',
        'health',
        'system',
        'computer',
        'meat',
        'year',
        'thanks',
        'music',
        'person',
        'reading',
        'method',
        'data',
        'food',
        'understanding',
        'theory',
        'law',
        'bird',
        'literature',
        'problem',
        'software',
        'control',
        'knowledge',
        'power',
        'ability',
        'economics',
        'love',
        'internet',
        'television',
        'science',
        'library',
        'nature',
        'fact',
        'product',
        'idea',
        'temperature',
        'investment',
        'area',
        'society',
        'activity',
        'story',
        'industry',
        'media',
        'thing',
        'oven',
        'community',
        'definition',
        'safety',
        'quality',
        'development',
        'language',
        'management',
        'player',
        'variety',
        'video',
        'week',
        'security',
        'country',
        'exam',
        'movie',
        'organization',
        'equipment',
        'physics',
        'analysis',
        'policy',
        'series',
        'thought',
        'basis',
        'boyfriend',
        'direction',
        'strategy',
        'technology',
        'army',
        'camera',
        'freedom',
        'paper',
        'environment',
        'child',
        'instance',
        'month',
        'truth',
        'marketing',
        'university',
        'writing',
        'article',
        'department',
        'difference',
        'goal',
        'news',
        'audience',
        'fishing',
        'growth',
        'income',
        'marriage',
        'user',
        'combination',
        'failure',
        'meaning',
        'medicine',
        'philosophy',
        'teacher',
        'communication',
        'night',
        'chemistry',
        'disease',
        'disk',
        'energy',
        'nation',
        'road',
        'role',
        'soup',
        'advertising',
        'location',
        'success',
        'addition',
        'apartment',
        'education',
        'math',
        'moment',
        'painting',
        'politics',
        'attention',
        'decision',
        'event',
        'property',
        'shopping',
        'student',
        'wood',
        'competition',
        'distribution',
        'entertainment',
        'office',
        'population',
        'president',
        'unit',
        'category',
        'cigarette',
        'context',
        'introduction',
        'opportunity',
        'performance',
        'driver',
        'flight',
        'length',
        'magazine',
        'newspaper',
        'relationship',
        'teaching',
        'cell',
        'dealer',
        'debate',
        'finding',
        'lake',
        'member',
        'message',
        'phone',
        'scene',
        'appearance',
        'association',
        'concept',
        'customer',
        'death',
        'discussion',
        'housing',
        'inflation',
        'insurance',
        'mood',
        'woman',
        'advice',
        'blood',
        'effort',
        'expression',
        'importance',
        'opinion',
        'payment',
        'reality',
        'responsibility',
        'situation',
        'skill',
        'statement',
        'wealth',
        'application',
        'city',
        'county',
        'depth',
        'estate',
        'foundation',
        'grandmother',
        'heart',
        'perspective',
        'photo',
        'recipe',
        'studio',
        'topic',
        'collection',
        'depression',
        'imagination',
        'passion',
        'percentage',
        'resource',
        'setting',
        'ad',
        'agency',
        'college',
        'connection',
        'criticism',
        'debt',
        'description',
        'memory',
        'patience',
        'secretary',
        'solution',
        'administration',
        'aspect',
        'attitude',
        'director',
        'personality',
        'psychology',
        'recommendation',
        'response',
        'selection',
        'storage',
        'version',
        'alcohol',
        'argument',
        'complaint',
        'contract',
        'emphasis',
        'highway',
        'loss',
        'membership',
        'possession',
        'preparation',
        'steak',
        'union',
        'agreement',
        'cancer',
        'currency',
        'employment',
        'engineering',
        'entry',
        'interaction',
        'limit',
        'mixture',
        'preference',
        'region',
        'republic',
        'seat',
        'tradition',
        'virus',
        'actor',
        'classroom',
        'delivery',
        'device',
        'difficulty',
        'drama',
        'election',
        'engine',
        'football',
        'guidance',
        'hotel',
        'match',
        'owner',
        'priority',
        'protection',
        'suggestion',
        'tension',
        'variation',
        'anxiety',
        'atmosphere',
        'awareness',
        'bread',
        'climate',
        'comparison',
        'confusion',
        'construction',
        'elevator',
        'emotion',
        'employee',
        'employer',
        'guest',
        'height',
        'leadership',
        'mall',
        'manager',
        'operation',
        'recording',
        'respect',
        'sample',
        'transportation',
        'boring',
        'charity',
        'cousin',
        'disaster',
        'editor',
        'efficiency',
        'excitement',
        'extent',
        'feedback',
        'guitar',
        'homework',
        'leader',
        'mom',
        'outcome',
        'permission',
        'presentation',
        'promotion',
        'reflection',
        'refrigerator',
        'resolution',
        'revenue',
        'session',
        'singer',
        'tennis',
        'basket',
        'bonus',
        'cabinet',
        'childhood',
        'church',
        'clothes',
        'coffee',
        'dinner',
        'drawing',
        'hair',
        'hearing',
        'initiative',
        'judgment',
        'lab',
        'measurement',
        'mode',
        'mud',
        'orange',
        'poetry',
        'police',
        'possibility',
        'procedure',
        'queen',
        'ratio',
        'relation',
        'restaurant',
        'satisfaction',
        'sector',
        'signature',
        'significance',
        'song',
        'tooth',
        'town',
        'vehicle',
        'volume',
        'wife',
        'accident',
        'airport',
        'appointment',
        'arrival',
        'assumption',
        'baseball',
        'chapter',
        'committee',
        'conversation',
        'database',
        'enthusiasm',
        'error',
        'explanation',
        'farmer',
        'gate',
        'girl',
        'hall',
        'historian',
        'hospital',
        'injury',
        'instruction',
        'maintenance',
        'manufacturer',
        'meal',
        'perception',
        'pie',
        'poem',
        'presence',
        'proposal',
        'reception',
        'replacement',
        'revolution',
        'river',
        'son',
        'speech',
        'tea',
        'village',
        'warning',
        'winner',
        'worker',
        'writer',
        'assistance',
        'breath',
        'buyer',
        'chest',
        'chocolate',
        'conclusion',
        'contribution',
        'cookie',
        'courage',
        'dad',
        'desk',
        'drawer',
        'establishment',
        'examination',
        'garbage',
        'grocery',
        'honey',
        'impression',
        'improvement',
        'independence',
        'insect',
        'inspection',
        'inspector',
        'king',
        'ladder',
        'menu',
        'penalty',
        'piano',
        'potato',
        'profession',
        'professor',
        'quantity',
        'reaction',
        'requirement',
        'salad',
        'sister',
        'supermarket',
        'tongue',
        'weakness',
        'wedding',
        'affair',
        'ambition',
        'analyst',
        'apple',
        'assignment',
        'assistant',
        'bathroom',
        'bedroom',
        'beer',
        'birthday',
        'celebration',
        'championship',
        'cheek',
        'client',
        'consequence',
        'departure',
        'diamond',
        'dirt',
        'ear',
        'fortune',
        'friendship',
        'funeral',
        'gene',
        'girlfriend',
        'hat',
        'indication',
        'intention',
        'lady',
        'midnight',
        'negotiation',
        'obligation',
        'passenger',
        'pizza',
        'platform',
        'poet',
        'pollution',
        'recognition',
        'reputation',
        'shirt',
        'sir',
        'speaker',
        'stranger',
        'surgery',
        'sympathy',
        'tale',
        'throat',
        'trainer',
        'uncle',
        'youth',
        'time',
        'work',
        'film',
        'water',
        'money',
        'example',
        'while',
        'business',
        'study',
        'game',
        'life',
        'form',
        'air',
        'day',
        'place',
        'number',
        'part',
        'field',
        'fish',
        'back',
        'process',
        'heat',
        'hand',
        'experience',
        'job',
        'book',
        'end',
        'point',
        'type',
        'home',
        'economy',
        'value',
        'body',
        'market',
        'guide',
        'interest',
        'state',
        'radio',
        'course',
        'company',
        'price',
        'size',
        'card',
        'list',
        'mind',
        'trade',
        'line',
        'care',
        'group',
        'risk',
        'word',
        'fat',
        'force',
        'key',
        'light',
        'training',
        'name',
        'school',
        'top',
        'amount',
        'level',
        'order',
        'practice',
        'research',
        'sense',
        'service',
        'piece',
        'web',
        'boss',
        'sport',
        'fun',
        'house',
        'page',
        'term',
        'test',
        'answer',
        'sound',
        'focus',
        'matter',
        'kind',
        'soil',
        'board',
        'oil',
        'picture',
        'access',
        'garden',
        'range',
        'rate',
        'reason',
        'future',
        'site',
        'demand',
        'exercise',
        'image',
        'case',
        'cause',
        'coast',
        'action',
        'age',
        'bad',
        'boat',
        'record',
        'result',
        'section',
        'building',
        'mouse',
        'cash',
        'class',
        'nothing',
        'period',
        'plan',
        'store',
        'tax',
        'side',
        'subject',
        'space',
        'rule',
        'stock',
        'weather',
        'chance',
        'figure',
        'man',
        'model',
        'source',
        'beginning',
        'earth',
        'program',
        'chicken',
        'design',
        'feature',
        'head',
        'material',
        'purpose',
        'question',
        'rock',
        'salt',
        'act',
        'birth',
        'car',
        'dog',
        'object',
        'scale',
        'sun',
        'note',
        'profit',
        'rent',
        'speed',
        'style',
        'war',
        'bank',
        'craft',
        'half',
        'inside',
        'outside',
        'standard',
        'bus',
        'exchange',
        'eye',
        'fire',
        'position',
        'pressure',
        'stress',
        'advantage',
        'benefit',
        'box',
        'frame',
        'issue',
        'step',
        'cycle',
        'face',
        'item',
        'metal',
        'paint',
        'review',
        'room',
        'screen',
        'structure',
        'view',
        'account',
        'ball',
        'discipline',
        'medium',
        'share',
        'balance',
        'bit',
        'black',
        'bottom',
        'choice',
        'gift',
        'impact',
        'machine',
        'shape',
        'tool',
        'wind',
        'address',
        'average',
        'career',
        'culture',
        'morning',
        'pot',
        'sign',
        'table',
        'task',
        'condition',
        'contact',
        'credit',
        'egg',
        'hope',
        'ice',
        'network',
        'north',
        'square',
        'attempt',
        'date',
        'effect',
        'link',
        'post',
        'star',
        'voice',
        'capital',
        'challenge',
        'friend',
        'self',
        'shot',
        'brush',
        'couple',
        'exit',
        'front',
        'function',
        'lack',
        'living',
        'plant',
        'plastic',
        'spot',
        'summer',
        'taste',
        'theme',
        'track',
        'wing',
        'brain',
        'button',
        'click',
        'desire',
        'foot',
        'gas',
        'influence',
        'notice',
        'rain',
        'wall',
        'base',
        'damage',
        'distance',
        'feeling',
        'pair',
        'savings',
        'staff',
        'sugar',
        'target',
        'text',
        'animal',
        'author',
        'budget',
        'discount',
        'file',
        'ground',
        'lesson',
        'minute',
        'officer',
        'phase',
        'reference',
        'register',
        'sky',
        'stage',
        'stick',
        'title',
        'trouble',
        'bowl',
        'bridge',
        'campaign',
        'character',
        'club',
        'edge',
        'evidence',
        'fan',
        'letter',
        'lock',
        'maximum',
        'novel',
        'option',
        'pack',
        'park',
        'plenty',
        'quarter',
        'skin',
        'sort',
        'weight',
        'baby',
        'background',
        'carry',
        'dish',
        'factor',
        'fruit',
        'glass',
        'joint',
        'master',
        'muscle',
        'red',
        'strength',
        'traffic',
        'trip',
        'vegetable',
        'appeal',
        'chart',
        'gear',
        'ideal',
        'kitchen',
        'land',
        'log',
        'mother',
        'net',
        'party',
        'principle',
        'relative',
        'sale',
        'season',
        'signal',
        'spirit',
        'street',
        'tree',
        'wave',
        'belt',
        'bench',
        'commission',
        'copy',
        'drop',
        'minimum',
        'path',
        'progress',
        'project',
        'sea',
        'south',
        'status',
        'stuff',
        'ticket',
        'tour',
        'angle',
        'blue',
        'breakfast',
        'confidence',
        'daughter',
        'degree',
        'doctor',
        'dot',
        'dream',
        'duty',
        'essay',
        'father',
        'fee',
        'finance',
        'hour',
        'juice',
        'luck',
        'milk',
        'mouth',
        'peace',
        'pipe',
        'stable',
        'storm',
        'substance',
        'team',
        'trick',
        'afternoon',
        'bat',
        'beach',
        'blank',
        'catch',
        'chain',
        'consideration',
        'cream',
        'crew',
        'detail',
        'gold',
        'interview',
        'kid',
        'mark',
        'mission',
        'pain',
        'pleasure',
        'score',
        'screw',
        'sex',
        'shop',
        'shower',
        'suit',
        'tone',
        'window',
        'agent',
        'band',
        'bath',
        'block',
        'bone',
        'calendar',
        'candidate',
        'cap',
        'coat',
        'contest',
        'corner',
        'court',
        'cup',
        'district',
        'door',
        'east',
        'finger',
        'garage',
        'guarantee',
        'hole',
        'hook',
        'implement',
        'layer',
        'lecture',
        'lie',
        'manner',
        'meeting',
        'nose',
        'parking',
        'partner',
        'profile',
        'rice',
        'routine',
        'schedule',
        'swimming',
        'telephone',
        'tip',
        'winter',
        'airline',
        'bag',
        'battle',
        'bed',
        'bill',
        'bother',
        'cake',
        'code',
        'curve',
        'designer',
        'dimension',
        'dress',
        'ease',
        'emergency',
        'evening',
        'extension',
        'farm',
        'fight',
        'gap',
        'grade',
        'holiday',
        'horror',
        'horse',
        'host',
        'husband',
        'loan',
        'mistake',
        'mountain',
        'nail',
        'noise',
        'occasion',
        'package',
        'patient',
        'pause',
        'phrase',
        'proof',
        'race',
        'relief',
        'sand',
        'sentence',
        'shoulder',
        'smoke',
        'stomach',
        'string',
        'tourist',
        'towel',
        'vacation',
        'west',
        'wheel',
        'wine',
        'arm',
        'aside',
        'associate',
        'bet',
        'blow',
        'border',
        'branch',
        'breast',
        'brother',
        'buddy',
        'bunch',
        'chip',
        'coach',
        'cross',
        'document',
        'draft',
        'dust',
        'expert',
        'floor',
        'god',
        'golf',
        'habit',
        'iron',
        'judge',
        'knife',
        'landscape',
        'league',
        'mail',
        'mess',
        'native',
        'opening',
        'parent',
        'pattern',
        'pin',
        'pool',
        'pound',
        'request',
        'salary',
        'shame',
        'shelter',
        'shoe',
        'silver',
        'tackle',
        'tank',
        'trust',
        'assist',
        'bake',
        'bar',
        'bell',
        'bike',
        'blame',
        'boy',
        'brick',
        'chair',
        'closet',
        'clue',
        'collar',
        'comment',
        'conference',
        'devil',
        'diet',
        'fear',
        'fuel',
        'glove',
        'jacket',
        'lunch',
        'monitor',
        'mortgage',
        'nurse',
        'pace',
        'panic',
        'peak',
        'plane',
        'reward',
        'row',
        'sandwich',
        'shock',
        'spite',
        'spray',
        'surprise',
        'till',
        'transition',
        'weekend',
        'welcome',
        'yard',
        'alarm',
        'bend',
        'bicycle',
        'bite',
        'blind',
        'bottle',
        'cable',
        'candle',
        'clerk',
        'cloud',
        'concert',
        'counter',
        'flower',
        'grandfather',
        'harm',
        'knee',
        'lawyer',
        'leather',
        'load',
        'mirror',
        'neck',
        'pension',
        'plate',
        'purple',
        'ruin',
        'ship',
        'skirt',
        'slice',
        'snow',
        'specialist',
        'stroke',
        'switch',
        'trash',
        'tune',
        'zone',
        'anger',
        'award',
        'bid',
        'bitter',
        'boot',
        'bug',
        'camp',
        'candy',
        'carpet',
        'cat',
        'champion',
        'channel',
        'clock',
        'comfort',
        'cow',
        'crack',
        'engineer',
        'entrance',
        'fault',
        'grass',
        'guy',
        'hell',
        'highlight',
        'incident',
        'island',
        'joke',
        'jury',
        'leg',
        'lip',
        'mate',
        'motor',
        'nerve',
        'passage',
        'pen',
        'pride',
        'priest',
        'prize',
        'promise',
        'resident',
        'resort',
        'ring',
        'roof',
        'rope',
        'sail',
        'scheme',
        'script',
        'sock',
        'station',
        'toe',
        'tower',
        'truck',
        'witness',
        'a',
        'you',
        'it',
        'can',
        'will',
        'if',
        'one',
        'many',
        'most',
        'other',
        'use',
        'make',
        'good',
        'look',
        'help',
        'go',
        'great',
        'being',
        'few',
        'might',
        'still',
        'public',
        'read',
        'keep',
        'start',
        'give',
        'human',
        'local',
        'general',
        'she',
        'specific',
        'long',
        'play',
        'feel',
        'high',
        'tonight',
        'put',
        'common',
        'set',
        'change',
        'simple',
        'past',
        'big',
        'possible',
        'particular',
        'today',
        'major',
        'personal',
        'current',
        'national',
        'cut',
        'natural',
        'physical',
        'show',
        'try',
        'check',
        'second',
        'call',
        'move',
        'pay',
        'let',
        'increase',
        'single',
        'individual',
        'turn',
        'ask',
        'buy',
        'guard',
        'hold',
        'main',
        'offer',
        'potential',
        'professional',
        'international',
        'travel',
        'cook',
        'alternative',
        'following',
        'special',
        'working',
        'whole',
        'dance',
        'excuse',
        'cold',
        'commercial',
        'low',
        'purchase',
        'deal',
        'primary',
        'worth',
        'fall',
        'necessary',
        'positive',
        'produce',
        'search',
        'present',
        'spend',
        'talk',
        'creative',
        'tell',
        'cost',
        'drive',
        'green',
        'support',
        'glad',
        'remove',
        'return',
        'run',
        'complex',
        'due',
        'effective',
        'middle',
        'regular',
        'reserve',
        'independent',
        'leave',
        'original',
        'reach',
        'rest',
        'serve',
        'watch',
        'beautiful',
        'charge',
        'active',
        'break',
        'negative',
        'safe',
        'stay',
        'visit',
        'visual',
        'affect',
        'cover',
        'report',
        'rise',
        'walk',
        'white',
        'beyond',
        'junior',
        'pick',
        'unique',
        'anything',
        'classic',
        'final',
        'lift',
        'mix',
        'private',
        'stop',
        'teach',
        'western',
        'concern',
        'familiar',
        'fly',
        'official',
        'broad',
        'comfortable',
        'gain',
        'maybe',
        'rich',
        'save',
        'stand',
        'young',
        'heavy',
        'hello',
        'lead',
        'listen',
        'valuable',
        'worry',
        'handle',
        'leading',
        'meet',
        'release',
        'sell',
        'finish',
        'normal',
        'press',
        'ride',
        'secret',
        'spread',
        'spring',
        'tough',
        'wait',
        'brown',
        'deep',
        'display',
        'flow',
        'hit',
        'objective',
        'shoot',
        'touch',
        'cancel',
        'chemical',
        'cry',
        'dump',
        'extreme',
        'push',
        'conflict',
        'eat',
        'fill',
        'formal',
        'jump',
        'kick',
        'opposite',
        'pass',
        'pitch',
        'remote',
        'total',
        'treat',
        'vast',
        'abuse',
        'beat',
        'burn',
        'deposit',
        'print',
        'raise',
        'sleep',
        'somewhere',
        'advance',
        'anywhere',
        'consist',
        'dark',
        'double',
        'draw',
        'equal',
        'fix',
        'hire',
        'internal',
        'join',
        'kill',
        'sensitive',
        'tap',
        'win',
        'attack',
        'claim',
        'constant',
        'drag',
        'drink',
        'guess',
        'minor',
        'pull',
        'raw',
        'soft',
        'solid',
        'wear',
        'weird',
        'wonder',
        'annual',
        'count',
        'dead',
        'doubt',
        'feed',
        'forever',
        'impress',
        'nobody',
        'repeat',
        'round',
        'sing',
        'slide',
        'strip',
        'whereas',
        'wish',
        'combine',
        'command',
        'dig',
        'divide',
        'equivalent',
        'hang',
        'hunt',
        'initial',
        'march',
        'mention',
        'spiritual',
        'survey',
        'tie',
        'adult',
        'brief',
        'crazy',
        'escape',
        'gather',
        'hate',
        'prior',
        'repair',
        'rough',
        'sad',
        'scratch',
        'sick',
        'strike',
        'employ',
        'external',
        'hurt',
        'illegal',
        'laugh',
        'lay',
        'mobile',
        'nasty',
        'ordinary',
        'respond',
        'royal',
        'senior',
        'split',
        'strain',
        'struggle',
        'swim',
        'train',
        'upper',
        'wash',
        'yellow',
        'convert',
        'crash',
        'dependent',
        'fold',
        'funny',
        'grab',
        'hide',
        'miss',
        'permit',
        'quote',
        'recover',
        'resolve',
        'roll',
        'sink',
        'slip',
        'spare',
        'suspect',
        'sweet',
        'swing',
        'twist',
        'upstairs',
        'usual',
        'abroad',
        'brave',
        'calm',
        'concentrate',
        'estimate',
        'grand',
        'male',
        'mine',
        'prompt',
        'quiet',
        'refuse',
        'regret',
        'reveal',
        'rush',
        'shake',
        'shift',
        'shine',
        'steal',
        'suck',
        'surround',
        'anybody',
        'bear',
        'brilliant',
        'dare',
        'dear',
        'delay',
        'drunk',
        'female',
        'hurry',
        'inevitable',
        'invite',
        'kiss',
        'neat',
        'pop',
        'punch',
        'quit',
        'reply',
        'representative',
        'resist',
        'rip',
        'rub',
        'silly',
        'smile',
        'spell',
        'stretch',
        'stupid',
        'tear',
        'temporary',
        'tomorrow',
        'wake',
        'wrap',
        'yesterday',
    ]
    all_names = []
    all_tweets = []
    all_ids = []
    delete_all()

    for i in range(0,20):
        user = RandomUserGeneration()
        all_names.append(user.get_username())
        register_user(user.get_username(), user.get_first_name() + " " + user.get_last_name(), "123", user.get_mail(), user.get_phone(), "BLAH BLAH BLAH", "None")


    for i in range(0,20):
        a = random.choice(all_names)
        message = "I " + random.choice(nouns) +" "+ random.choice(nouns)
        all_tweets.append(message)
        create_tweet(all_names[i],message)
        all_ids.append(get_tweet_id(message))
        relationship(str(all_names[i]),message,"tweet")
        b = random.choice(all_names)
        while(a == b):
            b = random.choice(all_names)
        retweet(b,get_tweet_id(message))

    for i in range(0,20):
        a = random.choice(all_names)
        b = random.choice(all_names)
        while (a == b):
            b = random.choice(all_names)
        follow(a,b)

    for i in range(0,20):
        a = random.choice(all_names)
        b = random.choice(all_ids)
        like(a,b)
