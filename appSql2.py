from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file, flash, get_flashed_messages
from youtube_comments import fetch_youtube_comments, analyze_sentiment, process_video_comments, generate_wordcloud, yt_title, get_transcription, generate_blog_from_transcription, calculate_confidence_level
from hashlib import sha256
from datetime import datetime
import uuid
import os
import io
import csv
import tweepy
from textblob import TextBlob
from instagram import scrape_instagram_comments
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)
# csrf = CSRFProtect(app)
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(f'config.{env.capitalize()}Config')
app.secret_key = os.urandom(24)  # Add a secret key for session management
# Database Instance
db = SQLAlchemy(app)
# migrate = Migrate(app, db)
# Twitter API credentials
consumer_key = 'BSU7CGgjPDyySYZVIeeXuE1dz'
consumer_secret = '0tTjx2GMlGOLQYFNlhzKdygWN00Z4nZzyNVyNTDFMpScoL65cb'
access_token = '1632059572138516480-xGsA5y9bODTGf7gOXIwMwk8qs3DcIF'
access_token_secret = 'O8EjJYHL92uZx5adOVEw7M2WTvynZnAtFLIfBvZ9sl9D5'

# Authenticate with Twitter
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

# User Model for Login and Authentication


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    notifications = db.Column(db.Boolean, default=False)  # Add this line
    sentiments = db.relationship('SentimentData', backref='user', lazy=True)
    posts = db.relationship('Post', backref='user', lazy=True)
    dashboards = db.relationship('Dashboard', backref='user', lazy=True)


class SentimentData(db.Model):
    __tablename__ = 'sentiments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform = db.Column(db.String(50))
    sentiment = db.Column(db.String(50))
    emotion = db.Column(db.String(50))
    date = db.Column(db.DateTime)
    location = db.Column(db.String(100))
    content = db.Column(db.Text)  # Added content field
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    vid_url = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    platform = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    analyses = db.relationship('AnalysisResult', backref='post', lazy=True)


class Dashboard(db.Model):
    __tablename__ = 'dashboards'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


class AnalysisResult(db.Model):
    __tablename__ = 'analysis_results'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=True)
    transcript = db.Column(db.String(6000), nullable=True)
    confidence_level = db.Column(db.Float, nullable=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)


class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    message = db.Column(db.Text)


# Initialize Flask-Admin
admin = Admin(app, name='Admin Panel', template_mode='bootstrap4')

# Add views for each model
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(SentimentData, db.session))
admin.add_view(ModelView(Post, db.session))
admin.add_view(ModelView(Dashboard, db.session))
admin.add_view(ModelView(AnalysisResult, db.session))
admin.add_view(ModelView(Feedback, db.session))


@app.route('/')
def index():
    return redirect(url_for('login'))

# Default Login Route


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
            return render_template('auth/login.html', error='Invalid username or password')
    return render_template('auth/login.html')

# logout


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Registration Route


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password == confirm_password:
            hashed_password = sha256(password.encode("utf-8")).hexdigest()
            new_user = User(username=username,
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
        total_sentiments = SentimentData.query.count()
        sentiment_distribution = db.session.query(SentimentData.sentiment, db.func.count(
            SentimentData.sentiment)).group_by(SentimentData.sentiment).all()
        platform_comparison = db.session.query(SentimentData.platform, db.func.count(
            SentimentData.platform)).group_by(SentimentData.platform).all()
        recent_status = SentimentData.query.order_by(
            SentimentData.date.desc()).limit(5).all()

        return render_template('Stats/dashboard.html', username=session['username'], total_sentiments=total_sentiments, sentiment_distribution=sentiment_distribution, platform_comparison=platform_comparison, recent_status=recent_status)
    return redirect(url_for('login'))


@app.route('/download-csv')
def download_csv():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Fetch the data from the database
    sentiment_data = db.session.query(SentimentData, User).join(User).all()

    # Prepare the CSV data
    data = [
        ["User", "Date", "Sentiment", "Platform", "Emotion", "Location", "Content"]
    ]
    for sentiment, user in sentiment_data:
        data.append([
            user.username,
            sentiment.date.strftime('%Y-%m-%d'),
            sentiment.sentiment,
            sentiment.platform,
            sentiment.emotion,
            sentiment.location,
            sentiment.content
        ])

    # Create a CSV file in memory
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerows(data)

    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)

    return send_file(output, mimetype='text/csv', as_attachment=True, download_name='sentiments.csv')


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
            positive_count = sum(
                1 for sentiment in sentiments if sentiment == 'Positive')
            negative_count = sum(
                1 for sentiment in sentiments if sentiment == 'Negative')
            neutral_count = sum(
                1 for sentiment in sentiments if sentiment == 'Neutral')
            wordcloud_img = generate_wordcloud(comments)
            title = yt_title(video_url)
            transcription = get_transcription(video_url)
            total_sentiments = positive_count + negative_count + neutral_count
            confidence_count = calculate_confidence_level(
                positive_count, negative_count, total_sentiments)
            user = User.query.filter_by(username=session['username']).first()
            user_id = user.id
            # Create a new Post instance
            new_post = Post(content=video_url, timestamp=datetime.utcnow(
            ), platform="youtube", user_id=user_id)
            db.session.add(new_post)
            db.session.commit()
            new_post_id = new_post.id
            analysis_result = AnalysisResult(
                vid_url=title, transcript=transcription, confidence_level=confidence_count, post_id=new_post_id)
            db.session.add(analysis_result)
            db.session.commit()

            # Update SentimentData table
            for comment, sentiment in zip(comments, sentiments):
                sentiment_data = SentimentData(
                    user_id=user_id,
                    content=comment,
                    sentiment=sentiment,
                    platform="youtube",
                    date=datetime.utcnow(),
                    post_id=new_post_id
                )
                db.session.add(sentiment_data)

            db.session.commit()
            return render_template('Stats/results.html', comments=comments, sentiments=sentiments, positive_count=positive_count, negative_count=negative_count, neutral_count=neutral_count, title=title, wordcloud_img=wordcloud_img, transcription=transcription, username=session['username'])
        return render_template('Stats/youtube.html', username=session['username'])
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
            return render_template('Stats/twitter_result.html', tweets=analyzed_tweets, username=session['username'])
        return render_template('Stats/twitter.html', username=session['username'])
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

            # Retrieve sentiment data related to the post
            positive_comments = SentimentData.query.filter_by(
                post_id=post.id, sentiment='positive').count()
            negative_comments = SentimentData.query.filter_by(
                post_id=post.id, sentiment='negative').count()
            neutral_comments = SentimentData.query.filter_by(
                post_id=post.id, sentiment='neutral').count()

            # Analyze overall sentiment
            overall_sentiment = analyze_sentiment(
                positive_comments, negative_comments, neutral_comments)

            # Extract data from the fetched objects
            video_url = post.vid_url if post else post.vid_url
            timestamp = post.timestamp
            title = analysis_result.title if analysis_result else None
            transcription = analysis_result.transcript if analysis_result else None
            confidence_level = analysis_result.confidence_level if analysis_result else None

            # Create a dictionary to store post data along with analysis result
            post_data = {
                'video_url': video_url,
                'timestamp': timestamp,
                'title': title,
                'transcription': transcription,
                'confidence_level': confidence_level,
                'positive_comments': positive_comments,
                'negative_comments': negative_comments,
                'neutral_comments': neutral_comments,
                'overall_sentiment': overall_sentiment
            }
            print(post_data)
            # Append the post data to the list
            posts_with_analysis.append(post_data)

        return render_template('Stats/history.html', posts_with_analysis=posts_with_analysis, username=session['username'])
    return redirect(url_for('login'))


