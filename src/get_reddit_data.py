import os
import sys

import pandas as pd

import praw
from pprint import pprint

from collections import defaultdict
from datetime import datetime

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA

# Global variables

CLIENT_ID = "s6mgv6DEda9oaQ"
CLIENT_SECRET = "qYOaYTL74kczAeRaVsVR8zb3jUI"
USER_AGENT = "chef_1075"

COLUMNS = ['post_ts', 'subreddit', 'title', 'score_neg',
           'score_neu', 'score_pos', 'score_compound']

SUBREDDIT_LIST = ["all",
                  "news",
                  "AskReddit",
                  "pics",
                  "politics",
                  "AmItheAsshole",
                  "funny",
                  "videos",
                  "gaming",
                  "aww",
                  "worldnews",
                  "memes",
                  "tifu",
                  "todayilearned",
                  "nextfuckinglevel",
                  "PublicFreakout",
                  "Wellthatsucks",
                  "gifs",
                  "movies",
                  "Showerthoughts",
                  "dankmemes",
                  "trashy",
                  "freefolk",
                  "insaneparents",
                  "unpopularopinion",
                  "insanepeoplefacebook",
                  "NoStupidQuestions",
                  "nottheonion",
                  "teenagers",
                  "MurderedByWords",
                  "mildlyinteresting",
                  "starterpacks",
                  "LifeProTips",
                  "WTF",
                  "WatchPeopleDieInside",
                  "pcmasterrace",
                  "Unexpected",
                  "oddlysatisfying",
                  "Whatcouldgowrong",
                  "science",
                  "TwoXChromosomes",
                  "MaliciousCompliance",
                  "Music",
                  "dataisbeautiful",
                  "wholesomememes",
                  "facepalm",
                  "cursedcomments",
                  "worldpolitics",
                  "awfuleverything",
                  "wallstreetbets",
                  "explainlikeimfive",
                  "comedyheaven",
                  "OldSchoolCool",
                  "whatisthisthing",
                  "legaladvice",
                  "HumansBeingBros",
                  "mildlyinfuriating",
                  "Cringetopia",
                  "space",
                  "ProgrammerHumor",              
                  "ChoosingBeggars",
                  "PoliticalHumor",
                  "rareinsults",
                  "personalfinance",
                  "blessedimages",
                  "technology"]

# Check if the data exists, and if not download it
try:
    nltk.data.find('sentiment/vader_lexicon')

except LookupError:
    nltk.download('vader_lexicon')

sia = SIA()

def get_subreddit_data() -> list:
    """
    Get the different sentiment values for subreddits. The scores returned are the positive, 
    negative, neutral, and the compound score.

    The compound score is computed by summing the valence scores of each 
    word in the lexicon, adjusted according to the rules, and then normalized to 
    be between -1 (most extreme negative) and +1 (most extreme positive). 
    Calling it a 'normalized, weighted composite score' is accurate.

    The compound score is used to generate the histogram.
    
    Returns:
        list: Values to append to the database

    Example:
        get_subreddit_data()
        >> [['2019-10-01', 'all', 'Some title to look at that is positive', 0, 0.2, 0.3, 0.5]]
    """

    current_datetime = datetime.now()

    reddit = praw.Reddit(client_id=CLIENT_ID,
                         client_secret=CLIENT_SECRET,
                         user_agent=USER_AGENT)

    headlines_sentiment_list = []

    # Loop through subreddits to get their posts sentiment scores
    for subreddit in SUBREDDIT_LIST:
        try:
            for submission in reddit.subreddit(subreddit).hot(limit=15):
                pol_score = sia.polarity_scores(submission.title)
                headlines_sentiment_list.append(
                    (current_datetime, subreddit, submission.title, pol_score['neg'], pol_score['neu'], pol_score['pos'], pol_score['compound'])
                    )
        except Exception as e:
            print(
                f'Subreddit {subreddit} does not exist. Exception raise: {e}\n')
            pass

    return headlines_sentiment_list
