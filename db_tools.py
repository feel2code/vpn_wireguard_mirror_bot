import os
import sqlite3
from datetime import datetime, timedelta
from os import getenv
from sqlite3 import DatabaseError, OperationalError

from dotenv import load_dotenv

load_dotenv(".env")
FS_USER = getenv("FS_USER")


def check_subscription_end(user_id):
    """
    Checks if user's subscription has ended
    """
    db_conn = SQLUtils()
    subscription_end = db_conn.query(
        f"select subscription_end from users where user_id={user_id};"
    )
    return subscription_end


def check_all_subscriptions():
    """
    Checks all subscriptions
    """
    db_conn = SQLUtils()
    subscriptions_end = db_conn.query(
        "select obfuscated_user from users where subscription_end <= date('now');"
    )
    subscriptions_ends_tomorrow_users = db_conn.query(
        "select user_id from users where subscription_end >= date('now', '+1 day');"
    )
    return subscriptions_end, subscriptions_ends_tomorrow_users


def get_obfuscated_user_conf(user_id):
    """
    Gets obfuscated user from the database
    """
    db_conn = SQLUtils()
    obfuscated_user = db_conn.query(
        f"select obfuscated_user from users where user_id={user_id};"
    )
    if not obfuscated_user:
        return None
    return f"{obfuscated_user}.conf"


def delete_user(user_id):
    """
    Deletes user from the database
    """
    db_conn = SQLUtils()
    db_conn.mutate(f"delete from users where user_id={user_id};")


def need_to_update_user(user_id, obfuscated_user):
    """
    Returns True if user exists in the database and False if not
    and updates user's subscription end date if exists,
    otherwise inserts new user with subscription end date
    """
    db_conn = SQLUtils()
    user_exist = db_conn.query(f"select count(*) from users where user_id={user_id};")
    cur_datetime = datetime.now()
    end_of_period = cur_datetime + timedelta(days=30)
    if user_exist:
        end_of_period = datetime.fromisoformat(
            check_subscription_end(user_id)
        ) + timedelta(days=30)
        db_conn.mutate(
            f"update users set subscription_end='{end_of_period}' where user_id={user_id};"
        )
        return True
    db_conn.mutate(
        f"""insert into users (id, user_id, obfuscated_user, subscription_start, subscription_end)
            values ((select max(id)+1 from users), '{user_id}', '{obfuscated_user}',
            '{cur_datetime}', '{end_of_period}');"""
    )
    return False


class SQLUtils:
    """
    Class for working with SQLite database
    """

    conn = None

    def connect(self):
        """Connects to the database"""
        self.conn = sqlite3.connect(
            f'/{FS_USER}/vpn_wireguard_mirror_bot/{os.getenv("DB_NAME")}.db'
        )

    def query(self, request):
        """Executes query"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(request)
        except (AttributeError, DatabaseError, OperationalError):
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute(request)
        fetched = cursor.fetchall()
        if len(fetched) == 1:
            if len(fetched[0]) == 1:
                return fetched[0][0]
            return fetched[0]
        if len(fetched) > 1 and len(fetched[0]) == 1:
            return [x[0] for x in fetched]
        return fetched

    def mutate(self, request):
        """Executes mutation"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(request)
            self.conn.commit()
        except (AttributeError, DatabaseError, OperationalError):
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute(request)
            self.conn.commit()
        return cursor
