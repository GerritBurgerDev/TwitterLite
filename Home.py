from flask import *
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from hashlib import md5
from werkzeug import secure_filename
import os
import Neotest
import string
import datetime
import time
import re
import string
import graphdata

UPLOAD_FOLDER = './static/img/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
Bootstrap(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/D3.html')
def D3():
    graphdata.run()
    return render_template('D3.html')

@app.route('/sign-up.html',methods=['GET','POST'])
def signup():

    error = None
    if request.method == 'POST':
        username = request.form['username']
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        comfirm_password = request.form['confirm_password']
        answer = request.form['answer']
        gender = request.form['gender']


        if (password != comfirm_password):
            error = 'Passwords do not match'
        elif len(username) < 1:
            error = 'Enter username'
        elif len(full_name) < 1:
            error = 'Enter full name'
        elif len(email) < 1:
            error = 'Enter email'
        elif len(answer) < 1:
            error = 'Enter answer'
        else:
            upper = re.search(r"[A-Z]", password)
            lower = re.search(r"[a-z]", password)
            digit = re.search(r"[0-9]", password)

            if len(password) < 8:
                error = "Your password must be at least 8 characters long."
                return render_template('sign-up.html', error=error)

            if upper == None:
                error = "Your password must contain an uppercase letter."
                return render_template('sign-up.html', error=error)

            if lower == None:
                error = "Your password must contain a lowercase letter."
                return render_template('sign-up.html', error=error)

            if digit == None:
                error = "Your password must contain a digit."
                return render_template('sign-up.html', error=error)

            try:
                Neotest.register_user(username,full_name,password,email,phone,answer, "None")
                session['username'] = username
            except:
                error = "User already excists"
                return render_template('sign-up.html', error=error)
            flash("YA LOGGED IN BRA")
            return redirect(url_for('home'))


    return render_template('sign-up.html', error=error)

@app.route('/login.html',methods=['GET','POST'])
def login():

    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if Neotest.login(username,password) == False :
            error = "Username/Password was incorrect"
        else:
            session['username'] = username
            return redirect(url_for('home'))

    return render_template('login.html', error=error)

@app.route('/home.html', methods=['GET','POST'])
def home():
    username = session['username']
    user = Neotest.get_user(username)
    email = Neotest.get_email(username)
    bio = Neotest.get_bio(username)

    followers = Neotest.count_followers(username)
    following = Neotest.count_following(username)
    current_time = datetime.datetime.now()
    suggested_users, suggested_users_avatars = Neotest.get_suggested_users(username)
    num_suggested_users = len(suggested_users)

    get_followers, get_followers_avatars = Neotest.get_followers(username)
    get_following, get_following_avatars = Neotest.get_following(username)

    hashtags = Neotest.get_trending_hashtag()
    num_hashtags = len(hashtags)

    get_file = "static/img/" + username + ".png"

    if os.path.isfile(get_file):
        avatar = get_file
        Neotest.update_avatar(username,avatar)
    else:
        digest = md5(email.lower().encode('utf-8')).hexdigest()
        avatar = 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, 200)

    tweets, tweets_users, times,full_names, days, hours, mins, tweet_avatars, id = Neotest.get_tweets(username)

    check_likes = []
    likes = []
    num = len(id)

    for i in range(0, num):
        likes.append(Neotest.count_likes(id[i]))
        check_likes.append(Neotest.check_for_like(username, id[i]))

    like_unlike = []
    for i in range(0, len(check_likes)):
        if check_likes[i] == 0:
            like_unlike.append("Like")
        else:
            like_unlike.append("Unlike")

    if request.method == 'POST':
        tweet = request.form['tweet']
        if len(tweet) > 1:
            user = session['username']
            Neotest.create_tweet(user,tweet)

    return render_template('home.html', user=user, avatar=avatar, bio=bio, followers=followers, following=following,tweets = tweets,tweets_users = tweets_users,times = times,full_names=full_names,days=days,hours=hours,mins=mins,num=num,tweet_avatars=tweet_avatars,id=id,suggested_users=suggested_users, suggested_users_avatars=suggested_users_avatars, num_suggested_users=num_suggested_users, likes=likes, like_unlike=like_unlike, get_followers=get_followers, get_followers_avatars=get_followers_avatars, get_following=get_following, get_following_avatars=get_following_avatars, hashtags=hashtags, num_hashtags=num_hashtags)