def analyze_sentiment(positive, negative, neutral):
    if positive > negative and positive > neutral:
        return "Positive"
    elif negative > positive and negative > neutral:
        return "Negative"
    else:
        return "Neutral"


@app.route('/instagram', methods=['GET', 'POST'])
def instagram():
    if 'username' in session:
        if request.method == 'POST':
            insta_url = request.form['insta_url']
            # Call functions from youtube_comments module
            comments = scrape_instagram_comments(insta_url)

            sentiments = analyze_sentiment(comments)
            positive_count = sum(
                1 for sentiment in sentiments if sentiment == 'Positive')
            negative_count = sum(
                1 for sentiment in sentiments if sentiment == 'Negative')
            neutral_count = sum(
                1 for sentiment in sentiments if sentiment == 'Neutral')
            wordcloud_img = generate_wordcloud(comments)

            transcription_tuple = get_transcription(insta_url)
            if isinstance(transcription_tuple, tuple):
                transcription = transcription_tuple[0]
            else:
                transcription = transcription_tuple

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

            # Update SentimentData table
            for comment, sentiment in zip(comments, sentiments):
                sentiment_data = SentimentData(
                    user_id=user_id,
                    content=comment,
                    sentiment=sentiment,
                    platform="instagram",
                    date=datetime.utcnow(),
                    post_id=new_post_id
                )
                db.session.add(sentiment_data)

            db.session.commit()

            return render_template('Stats/instagram_result.html', comments=comments, sentiments=sentiments, positive_count=positive_count, negative_count=negative_count, neutral_count=neutral_count, wordcloud_img=wordcloud_img, username=session['username'])
        return render_template('Stats/instagram.html', username=session['username'])
    return redirect(url_for('login'))


@app.route('/about')
def about():
    if 'username' in session:
        return render_template('Stats/about.html', username=session['username'])
    return redirect(url_for('login'))


# Route to handle user settings
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'username' not in session:
        flash('Please log in to access this page', 'info')
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        notifications = request.form.get('notifications') == 'on'

        # Verify current password
        if user.password == sha256(current_password.encode('utf-8')).hexdigest():
            # Update username and email
            user.username = username
            user.email = email

            # Update password if new password is provided and matches confirm password
            if new_password and new_password == confirm_password:
                user.password = sha256(
                    new_password.encode('utf-8')).hexdigest()

            # Update notification settings
            user.notifications = notifications

            # Commit changes to the database
            db.session.commit()

            flash('Password updated successfully', 'success')
        else:
            flash('Current password is incorrect', 'danger')

        return redirect(url_for('settings'))

    return render_template('Stats/settings.html', username=user.username, email=user.email, notifications=user.notifications)


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

        # Flash success message
        flash('Thank you for your feedback! We will contact you soon.', 'success')

        # Redirect to the contact page or any other desired page
        return redirect(url_for('contact'))

    # Check if user is logged in (you can adjust this logic as per your session management)
    if 'username' in session:
        return render_template('Stats/contact.html', username=session['username'])

    # Redirect to login page if user is not logged in
    return redirect(url_for('login'))


# Starting Point
if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print("An error occurred while creating tables:", str(e))
    app.run(host='0.0.0.0', debug=True)
