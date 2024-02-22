import requests
import re
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import BytesIO
import base64

def generate_wordcloud(comments):
    # Convert comments list to text
    if comments==[]:
        return "nothing to cloud"
    text = ' '.join(comments)

    # Generate word cloud
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)

    # Convert word cloud to image and encode as base64
    img = BytesIO()
    wordcloud.to_image().save(img, format='PNG')
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode()

    return img_base64

# Download NLTK resources (if not already downloaded)
nltk.download('vader_lexicon')

def extract_video_id(url):
    """
    Extract the video ID from a YouTube video URL.
    """
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.match(pattern, url)
    if match:
        return match.group(1)
    else:
        return None

def fetch_youtube_comments(api_key, video_url):
    """
    Fetch comments from a YouTube video using the YouTube Data API v3.
    """
    video_id = extract_video_id(video_url)
    base_url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        'part': 'snippet',
        'videoId': video_id,
        'key': api_key,
        'maxResults': 100,
    }
    comments = []
    try:
        while True:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            for item in data['items']:
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                comments.append(comment)
            if 'nextPageToken' in data:
                params['pageToken'] = data['nextPageToken']
            else:
                break
    except requests.exceptions.RequestException as e:
        print("Error fetching comments:", e)
    return comments

def analyze_sentiment(comments):
    """
    Analyze the sentiment of the comments using NLTK's VADER sentiment analyzer.
    """
    sia = SentimentIntensityAnalyzer()
    sentiments = []
    for comment in comments:
        scores = sia.polarity_scores(comment)
        sentiment = 'Positive' if scores['compound'] > 0 else 'Negative' if scores['compound'] < 0 else 'Neutral'
        sentiments.append(sentiment)
    return sentiments

def process_video_comments(video_url):
    # Call functions from youtube_comments module
    api_key = 'AIzaSyDZiPNl_kz2QqniOQHRcRqmDoX6E4MxaIg'
    comments = fetch_youtube_comments(api_key, video_url)
    sentiments = analyze_sentiment(comments)
    # print(comments, sentiments)
    return comments, sentiments  