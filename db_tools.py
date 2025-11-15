import os
import sqlite3
from datetime import datetime, timedelta
from os import getenv
from sqlite3 import DatabaseError, OperationalError

from dotenv import load_dotenv

load_dotenv(".env")
FS_USER = getenv("FS_USER")


def check_subscription_end(user_id, is_proxy=0, is_vray=0):
    """
    Checks if user's subscription has ended
    """
    db_conn = SQLUtils()
    subscription_end = db_conn.query(
        f"select subscription_end from users where user_id={user_id} "
        f"and is_proxy={is_proxy} and is_vray={is_vray};"
    )
    return subscription_end


def get_all_users():
    """
    Gets all users from the database
    """
    db_conn = SQLUtils()
    all_users = db_conn.query("select user_id from users;")
    return all_users


def check_all_subscriptions():
    """
    Checks all subscriptions
    """
    db_conn = SQLUtils()
    subscriptions_end_vpn = db_conn.query(
        "select obfuscated_user from users where subscription_end <= date('now') "
        "and is_proxy=0 and is_vray=0;"
    )
    subscriptions_ends_tomorrow_users_vpn = db_conn.query(
        """select user_id from users where subscription_end >= date('now', '+1 day') 
            and subscription_end < date('now', '+2 day') 
            and is_proxy=0 and is_vray=0;"""
    )
    subscriptions_end_proxy = db_conn.query(
        "select obfuscated_user from users where subscription_end <= date('now')"
        "and is_proxy=1 and is_vray=0;"
    )
    subscriptions_ends_tomorrow_users_proxy = db_conn.query(
        """select user_id from users where subscription_end >= date('now', '+1 day') 
            and subscription_end < date('now', '+2 day') 
            and is_proxy=1 and is_vray=0;"""
    )
    subscriptions_end_vray = db_conn.query(
        "select obfuscated_user from users where subscription_end <= date('now') "
        "and is_proxy=0 and is_vray=1;"
    )
    subscriptions_ends_tomorrow_users_vray = db_conn.query(
        """select user_id from users where subscription_end >= date('now', '+1 day') 
            and subscription_end < date('now', '+2 day')
            and is_proxy=0 and is_vray=1;"""
    )
    return (
        subscriptions_end_vpn,
        subscriptions_end_proxy,
        subscriptions_ends_tomorrow_users_vpn,
        subscriptions_ends_tomorrow_users_proxy,
        subscriptions_end_vray,
        subscriptions_ends_tomorrow_users_vray,
    )


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


def delete_user_subscription(user_id, is_proxy=0, is_vray=0):
    """
    Deletes user subscription from the database
    """
    db_conn = SQLUtils()
    db_conn.mutate(
        f"delete from users where user_id={user_id} "
        f"and is_proxy={is_proxy} and is_vray={is_vray};"
    )


def need_to_update_user(user_id, obfuscated_user, invoice_payload):
    """
    Returns True if user exists in the database and False if not
    and updates user's subscription end date if exists,
    otherwise inserts new user with subscription end date
    """
    db_conn = SQLUtils()
    cur_datetime = datetime.now()

    subscription_type = invoice_payload.split("_")[0]
    prolongation = int(invoice_payload.split("_")[1])

    is_proxy = 1 if subscription_type == "proxy" else 0
    is_vray = 1 if subscription_type == "vray" else 0
    user_exist = db_conn.query(
        f"select count(*) from users where user_id={user_id} "
        f"and is_proxy={is_proxy} and is_vray={is_vray};"
    )
    if user_exist:
        end_of_period = datetime.fromisoformat(
            check_subscription_end(user_id, is_proxy=is_proxy, is_vray=is_vray)
        ) + timedelta(days=prolongation)
        db_conn.mutate(
            f"""update users set subscription_end='{end_of_period}'
                where user_id={user_id} and is_proxy={is_proxy} and is_vray={is_vray};"""
        )
        return True
    end_of_period = cur_datetime + timedelta(days=prolongation)
    db_conn.mutate(
        f"""insert into users
            (id, user_id, obfuscated_user, subscription_start, subscription_end, is_proxy, is_vray)
            values ((select max(id)+1 from users), '{user_id}', '{obfuscated_user}',
            '{cur_datetime}', '{end_of_period}', {is_proxy}, {is_vray});"""
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
