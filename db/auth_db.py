import pyotp, secrets, pymysql, bcrypt
import streamlit as st
import time
from db.setup_db import get_db_conn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DB_Utils:
    def __init__(self):
        pass

    def generate_hashed_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    def verify_password(self, password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash)

    def generate_mfa_secret(self):
        return pyotp.random_base32()

    def verify_totp(self, mfa_secret: str, totp_code: str) -> bool:
        totp = pyotp.TOTP(mfa_secret)
        return totp.verify(totp_code, valid_window=1)


class SessionManagement:
    def __init__(self):
        pass

    def create_session(self, username, role):
        session_id = secrets.token_urlsafe(32)
        created_at = int(time.time())
        conn = None
        try:
            conn = get_db_conn()
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO user_sessions (session_id, username, role, created_at) "
                    "VALUES (%s, %s, %s, %s)",
                    (session_id, username, role, created_at),
                )
                conn.commit()
            return session_id
        except pymysql.Error as e:
            print(f"Session creation error: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_session(self, session_id):
        """Retrieve session details from the database"""
        conn = None
        try:
            conn = get_db_conn()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM user_sessions WHERE session_id = %s", (session_id,)
                )
                return cursor.fetchone()
        except pymysql.Error as e:
            print(f"Session retrieval error: {e}")
            return None
        finally:
            if conn:
                conn.close()

    # Add this to your logout function
    def update_session(self, session_id):
        """Update session expiration time"""
        conn = None
        try:
            conn = get_db_conn()
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE user_sessions SET created_at = %s WHERE session_id = %s",
                    (int(time.time()), session_id),
                )
                conn.commit()
            return True
        except Exception as e:
            print(f"Session update error: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def delete_session(self, session_id):
        """Delete a session from the database"""
        conn = None
        try:
            conn = get_db_conn()
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM user_sessions WHERE session_id = %s", (session_id,)
                )
                conn.commit()
            return True
        except Exception as e:
            print(f"Session deletion error: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def logout(self, session_id):
        """Logout by deleting session"""
        self.delete_session(session_id)
        st.query_params.clear()


utils = DB_Utils()


def get_user_details(username):
    conn = None
    try:
        conn = get_db_conn()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM users WHERE username = %s
            """,
                (username,),
            )
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Error fetching user {username}: {e}")
        return None
    finally:
        if conn:
            conn.close()


def create_user(username: str, password: str, role: str = "user"):
    conn = None
    try:
        password_hash = utils.generate_hashed_password(password)
        mfa_secret = utils.generate_mfa_secret()
        conn = get_db_conn()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, mfa_secret)
                VALUES (%s, %s, %s, %s)
                """,
                (username, password_hash, role, mfa_secret),
            )
            conn.commit()
            return True, {"mfa_secret": mfa_secret, "username": username}
    except Exception as e:
        logger.error(f"Error adding user {username}: {e}")
        return False, None
    finally:
        if conn:
            conn.close()


def verify_login(username: str, password: str, totp_code: str):
    try:
        user_details = get_user_details(username)
        if not user_details:
            return False, "User not found"

        if not utils.verify_password(
            password, user_details["password_hash"].encode("utf-8")
        ):
            return False, "Invalid password"

        if not utils.verify_totp(user_details["mfa_secret"], totp_code):
            return False, "Invalid MFA code"

        return True, user_details

    except Exception as e:
        logger.error(f"Error validating login for {username}: {e}")
        return False, "An error occurred during login validation"


def reset_password(username: str, new_password: str):
    conn = None
    try:
        password_hash = utils.generate_hashed_password(new_password)
        conn = get_db_conn()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users SET password_hash = %s WHERE username = %s
            """,
                (password_hash, username),
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error resetting password for {username}: {e}")
        return False

    finally:
        if conn:
            conn.close()
