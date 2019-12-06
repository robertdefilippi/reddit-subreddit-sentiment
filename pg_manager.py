import os
import sys

import psycopg2
import datetime
import yaml


class DBConnect:

    _instance = None
    _path = 'config.yml'

    def __new__(cls):
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
        if os.path.exists(self._path):
            with open(self._path, 'r') as config_file:
                yaml_loader = yaml.load(config_file, Loader=yaml.BaseLoader)
            self._config = yaml_loader['postgresql']

        else:
            print(f"The path {self._path} does not exist.")

    def set_credentials(self):
        self._host = self._config.get('host')
        self._username = self._config.get('username')
        self._password = self._config.get('password')
        self._port = self._config.get('part')
        self._dbname = self._config.get('database')

    def get_connection(self):
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
        if(self._conn is None):
            self.get_credentials()
            self.set_credentials()
            self.get_connection()

    def close_connection(self):
        self._conn.close()

    def write_once(self):
        cur = self._conn.cursor()
        cur.execute("INSERT INTO sentiment (post_ts, subreddit, post_title, score_negative, score_neutral, score_positive, score_compound) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (datetime.datetime.now(),
                     "foo",
                     "foo",
                     .1,
                     .2,
                     .3,
                     .4))

        cur.execute("SELECT * FROM sentiment;")
        print(cur.fetchone())
        self._conn.commit()
        cur.close()

    def write_record(self, post_ts, subreddit, post_title, score_negative, score_neutral, score_positive, score_compound):
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
        cur = self._conn.cursor()
        args_str = ','.join(cur.mogrify(
            "(%s,%s,%s,%s,%s,%s,%s)", row).decode('utf-8') for row in data)
        sql = f"INSERT INTO sentiment (post_ts, subreddit, post_title, score_negative, score_neutral, score_positive, score_compound) VALUES {args_str}"
        cur.execute(sql)
        self._conn.commit()

    def did_write_this_hour(self):
        """Returns dt object from db
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

    def remove_duplicates(self):

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

    def get_unique_categories(self):

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

    def get_random_rows(self, subreddit_name: str):

        data_labels = []

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
            data_labels.append(
                [row[0], row[1], row[2], row[3], row[4], row[5]])

        return data_labels

    def get_card_counts(self, subreddit_name: str):
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

    def get_histogram_counts(self, subreddit_name: str = 'all'):
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

        query_string = f"""    
        SELECT
            COUNT(*) AS cnt

        FROM sentiment
        """

        cur = self._conn.cursor()
        cur.execute(query_string)
        result_set = cur.fetchall()

        return result_set[0][0]

    def delete_oldest_two_datetime(self):

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

    def create_new_user(self, user_name, password):
        
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

    def get_user_password_hash(self, user_name):

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

        return result_set[0][0]
