create table sentiment
(
  id serial NOT NULL,
  post_ts timestamp NOT NULL,
  subreddit VARCHAR NOT NULL,
  post_title VARCHAR NOT NULL,
  score_negative FLOAT NOT NULL,
  score_neutral FLOAT NOT NULL,
  score_positive FLOAT NOT NULL,
  score_compound FLOAT NOT NULL
);

create unique index sent_2_id_uindex
	on sent_2 (id);

