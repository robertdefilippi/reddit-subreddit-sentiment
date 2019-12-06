create table sentiment_users
(
	user_id serial not null
		constraint sentiment_users_pk
			primary key,
	user_name VARCHAR not null,
	password VARCHAR not null
);

