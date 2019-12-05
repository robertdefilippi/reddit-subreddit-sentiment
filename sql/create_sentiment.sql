CREATE TABLE sentiment (
post_ts timestamp NOT NULL,
subreddit VARCHAR NOT NULL,
post_title VARCHAR NOT NULL,
score_negative FLOAT NOT NULL,
score_neutral FLOAT NOT NULL,
score_positive FLOAT NOT NULL,
score_compound FLOAT NOT NULL);