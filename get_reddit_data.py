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
NOW = datetime.now()

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
                  "modernwarfare",
                  "tifu",
                  "interestingasfuck",
                  "todayilearned",
                  "BlackPeopleTwitter",
                  "nextfuckinglevel",
                  "PublicFreakout",
                  "Wellthatsucks",
                  "nba",
                  "gifs",
                  "movies",
                  "Showerthoughts",
                  "dankmemes",
                  "trashy",
                  "television",
                  "Jokes",
                  "AskMen",
                  "freefolk",
                  "insaneparents",
                  "unpopularopinion",
                  "insanepeoplefacebook",
                  "IdiotsInCars",
                  "leagueoflegends",
                  "NoStupidQuestions",
                  "nottheonion",
                  "teenagers",
                  "MurderedByWords",
                  "mildlyinteresting",
                  "starterpacks",
                  "LifeProTips",
                  "soccer",
                  "WTF",
                  "WatchPeopleDieInside",
                  "gatekeeping",
                  "pokemon",
                  "WhitePeopleTwitter",
                  "pcmasterrace",
                  "Unexpected",
                  "oddlysatisfying",
                  "Whatcouldgowrong",
                  "science",
                  "TrueOffMyChest",
                  "NintendoSwitch",
                  "Android",
                  "TwoXChromosomes",
                  "KidsAreFuckingStupid",
                  "LivestreamFail",
                  "HistoryMemes",
                  "assholedesign",
                  "Tinder",
                  "MaliciousCompliance",
                  "therewasanattempt",
                  "Music",
                  "PewdiepieSubmissions",
                  "dataisbeautiful",
                  "wholesomememes",
                  "facepalm",
                  "cursedcomments",
                  "worldpolitics",
                  "nfl",
                  "awfuleverything",
                  "wallstreetbets",
                  "MMA",
                  "iamatotalpieceofshit",
                  "explainlikeimfive",
                  "comedyheaven",
                  "OldSchoolCool",
                  "whatisthisthing",
                  "legaladvice",
                  "blursedimages",
                  "HumansBeingBros",
                  "mildlyinfuriating",
                  "Games",
                  "Cringetopia",
                  "space",
                  "ProgrammerHumor",
                  "DestinyTheGame",
                  "sex",
                  "ChoosingBeggars",
                  "PoliticalHumor",
                  "rareinsults",
                  "classicwow",
                  "personalfinance",
                  "Minecraft",
                  "instantkarma",
                  "RoastMe",
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

    reddit = praw.Reddit(client_id=CLIENT_ID,
                         client_secret=CLIENT_SECRET,
                         user_agent=USER_AGENT)

    headlines_sentiment_list = []

    # Loop through subreddits to get their posts sentiment scores
    for subreddit in SUBREDDIT_LIST:
        try:
            for submission in reddit.subreddit(subreddit).hot(limit=20):
                pol_score = sia.polarity_scores(submission.title)
                headlines_sentiment_list.append(
                    (NOW, subreddit, submission.title, pol_score['neg'], pol_score['neu'], pol_score['pos'], pol_score['compound'])
                    )
        except Exception as e:
            print(
                f'Subreddit {subreddit} does not exist. Exception raise: {e}\n')
            pass

    return headlines_sentiment_list
