import create_spotify_playlist
import datetime
import praw
import pdb
import re
import toolz
from credentials import reddit_credentials

# Create the Reddit instance
reddit = praw.Reddit(
    client_id=reddit_credentials.CLIENT_ID,
    client_secret=reddit_credentials.CLIENT_SECRET,
    password=reddit_credentials.PASSWORD,
    user_agent=reddit_credentials.USER_AGENT,
    username=reddit_credentials.USERNAME
)


def response_generator(messages):
    for message in messages:
        if (isinstance(message, praw.models.Comment)):
            current_time = datetime.datetime.now()
            playlist_url = get_playlist_url(message.submission)
            if (playlist_url != ''):
                message.reply(
                    playlist_url +
                    '\n\n The link above is to a Spotify playlist featuring every video linked within this thread as of ' +
                    current_time.strftime("%A") +
                    ", " + current_time.strftime("%B %d %Y") +
                    ", " + current_time.strftime("%Y") +
                    " at " + current_time.strftime("%I") +
                    ":" + current_time.strftime("%M") +
                    " " + current_time.strftime("%p") +
                    " " + current_time.strftime("%Z") +
                    '.')


def get_playlist_url(submission):
    playlist_url = ''
    spotify_urls = extract_spotify_urls(submission.selftext) + list(
        toolz.itertoolz.unique(
            toolz.itertoolz.concat(
                extract_spotify_urls(comment.body) for comment in submission.comments
            )
        )
    )
    if (len(spotify_urls) > 0):
        playlist_url = create_spotify_playlist.create_playlist(
            submission, spotify_urls)
    return playlist_url


def extract_spotify_urls(comment):
    spotify_urls = re.findall(r"spotify\.com[^\s]*", comment, re.I)
    return spotify_urls


def reply():
    messages = list(reddit.inbox.unread())
    response_generator(messages)
    reddit.inbox.mark_read(messages)
