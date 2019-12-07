import os
import sys

import pandas as pd

import praw
from pprint import pprint

from collections import defaultdict
from datetime import datetime

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA

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

sia = SIA()

does_vader_exist = os.path.exists("data/vader_lexicon/vader_lexicon.txt")

if not does_vader_exist:
    nltk.download('vader_lexicon')

else:
    nltk.data.load("data/vader_lexicon/vader_lexicon.txt") 


# The compound score is computed by summing the valence scores of each word in the lexicon, 
# adjusted according to the rules, and then normalized to be between -1 (most extreme negative) and +1 (most extreme positive). 
# This is the most useful metric if you want a single unidimensional measure of sentiment for a given sentence. 
#  Calling it a 'normalized, weighted composite score' is accurate.


def get_subreddit_data():

    reddit = praw.Reddit(client_id=CLIENT_ID,
                         client_secret=CLIENT_SECRET,
                         user_agent=USER_AGENT)

    headlines_sentiment_list = []

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

    # df = pd.DataFrame(headlines_sentiment_list, columns=COLUMNS)

    # return df
    return headlines_sentiment_list
