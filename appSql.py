from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from youtube_comments import fetch_youtube_comments, analyze_sentiment, process_video_comments, generate_wordcloud, yt_title, get_transcription, generate_blog_from_transcription, calculate_confidence_level
from hashlib import sha256
from datetime import datetime
import uuid
import os
import tweepy
from textblob import TextBlob
from instagram import scrape_instagram_comments
from flask_sqlalchemy import SQLAlchemy

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


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    platform = db.Column(db.String(50), nullable=False)
    # Assuming your User model is named 'User'
    user_id = db.Column(db.String(32), db.ForeignKey(
        'user.id'), nullable=False)


class Dashboard(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.String(32), db.ForeignKey(
        'user.id'), nullable=False)


class AnalysisResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vid_url = db.Column(db.String(255), nullable=True)
    transcript = db.Column(db.String(6000), nullable=True)
    confidence_level = db.Column(db.Float, nullable=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    message = db.Column(db.Text)


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
        # def print_session_attributes():
        #     # Iterate over the session items and print each key-value pair
        #     for key, value in session.items():
        #         print(f"{key}: {value}")

        # # Call the function to print session attributes
        # print_session_attributes()
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
            total_sentiments = positive_count + negative_count + neutral_count
            confidence_count = calculate_confidence_level(
                positive_count, negative_count, total_sentiments)
            user = User.query.filter_by(username=session['username']).first()
            user_id = user.id
            # Create a new Post instance
            new_post = Post(content=video_url, timestamp=datetime.utcnow(),
                            platform="youtube", user_id=user_id)
            # Add the new post to the database session
            db.session.add(new_post)
            # Commit the session to save the changes to the database
            db.session.commit()
            new_post_id = new_post.id
            analysis_result = AnalysisResult(
                vid_url=title, transcript=transcription, confidence_level=confidence_count, post_id=new_post_id)
            db.session.add(analysis_result)
            db.session.commit()
            return render_template('Stats/results.html', comments=comments, sentiments=sentiments, positive_count=positive_count, negative_count=negative_count, neutral_count=neutral_count, title=title, wordcloud_img=wordcloud_img, transcription=transcription, username=session['username'])
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


@app.route('/history')
def history():
    if 'username' in session:
        # Fetch the user ID for the current user
        user = User.query.filter_by(username=session['username']).first()
        user_id = user.id

        # Fetch all posts and analysis results for the current user
        all_posts = Post.query.filter_by(user_id=user_id).all()
        posts_with_analysis = []

        for post in all_posts:
            analysis_result = AnalysisResult.query.filter_by(
                post_id=post.id).first()

            # Extract data from the fetched objects
            video_url = post.content
            timestamp = post.timestamp
            title = analysis_result.vid_url if analysis_result else None
            transcription = analysis_result.transcript if analysis_result else None
            confidence_level = analysis_result.confidence_level if analysis_result else None

            # Create a dictionary to store post data along with analysis result
            post_data = {
                'video_url': video_url,
                'timestamp': timestamp,
                'title': title,
                'transcription': transcription,
                'confidence_level': confidence_level
            }

            # Append the post data to the list
            posts_with_analysis.append(post_data)

        return render_template('Stats/history.html',
                               posts_with_analysis=posts_with_analysis,
                               username=session['username'])
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
            transcription = get_transcription(insta_url)
            # print(transcription)
            # blog_content = generate_blog_from_transcription(transcription)
            # print(blog_content)
            total_sentiments = positive_count + negative_count + neutral_count
            confidence_count = calculate_confidence_level(
                positive_count, negative_count, total_sentiments)
            user = User.query.filter_by(username=session['username']).first()
            user_id = user.id
            new_post = Post(content=insta_url, timestamp=datetime.utcnow(),
                            platform="Instagram", user_id=user_id)

            # Add the new post to the database session
            db.session.add(new_post)

            # Commit the session to save the changes to the database
            db.session.commit()
            new_post_id = new_post.id
            analysis_result = AnalysisResult(
                vid_url=insta_url, transcript=transcription, confidence_level=confidence_count, post_id=new_post_id)
            db.session.add(analysis_result)
            db.session.commit()
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


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Fetch form data
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Create a new feedback object
        feedback = Feedback(name=name, email=email, message=message)

        # Add feedback to the database session and commit
        db.session.add(feedback)
        db.session.commit()

        return render_template('Stats/contact.html', username=session.get('username'))
    elif 'username' in session:
        return render_template('Stats/contact.html', username=session['username'])
    return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print("An error occurred while creating tables:", str(e))
    app.run(host='0.0.0.0', debug=True)
