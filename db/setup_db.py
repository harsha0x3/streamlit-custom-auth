import pymysql
import os
from utils.log import logger
from dotenv import load_dotenv

load_dotenv()


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
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                incident_number VARCHAR(255) UNIQUE,
                created_on DATETIME,
                priority VARCHAR(255),
                risk_score VARCHAR(255),
                status VARCHAR(255),
                sender VARCHAR(255),
                service_start DATETIME,
                issue_summary TEXT,
                domain VARCHAR(255)
            )
        """
        )

        # ----- Create meta table for alert tracking -----

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS meta (
                incident_number VARCHAR(255) PRIMARY KEY,
                last_alert_sent_to_h1 DATETIME,
                last_alert_sent_to_h2 DATETIME,
                last_breach_alert_sent_to_h1 DATETIME,
                last_breach_alert_sent_to_h2 DATETIME
            )
        """
        )

        # ----- Create table for verticals -----

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS verticals (
                id INT AUTO_INCREMENT PRIMARY KEY,
                vertical_name VARCHAR(255) NOT NULL UNIQUE,
                team_lead VARCHAR(255) NOT NULL,
                vertical_head VARCHAR(255) NOT NULL
            )"""
        )

        # ----- Create table for domains -----
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS domains (
                vertical_id INT NOT NULL,
                domain VARCHAR(255) NOT NULL,
                PRIMARY KEY (vertical_id, domain),
                FOREIGN KEY (vertical_id) REFERENCES verticals(id)
                )"""
        )

        # ----- Create table for contacts -----
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                vertical_id INT NOT NULL UNIQUE,
                team_lead_contact VARCHAR(512),
                vertical_head_contact VARCHAR(512),
                FOREIGN KEY (vertical_id) REFERENCES verticals(id)
                )
                """
        )

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