@app.route('/user.html', methods=['GET', 'POST'])
def user():
    current_time = datetime.datetime.now()

    if request.method == 'POST':
        username = session['username']
        result = request.form.get('user')
        user = Neotest.get_user(result)
        email = Neotest.get_email(result)
        followers = Neotest.count_followers(result)
        following = Neotest.count_following(result)
        is_following = 0

        get_followers, get_followers_avatars = Neotest.get_followers(result)
        get_following, get_following_avatars = Neotest.get_following(result)

        check_follow = Neotest.check_follow(username, result)

        if check_follow == 1:
            is_following = 1

        suggested_users, suggested_users_avatars = Neotest.get_suggested_users(session['username'])
        num_suggested_users = len(suggested_users)

        tweets, days, hours, mins, id = Neotest.get_own_tweets(result)

        retweets, retweet_users, retweet_times, retweet_days, retweet_hours, retweet_mins, retweet_avatars, retweet_fullnames, retweet_ids = Neotest.get_retweets(username)

        num_retweets = len(retweets)

        check_likes = []
        likes = []
        num = len(tweets)

        for i in range(0, num):
            likes.append(Neotest.count_likes(id[i]))
            check_likes.append(Neotest.check_for_like(username, id[i]))

        for i in range(0, num_retweets):
            likes.append(Neotest.count_likes(retweet_ids[i]))
            check_likes.append(Neotest.check_for_like(username, retweet_ids[i]))

        like_unlike = []
        for i in range(0, len(check_likes)):
            if check_likes[i] == 0:
                like_unlike.append("Like")
            else:
                like_unlike.append("Unlike")

        hashtags = Neotest.get_trending_hashtag()
        num_hashtags = len(hashtags)

        get_file = "static/img/" + result + ".png"

        if os.path.isfile(get_file):
            avatar = get_file
        else:
            digest = md5(email.lower().encode('utf-8')).hexdigest()
            avatar = 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, 200)

        return render_template('user.html', user=user, avatar=avatar, followers=followers, following=following, tweets=tweets, days=days, hours=hours, mins=mins, num=num, suggested_users=suggested_users, suggested_users_avatars=suggested_users_avatars, num_suggested_users=num_suggested_users, likes=likes, like_unlike=like_unlike, num_retweets=num_retweets, retweets=retweets, retweet_users=retweet_users, retweet_times=retweet_times, retweet_days=retweet_days, retweet_hours=retweet_hours, retweet_mins=retweet_mins, retweet_avatars=retweet_avatars, retweet_fullnames=retweet_fullnames, is_following=is_following, get_followers=get_followers, get_followers_avatars=get_followers_avatars, get_following=get_following, get_following_avatars=get_following_avatars, retweet_ids=retweet_ids, id=id, hashtags=hashtags, num_hashtags=num_hashtags)

@app.route('/')
def logout():
    session.pop('username', None)
    return render_template(url_for('index'))

@app.route('/like', methods=['POST'])
def like():
    username = session['username']
    tweet_id = request.form['tweet']

    num = Neotest.check_for_like(username, tweet_id)

    if num == 0:
        Neotest.like(username, tweet_id)
        Neotest.update_likes(tweet_id)
    else:
        Neotest.unlike(username, tweet_id)

    return jsonify({'error' : 'not needed'})

@app.route('/share', methods=['POST'])
def share():
    username = session['username']
    tweet = request.form['tweet']

    Neotest.retweet(username, tweet)

    return jsonify({'error' : 'not needed'})

@app.route('/post', methods=['POST'])
def post():
    username = session['username']
    tweet = request.form['tweet']

    if tweet:
        Neotest.create_tweet(username, tweet)

    return jsonify({'error' : 'not needed'})

