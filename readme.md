![NLP](https://nlpforhackers.io/wp-content/uploads/2016/11/Sentiment-Analysis.png)

# Sentiment Analysis of Posts in Subreddits

A flask app which looks at 50 of the top subreddits on Reddit, to determine if the 'hot' posts are either positive, negative, or neutral. E.g. Are we seeing more positive posts
in `WorldNews` than we are in `todayilearned`? Or are subreddits which use more images and/or gifs, being analyzed the same as those with more text posts?

## Getting Started

Live version of the app is available [here](https://reddit-subreddit-sentiment.herokuapp.com/). To be able to access it correctly, you need to make a login for the app. Don't worry, all passwords are hashed.

## Installing

If you want to run this locally, simply:

1. Clone and download the repository
2. `$ python app.py`
3. Go to [http://127.0.0.1:5000/](http://127.0.0.1:5000/) in your browser to access the site
4. Enjoy!


## Built With

* [Flask](http://flask.palletsprojects.com/en/1.1.x/) - The web framework used
* [Heroku](https://heroku.com) - Web hosting
* [BootStrap](https://getbootstrap.com/) - CSS and templates
* [NLTK](https://www.nltk.org/api/nltk.sentiment.html) - Sentiment analysis API for posts
* [Postgres](https://www.postgresql.org/) - Database to hold posts and users


## Author

 **Robert DeFilippi** [Github](https://github.com/robertdefilippi) 

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

