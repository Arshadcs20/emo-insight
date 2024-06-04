from flask import Flask, request, jsonify
import requests
import re
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
import assemblyai as aai
import openai
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from pytube import YouTube
import os


def yt_title(link):
    yt = YouTube(link)
    title = yt.title
    return title


def calculate_confidence_level(positive_count, negative_count, total_sentiments):
    if total_sentiments == 0:
        return 0.0
    confidence_level = (positive_count - negative_count) / total_sentiments
    return confidence_level


def get_transcription(youtube_url):
    try:
        # Download the audio file from the YouTube video URL
        audio_file_path = download_audio(youtube_url)
        # Transcribe the audio file
        transcription = transcribe_audio(audio_file_path)
        # print(transcription)
        return transcription
    except Exception as e:
        return str(e), 500


def download_audio(link):
    yt = YouTube(link)
    video = yt.streams.filter(only_audio=True).first()
    media_folder = 'media'
    if not os.path.exists(media_folder):
        os.makedirs(media_folder)

    filename = video.title
    filename = "".join(x for x in filename if x.isalnum()
                       or x in [" ", ".", "_"]).strip()

    file_path = os.path.join(media_folder, f"{filename}.mp3")

    if os.path.exists(file_path):
        # If the file already exists, return its path without re-downloading
        return file_path

    out_file = video.download(output_path=media_folder)
    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    os.rename(out_file, new_file)

    return new_file


def transcribe_audio(audio_file_path):
    aai.settings.api_key = "f910199c49cc45d6b3e624192105276f"
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file_path)
    return transcript.text


def generate_blog_from_transcription(transcription):
    openai.api_key = "sk-proj-BMvUb7B3n980CLPelbSDT3BlbkFJo1I550TswEN2fdVgdET1"

    prompt = f"""Based on the following transcript from a YouTube video, write a comprehensive blog article, write it based on the transcript, but don't make it look like a YouTube video, make it look like a proper blog article:

    {transcription}

    Article:"""

    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=250
    )

    generated_content = response['choices'][0]['text'].strip()

    return generated_content
    

def generate_wordcloud(comments):
    # Convert comments list to text
    if comments == []:
        return "nothing to cloud"
    text = ' '.join(comments)

    # Generate word cloud
    wordcloud = WordCloud(width=800, height=400,
                          background_color='white').generate(text)

    # Convert word cloud to image and encode as base64
    img = BytesIO()
    wordcloud.to_image().save(img, format='PNG')
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode()

    return img_base64


# Download NLTK resources(if not already downloaded)
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