@app.route('/follow', methods=['POST'])
def follow():
    username = session['username']
    other_user = request.form['name']
    user = Neotest.get_user(username)

    if other_user:
        Neotest.follow(username, other_user)

    return jsonify({'error' : 'lolol'})

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/profile.html', methods=['GET','POST'])
def profile():
    username = session['username']
    user = Neotest.get_user(username)
    email = Neotest.get_email(username)
    phone = Neotest.get_phone(username)
    password = Neotest.get_pass(username)
    bio = Neotest.get_bio(username)
    fullname = Neotest.get_fullname(username)
    num_tweets = Neotest.count_tweets(username)
    num_followers = Neotest.count_followers(username)
    num_following = Neotest.count_following(username)
    suggested_users, suggested_users_avatars = Neotest.get_suggested_users(username)
    num_suggested_users = len(suggested_users)
    tweets, days, hours, mins, id = Neotest.get_own_tweets(username)
    num = len(tweets)
    retweet_users_model,retweet_avatars_model = Neotest.get_retweet_users(username)

    retweets, retweet_users, retweet_times, retweet_days, retweet_hours, retweet_mins, retweet_avatars, retweet_fullnames, retweet_ids = Neotest.get_retweets(username)

    num_retweets_model = len(retweet_users_model)
    num_retweets = len(retweets)

    hashtags = Neotest.get_trending_hashtag()
    num_hashtags = len(hashtags)

    count_retweets_for_user = Neotest.count_retweets(username)
    count_likes_for_user = Neotest.count_likes_for_user(username)

    get_followers, get_followers_avatars = Neotest.get_followers(username)
    get_following, get_following_avatars = Neotest.get_following(username)

    check_likes = []
    likes = []

    for i in range(0, num):
        likes.append(Neotest.count_likes(id[i]))
        check_likes.append(Neotest.check_for_like(username, id[i]))

    for i in range(0, num_retweets):
        likes.append(Neotest.count_likes(retweet_ids[i]))
        check_likes.append(Neotest.check_for_like(username, retweet_ids[i]))

    like_unlike = []
    for i in range(0, len(check_likes)):
        if check_likes[i] == 0:
            like_unlike.append("Like")
        else:
            like_unlike.append("Unlike")

    get_file = "static/img/" + username + ".png"

    if os.path.isfile(get_file):
        avatar = get_file
    else:
        digest = md5(email.lower().encode('utf-8')).hexdigest()
        avatar = 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, 200)

    error = None
    success = None
    if request.method == 'POST':
        if request.form['btn'] == "SAVE":
            new_username = request.form['username']
            new_bio = request.form['bio']
            new_fullname = request.form['full_name']
            new_phone = request.form['mobile']
            new_email = request.form['email']
            new_password = request.form['password']
            new_password2 = request.form['password2']

            if len(new_username) < 1:
                new_username = username

            if len(new_bio) < 1:
                new_bio = bio

            if len(new_fullname) < 1:
                new_fullname = fullname

            if len(new_phone) < 1:
                new_phone = phone

            if len(new_email) < 1:
                new_email = email

            if len(new_password) < 1:
                new_password = password
                new_password2 = password

            if (new_password != new_password2):
                error = "Password do not match."
            else:
                success = "Successfully updated your profile."
                session['username'] = new_username
                Neotest.update_user(username, new_username, new_bio, new_fullname, new_phone, new_email, new_password)

                return render_template('profile.html',hashtags=hashtags, num_hashtags=num_hashtags, num_retweets_model=num_retweets_model,retweet_avatars_model=retweet_avatars_model,retweet_users_model=retweet_users_model, user=user, username=new_username, avatar=avatar, bio=new_bio, success=success,num_followers=num_followers,num_following=num_following,num_tweets=num_tweets,suggested_users=suggested_users, suggested_users_avatars=suggested_users_avatars, num_suggested_users=num_suggested_users, tweets=tweets, days=days, hours=hours, mins=mins, num=num, likes=likes, like_unlike=like_unlike, num_retweets=num_retweets, retweets=retweets, retweet_users=retweet_users, retweet_times=retweet_times, retweet_days=retweet_days, retweet_hours=retweet_hours, retweet_mins=retweet_mins, retweet_avatars=retweet_avatars, retweet_fullnames=retweet_fullnames, count_retweets_for_user=count_retweets_for_user, count_likes_for_user=count_likes_for_user, get_followers=get_followers, get_followers_avatars=get_followers_avatars, get_following=get_following, get_following_avatars=get_following_avatars, id=id, retweet_ids=retweet_ids)

            return render_template('profile.html',hashtags=hashtags, num_hashtags=num_hashtags, num_retweets_model=num_retweets_model,retweet_avatars_model=retweet_avatars_model,retweet_users_model=retweet_users_model, user=user, username=username, avatar=avatar, bio=bio, error=error,num_followers=num_followers,num_following=num_following,num_tweets=num_tweets,suggested_users=suggested_users, suggested_users_avatars=suggested_users_avatars,num_suggested_users=num_suggested_users,tweets=tweets, days=days, hours=hours, mins=mins, num=num, likes=likes, like_unlike=like_unlike, num_retweets=num_retweets, retweets=retweets, retweet_users=retweet_users, retweet_times=retweet_times, retweet_days=retweet_days, retweet_hours=retweet_hours, retweet_mins=retweet_mins, retweet_avatars=retweet_avatars, retweet_fullnames=retweet_fullnames, count_retweets_for_user=count_retweets_for_user, count_likes_for_user=count_likes_for_user, get_followers=get_followers, get_followers_avatars=get_followers_avatars, get_following=get_following, get_following_avatars=get_following_avatars, id=id, retweet_ids=retweet_ids)
        else:
            f = request.files['file']

            if f.filename != '' and allowed_file(f.filename):
                session['username'] = username
                filename = username + ".png"
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                success = "Profile picture updated."
                avatar = "static/img/" + filename
                return render_template('profile.html',hashtags=hashtags, num_hashtags=num_hashtags, num_retweets_model=num_retweets_model,retweet_avatars_model=retweet_avatars_model,retweet_users_model=retweet_users_model, filename=filename, user=user, username=username, avatar=avatar, bio=bio, success=success,num_followers=num_followers,num_following=num_following,num_tweets=num_tweets,suggested_users=suggested_users, suggested_users_avatars=suggested_users_avatars,num_suggested_users=num_suggested_users, tweets=tweets, days=days, hours=hours, mins=mins, num=num, likes=likes, like_unlike=like_unlike, num_retweets=num_retweets, retweets=retweets, retweet_users=retweet_users, retweet_times=retweet_times, retweet_days=retweet_days, retweet_hours=retweet_hours, retweet_mins=retweet_mins, retweet_avatars=retweet_avatars, retweet_fullnames=retweet_fullnames, count_retweets_for_user=count_retweets_for_user, count_likes_for_user=count_likes_for_user, get_followers=get_followers, get_followers_avatars=get_followers_avatars, get_following=get_following, get_following_avatars=get_following_avatars, id=id, retweet_ids=retweet_ids)
            else:
                error = "The file could not be uploaded."

        return render_template('profile.html',hashtags=hashtags, num_hashtags=num_hashtags, num_retweets_model=num_retweets_model,retweet_avatars_model=retweet_avatars_model,retweet_users_model=retweet_users_model, user=user, username=username, avatar=avatar, bio=bio, error=error,num_followers=num_followers,num_following=num_following,num_tweets=num_tweets,suggested_users=suggested_users, suggested_users_avatars=suggested_users_avatars,num_suggested_users=num_suggested_users, tweets=tweets, days=days, hours=hours, mins=mins, num=num, likes=likes, like_unlike=like_unlike, num_retweets=num_retweets, retweets=retweets, retweet_users=retweet_users, retweet_times=retweet_times, retweet_days=retweet_days, retweet_hours=retweet_hours, retweet_mins=retweet_mins, retweet_avatars=retweet_avatars, retweet_fullnames=retweet_fullnames, count_retweets_for_user=count_retweets_for_user, count_likes_for_user=count_likes_for_user, get_followers=get_followers, get_followers_avatars=get_followers_avatars, get_following=get_following, get_following_avatars=get_following_avatars, id=id, retweet_ids=retweet_ids)

    return render_template('profile.html',hashtags=hashtags, num_hashtags=num_hashtags, num_retweets_model=num_retweets_model, retweet_avatars_model=retweet_avatars_model,retweet_users_model=retweet_users_model, user=user, username=username, avatar=avatar, bio=bio, error=error,num_followers=num_followers,num_following=num_following,num_tweets=num_tweets,suggested_users=suggested_users, suggested_users_avatars=suggested_users_avatars,num_suggested_users=num_suggested_users, tweets=tweets, days=days, hours=hours, mins=mins, num=num, likes=likes, like_unlike=like_unlike, num_retweets=num_retweets, retweets=retweets, retweet_users=retweet_users, retweet_times=retweet_times, retweet_days=retweet_days, retweet_hours=retweet_hours, retweet_mins=retweet_mins, retweet_avatars=retweet_avatars, retweet_fullnames=retweet_fullnames, count_retweets_for_user=count_retweets_for_user, count_likes_for_user=count_likes_for_user, get_followers=get_followers, get_followers_avatars=get_followers_avatars, get_following=get_following, get_following_avatars=get_following_avatars, id=id, retweet_ids=retweet_ids)

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    result = request.form.get['results']
    return jsonify(matching_results=results)

