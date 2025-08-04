import pymysql
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_conn():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_DATABASE"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def init_db():
    try:
        conn = get_db_conn()
        c = conn.cursor()

        # ----- Create tables if they don't exist -----

        # ----- Create table for users -----

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                mfa_secret VARCHAR(255),
                role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ----- Create table for user sessions -----

        c.execute(
            """
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id VARCHAR(255) PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL,
            created_at BIGINT NOT NULL,
            INDEX (username)
        )
        """
        )

        conn.commit()
    except Exception as e:
        logger.exception("Error while initializing DB")
    finally:
        if conn:
            conn.close()


init_db()
