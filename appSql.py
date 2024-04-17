from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from youtube_comments import fetch_youtube_comments, analyze_sentiment, process_video_comments, generate_wordcloud, yt_title, get_transcription, generate_blog_from_transcription
from hashlib import sha256
import uuid
import os
import tweepy
from textblob import TextBlob
from instagram import scrape_instagram_comments

app = Flask(__name__)

env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(f'config.{env.capitalize()}Config')

db = SQLAlchemy(app)

# Twitter API credentials
consumer_key = 'BSU7CGgjPDyySYZVIeeXuE1dz'
consumer_secret = '0tTjx2GMlGOLQYFNlhzKdygWN00Z4nZzyNVyNTDFMpScoL65cb'
access_token = '1632059572138516480-xGsA5y9bODTGf7gOXIwMwk8qs3DcIF'
access_token_secret = 'O8EjJYHL92uZx5adOVEw7M2WTvynZnAtFLIfBvZ9sl9D5'

# Authenticate with Twitter
auth = tweepy.OAuth1UserHandler(
    consumer_key, consumer_secret, access_token, access_token_secret)
api = tweepy.API(auth)


class User(db.Model):
    id = db.Column(db.String(32), primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=False)


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and sha256(password.encode("utf-8")).hexdigest() == user.password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('/auth/login.html', error='Invalid username or password')
    return render_template('auth/login.html')

# logout


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password == confirm_password:
            hashed_password = sha256(password.encode("utf-8")).hexdigest()
            new_user = User(id=uuid.uuid4().hex, username=username,
                            password=hashed_password, email=email)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        else:
            return render_template('auth/register.html', error='Passwords do not match')
    return render_template('auth/register.html')


@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('Stats/dashboard.html', username=session['username'])
    return redirect(url_for('login'))


@app.route('/analytics')
def analytics():
    if 'username' in session:
        return render_template('Stats/analytics.html', username=session['username'])
    return redirect(url_for('login'))


@app.route('/profile')
def profile():
    if 'username' in session:
        return render_template('Stats/profile.html', username=session['username'])
    return redirect(url_for('login'))


@app.route('/youtube', methods=['GET', 'POST'])
def youtube():
    if 'username' in session:
        if request.method == 'POST':
            video_url = request.form['video_url']
            # Call functions from youtube_comments module
            comments, sentiments = process_video_comments(video_url)
            # print(comments)
            positive_count = sum(
                1 for sentiment in sentiments if sentiment == 'Positive')
            negative_count = sum(
                1 for sentiment in sentiments if sentiment == 'Negative')
            neutral_count = sum(
                1 for sentiment in sentiments if sentiment == 'Neutral')
            wordcloud_img = generate_wordcloud(comments)
            title = yt_title(video_url)
            transcription = get_transcription(video_url)
            # print(transcription)
            # blog_content = generate_blog_from_transcription(transcription)
            # print(blog_content)
            return render_template('Stats/results.html', comments=comments, sentiments=sentiments, positive_count=positive_count, negative_count=negative_count, neutral_count=neutral_count, title=title, wordcloud_img=wordcloud_img, transcription=transcription)
            # , summary=blog_content
        return render_template('Stats/youtube.html', username=session['username'])
        # return render_template('Stats/youtube.html', username=session['username'])
    return redirect(url_for('login'))


@app.route('/twitter', methods=['GET', 'POST'])
def twitter():
    if 'username' in session:
        if request.method == 'POST':
            # Get the Twitter username from the form
            username = request.form['username']

            # Fetch user's tweets
            tweets = api.user_timeline(screen_name=username, count=10)

            # Perform sentiment analysis
            analyzed_tweets = []
            for tweet in tweets:
                analysis = TextBlob(tweet.text)
                sentiment = 'positive' if analysis.sentiment.polarity > 0 else 'negative' if analysis.sentiment.polarity < 0 else 'neutral'
                analyzed_tweets.append((tweet.text, sentiment))

            # Render template with analyzed tweets
            return render_template('twitter_result.html', tweets=analyzed_tweets)
        return render_template('Stats/twitter.html', username=session['username'])
    else:
        return redirect(url_for('login'))


@app.route('/ticket')
def ticket():
    if 'username' in session:
        return render_template('Stats/tickets.html', username=session['username'])
    return redirect(url_for('login'))


@app.route('/instagram', methods=['GET', 'POST'])
def instagram():
    if 'username' in session:
        if request.method == 'POST':
            insta_url = request.form['insta_url']
            # Call functions from youtube_comments module
            comments = scrape_instagram_comments(insta_url)
            # print(comments)
            sentiments = analyze_sentiment(comments)
            positive_count = sum(
                1 for sentiment in sentiments if sentiment == 'Positive')
            negative_count = sum(
                1 for sentiment in sentiments if sentiment == 'Negative')
            neutral_count = sum(
                1 for sentiment in sentiments if sentiment == 'Neutral')
            wordcloud_img = generate_wordcloud(comments)
            return render_template('Stats/instagram_result.html', comments=comments, sentiments=sentiments, positive_count=positive_count, negative_count=negative_count, neutral_count=neutral_count, wordcloud_img=wordcloud_img)
        return render_template('Stats/instagram.html', username=session['username'])
        # return render_template('Stats/youtube.html', username=session['username'])
    return redirect(url_for('login'))


@app.route('/about')
def about():
    if 'username' in session:
        return render_template('Stats/about.html', username=session['username'])
    return redirect(url_for('login'))


@app.route('/settings')
def settings():
    if 'username' in session:
        return render_template('Stats/settings.html', username=session['username'])
    return redirect(url_for('login'))


@app.route('/contact')
def contact():
    if 'username' in session:
        return render_template('Stats/contact.html', username=session['username'])
    return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