@app.route('/search', methods=['POST'])
def search():
    current_time = datetime.datetime.now()
    is_following = 0

    if request.method == 'POST':
        username = session['username']
        hashtag = request.form.get('hashtag')

        check_likes = []

        if hashtag is not None:
            messages, users, days, hours, mins, likes, id = Neotest.get_hashtag_tweets(hashtag)
            num = len(messages)

            for i in range(num):
                check_likes.append(Neotest.check_for_like(username, id[i]))

            like_unlike = []
            for i in range(0, len(check_likes)):
                if check_likes[i] == 0:
                    like_unlike.append("Like")
                else:
                    like_unlike.append("Unlike")

            return render_template('hashtags.html', name=hashtag, likes=likes, num=num, messages=messages, users=users, days=days, hours=hours, mins=mins, like_unlike=like_unlike, id=id)

        name = request.form['autocomplete']
        h = name.startswith("#")
        if h is True:
            name = name[1:]
            messages, users, days, hours, mins, likes, id = Neotest.get_hashtag_tweets(name)
            num = len(messages)

            for i in range(num):
                check_likes.append(Neotest.check_for_like(username, id[i]))

            like_unlike = []
            for i in range(0, len(check_likes)):
                if check_likes[i] == 0:
                    like_unlike.append("Like")
                else:
                    like_unlike.append("Unlike")

            return render_template('hashtags.html', name=name, likes=likes, num=num, messages=messages, users=users, days=days, hours=hours, mins=mins, like_unlike=like_unlike, id=id)

        result = Neotest.search_user(name)

        if result is None:
            result = username

        user = Neotest.get_user(result)
        email = Neotest.get_email(result)
        followers = Neotest.count_followers(result)
        following = Neotest.count_following(result)

        hashtags = Neotest.get_trending_hashtag()
        num_hashtags = len(hashtags)

        if username == result:
            is_following = 1
        else:
            check_follow = Neotest.check_follow(username, result)

            if check_follow == 1:
                is_following = 1


        suggested_users, suggested_users_avatars = Neotest.get_suggested_users(username)
        num_suggested_users = len(suggested_users)

        tweets, days, hours, mins, id = Neotest.get_own_tweets(result)

        retweets, retweet_users, retweet_times, retweet_days, retweet_hours, retweet_mins, retweet_avatars, retweet_fullnames, retweet_ids = Neotest.get_retweets(result)

        num_retweets = len(retweets)

        get_followers, get_followers_avatars = Neotest.get_followers(result)
        get_following, get_following_avatars = Neotest.get_following(result)

        likes = []
        num = len(id)

        for i in range(0, num):
            likes.append(Neotest.count_likes(id[i]))
            check_likes.append(Neotest.check_for_like(username, id[i]))

        for i in range(0, num_retweets):
            likes.append(Neotest.count_likes(retweet_ids[i]))
            check_likes.append(Neotest.check_for_like(username, retweet_ids[i]))

        like_unlike = []
        for i in range(0, len(check_likes)):
            if check_likes[i] == 0:
                like_unlike.append("Like")
            else:
                like_unlike.append("Unlike")

        get_file = "static/img/" + result + ".png"

        if os.path.isfile(get_file):
            avatar = get_file
        else:
            digest = md5(email.lower().encode('utf-8')).hexdigest()
            avatar = 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, 200)

        return render_template('user.html', user=user, avatar=avatar, followers=followers, following=following, tweets=tweets, days=days, hours=hours, mins=mins, num=num, suggested_users=suggested_users, suggested_users_avatars=suggested_users_avatars, num_suggested_users=num_suggested_users, likes=likes, like_unlike=like_unlike, num_retweets=num_retweets, retweets=retweets, retweet_users=retweet_users, retweet_times=retweet_times, retweet_days=retweet_days, retweet_hours=retweet_hours, retweet_mins=retweet_mins, retweet_avatars=retweet_avatars, retweet_fullnames=retweet_fullnames, get_followers=get_followers, get_followers_avatars=get_followers_avatars, get_following=get_following, get_following_avatars=get_following_avatars, id=id, retweet_ids=retweet_ids, is_following=is_following, hashtags=hashtags, num_hashtags=num_hashtags)

if __name__ == "__main__":
    # Neotest.run()
    app.run(debug=True)