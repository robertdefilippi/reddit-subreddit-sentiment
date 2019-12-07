import os
import sys

import psycopg2
import datetime
import yaml

"""Database Manager

Performs the CRUD methods on the database.
"""


class DBConnect:

    _instance = None
    _path = 'config.yml'

    def __new__(cls):
        """
        Makes sure there is only a single instance of the connection.
        """
        if DBConnect._instance is None:
            DBConnect._instance = object.__new__(cls)
        return DBConnect._instance

    def __init__(self):
        self._host = None
        self._username = None
        self._password = None
        self._port = None
        self._dbname = None
        self._conn = None
        self._config = None
        self._curr = None

    def get_credentials(self):
        """
        Get the database credentials.
        """
        if os.path.exists(self._path):
            with open(self._path, 'r') as config_file:
                yaml_loader = yaml.load(config_file, Loader=yaml.BaseLoader)
            self._config = yaml_loader['postgresql']

        else:
            print(f"The path {self._path} does not exist.")

    def set_credentials(self):
        """
        Set the credentials on self.
        """
        self._host = self._config.get('host')
        self._username = self._config.get('username')
        self._password = self._config.get('password')
        self._port = self._config.get('part')
        self._dbname = self._config.get('database')

    def get_connection(self):
        """
        Check if there is a connection, and if there is done create one.
        """
        try:
            if(self._conn is None):
                self._conn = psycopg2.connect(dbname=self._dbname,
                                              user=self._username, password=self._password,
                                              host=self._host, port=self._port, sslmode='require')
        except psycopg2.DatabaseError as e:
            print(f"Error: {e}")
            sys.exit()

        finally:
            print('Connection opened successfully.')

    def set_credentials_and_connections(self):
        """
        Perform the set up tasks for the database.
        """
        if(self._conn is None):
            self.get_credentials()
            self.set_credentials()
            self.get_connection()

    def close_connection(self):
        """
        Close the connection to the database.
        """
        self._conn.close()

    def write_record(self, post_ts: str, subreddit: str, post_title: str, score_negative: str, score_neutral: str, score_positive: str, score_compound: str) -> None:
        """
        Write a single record to the data base

        Args:
            post_ts (str): Time stamp of when the post was captured from Reddit
            subreddit (str): Subreddit name
            post_title (str): Post title from the subreddit
            score_negative (str): Negative score from the sentiment scorer
            score_neutral (str): Neutral score from the sentiment scorer
            score_positive (str): Positive score from the sentiment scorer
            score_compound (str): Compoud score from the sentiment scorer
        """
        cur = self._conn.cursor()
        cur.execute("INSERT INTO sentiment (post_ts, subreddit, post_title, score_negative, score_neutral, score_positive, score_compound) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (post_ts,
                     subreddit,
                     post_title,
                     score_negative,
                     score_neutral,
                     score_positive,
                     score_compound))
        self._conn.commit()

    def write_bulk(self, data):
        """
        Bulk write record to the database.

        Args:
            post_ts (str): Time stamp of when the post was captured from Reddit
            subreddit (str): Subreddit name
            post_title (str): Post title from the subreddit
            score_negative (str): Negative score from the sentiment scorer
            score_neutral (str): Neutral score from the sentiment scorer
            score_positive (str): Positive score from the sentiment scorer
            score_compound (str): Compoud score from the sentiment scorer
        """
        cur = self._conn.cursor()
        args_str = ','.join(cur.mogrify(
            "(%s,%s,%s,%s,%s,%s,%s)", row).decode('utf-8') for row in data)
        sql = f"INSERT INTO sentiment (post_ts, subreddit, post_title, score_negative, score_neutral, score_positive, score_compound) VALUES {args_str}"
        cur.execute(sql)
        self._conn.commit()

    def did_write_this_hour(self) -> bool:
        """
        Check if there has been a database write within the last hour.

        Returns:
            value_to_return (bool): Returns true if there has been a
            write, flase if there has not been a write.
        """

        value_to_return = None

        cur = self._conn.cursor()
        cur.execute("SELECT MAX(post_ts) FROM sentiment")
        datetime_list = [i for i in cur.fetchone()]
        max_datetime = datetime_list[0]

        current_datetime = datetime.datetime.today()
        current_hour = current_datetime.hour
        current_day = current_datetime.day

        is_same_hour = max_datetime.hour == current_hour
        is_same_day = max_datetime.day == current_day

        if is_same_hour and is_same_day:
            value_to_return = True
        else:
            value_to_return = False

        return value_to_return

    def remove_duplicates(self) -> None:
        """
        Remove duplicate entries from the database.
        """

        query_string = f"""    
        DELETE FROM sentiment a USING (
        
            SELECT 
                MIN(post_ts) as post_ts,
                post_title
            
            FROM sentiment
            
            GROUP BY 
            post_title HAVING COUNT(*) > 1) b
      
        WHERE 
            a.post_title = b.post_title
            AND a.post_ts <> b.post_ts
        """

        cur = self._conn.cursor()
        cur.execute(query_string)
        self._conn.commit()
        cur.close()

    def get_histogram_data(self, subreddit_name: str):
        """
        Get the binned and normalized data for the histogram

        Args:
            subreddit_name (str): the name the subreddit the data
            should come from.

        Returns:
            normalized_data_values (list)
            data_labels (list) 
            subreddit_name (str)

        """

        data_values = []
        data_labels = []

        query_string = f"""    
            WITH cte_scores AS (
            SELECT
                width_bucket(score_compound * 100, -110, 100, 21) - 12 AS buckets,
                count(*) AS cnt

            FROM sentiment

            WHERE
                subreddit = ('{subreddit_name}')
                AND score_compound != 0

            GROUP BY
                buckets

            ORDER BY
                buckets
            )

            SELECT
            series AS buckets,
            coalesce(cnt, 0) as bucket_count

            FROM generate_series(-10, 10) series
            LEFT JOIN cte_scores ON cte_scores.buckets = series"""

        cur = self._conn.cursor()
        cur.execute(query_string)
        result_set = cur.fetchall()

        for row in result_set:
            data_labels.append(row[0])
            data_values.append(row[1])

        data_values_total = sum(data_values)

        normalized_data_values = [x / data_values_total for x in data_values]

        return normalized_data_values, data_labels, subreddit_name

    def get_unique_categories(self) -> list:
        """
        Get a list of all the subreddits in the database.

        Returns:
            data_labels (list)
        """

        data_labels = ['all']

        query_string = f"""    
            SELECT DISTINCT subreddit

            FROM sentiment

            WHERE
                subreddit != 'all'

            ORDER BY
                subreddit
            """

        cur = self._conn.cursor()
        cur.execute(query_string)
        result_set = cur.fetchall()

        for row in result_set:
            data_labels.append(row[0])

        return data_labels

    def get_random_rows(self, subreddit_name: str) -> list:
        """
        Get random rows from a sub reddit to populate a
        table in the app.

        Args:
            subreddit_name (str): The subreddit to get the rows from

        Return:
            random_rows (list): A list of rows to generate
        """

        random_rows = []

        query_string = f"""    
            SELECT
                subreddit,
                post_title,
                score_negative,
                score_neutral,
                score_positive,
                score_compound

            FROM 
                sentiment
            
            WHERE 
                subreddit = ('{subreddit_name}')
            
            ORDER BY 
                random()
            
            LIMIT 3;
            """

        cur = self._conn.cursor()
        cur.execute(query_string)
        result_set = cur.fetchall()

        for row in result_set:
            random_rows.append(
                [row[0], row[1], row[2], row[3], row[4], row[5]])

        return random_rows

    def get_card_counts(self, subreddit_name: str) -> list:
        """
        Get counts for the cards at the top of the app.

        Args:
            subreddit_name (str): The subreddit to get specific counts from
            for each of the cards

        Return:
            data_results (list): A list counts for the cards
        """
        data_results = []

        # New posts
        query_string = f"""    
        SELECT
            COUNT(*) AS cnt

        FROM sentiment

        WHERE 
            subreddit = ('{subreddit_name}')
            AND post_ts = (SELECT MAX(post_ts) FROM sentiment)
        """

        cur = self._conn.cursor()
        cur.execute(query_string)
        result_set = cur.fetchall()

        [data_results.append(row) for row in result_set]

        # Total subreddits
        query_string = f"""    
        SELECT
            COUNT(*) AS cnt

        FROM sentiment

        WHERE subreddit = ('{subreddit_name}')
        """

        cur = self._conn.cursor()
        cur.execute(query_string)
        result_set = cur.fetchall()

        [data_results.append(row) for row in result_set]

        # Posts per subreddit
        query_string = f"""    
        SELECT
            TRUNC(COUNT(*) / COUNT(DISTINCT subreddit)::DECIMAL, 2)::VARCHAR AS cnt

        FROM sentiment;
        """

        cur = self._conn.cursor()
        cur.execute(query_string)
        result_set = cur.fetchall()

        [data_results.append(row) for row in result_set]

        # Unique subreddits
        query_string = f"""    
        SELECT
            COUNT(DISTINCT subreddit) AS cnt

        FROM sentiment;
        """

        cur = self._conn.cursor()
        cur.execute(query_string)
        result_set = cur.fetchall()

        [data_results.append(row) for row in result_set]

        return data_results

    def get_histogram_counts(self, subreddit_name: str = 'all') -> list:
        """
        Get the individual counts of positive, negative, and neutral
        scores for a specific subreddit.

        Args:
            subreddit_name (str): The subreddit to get specific counts for

        Return:
            data_results (list): A list counts for the subreddit
        """
        data_results = []

        # Posts last hour
        query_string = f"""    
        SELECT
            SUM(neg_post) AS neg_post,
            SUM(pos_post) AS pos_post,
            SUM(neu_post) AS neu_post

            FROM (

                SELECT
                CASE WHEN score_compound < -.1 THEN 1 ELSE 0 END AS neg_post,
                CASE WHEN score_compound > .1 THEN 1 ELSE 0 END AS pos_post,
                CASE WHEN score_compound BETWEEN -.1 AND .1 THEN 1 ELSE 0 END AS neu_post

                FROM sentiment
                WHERE subreddit = ('{subreddit_name}') ) AS count_subquery;
        """

        cur = self._conn.cursor()
        cur.execute(query_string)
        result_set = cur.fetchall()

        [data_results.append(row) for row in result_set]

        return data_results

    def get_total_records(self):
        """
        Get the total number of records in the database.
        """

        query_string = f"""    
        SELECT
            COUNT(*) AS cnt

        FROM sentiment
        """

        cur = self._conn.cursor()
        cur.execute(query_string)
        result_set = cur.fetchall()

        return result_set[0][0]

    def delete_oldest_two_datetime(self) -> None:
        """
        Get the oldest two datetimes, and delete all values which
        match that datetime in the database.
        """

        query_string = f"""    
        DELETE FROM 
            sentiment
        WHERE
            post_ts IN (SELECT
                            post_ts

                        FROM sentiment

                        GROUP BY
                            post_ts

                        ORDER BY
                        post_ts ASC

                        LIMIT 2)
        """

        cur = self._conn.cursor()
        cur.execute(query_string)
        self._conn.commit()
        cur.close()

    def check_if_exists(self, user_name: str) -> bool:
        """
        Check if a user exists in the database.

        Args:
            user_name (str): The user name (email) to check in the database

        Returns:
            result (bool): True if the user exists in the database, false 
            if not.
        """
        query_string = f"""    
            SELECT
                CASE WHEN user_name IS NULL
                THEN False
                ELSE True
            END AS does_exist

        FROM sentiment_users WHERE user_name = ('{user_name}')
        """

        cur = self._conn.cursor()
        cur.execute(query_string)
        result_set = cur.fetchall()

        result = True if len(result_set) > 0 else False

        return result

    def create_new_user(self, user_name: str, password: str) -> None:
        """
        Create a new user in the database if they don't already exist.

        Args:
            user_name (str): The user name (email) to use in the database
            user_name (str): The hased password to save in the database.
        """

        query_string = f"""    
            INSERT INTO  sentiment_users (user_name, password)
            
            SELECT ('{user_name}'), ('{password}') 
            
            WHERE NOT EXISTS (  SELECT  
                                    1 
                                FROM 
                                    sentiment_users 
                                WHERE 
                                    user_name = ('{user_name}')
                            )
        """

        cur = self._conn.cursor()
        cur.execute(query_string)
        self._conn.commit()
        cur.close()

    def get_user_password_hash(self, user_name: str):
        """
        Get the hashed password of the user to determine if
        if a user has inputted the correct password.
        """

        query_string = f"""    
        SELECT
            password

        FROM sentiment_users

        WHERE
            user_name = ('{user_name}')
        """

        cur = self._conn.cursor()
        cur.execute(query_string)
        result_set = cur.fetchall()

        result = result_set[0][0] if len(result_set) > 0 else None

        return result
