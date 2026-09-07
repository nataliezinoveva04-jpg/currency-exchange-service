import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

DB_NAME = os.getenv('DB_NAME', 'currency.db')


@contextmanager
def get_db_connection():
    """Контекстный менеджер для подключения к БД"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Инициализация базы данных"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                currency TEXT NOT NULL,
                rate REAL NOT NULL,
                date TEXT NOT NULL,
                UNIQUE(currency, date)
            )
        '''
        )
        conn.commit()


def save_rate(currency, rate, date=None):
    """Сохранение курса валюты в БД"""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    if not isinstance(currency, str) or len(currency) != 3:
        raise ValueError("Currency must be a 3-letter string")
    if not isinstance(rate, (int, float)) or rate <= 0:
        raise ValueError("Rate must be a positive number")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                '''
                INSERT INTO rates (currency, rate, date)
                VALUES (?, ?, ?)
                ON CONFLICT(currency, date) 
                DO UPDATE SET rate = excluded.rate
            ''',
                (currency.upper(), rate, date),
            )
            conn.commit()
        except sqlite3.OperationalError as e:
            raise Exception(f"Database error: {e}")
        except sqlite3.IntegrityError as e:
            raise Exception(f"Data integrity error: {e}")


def get_saved_rate(currency, date=None):
    """Получение курса валюты из БД"""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT currency, rate, date FROM rates 
            WHERE currency = ? AND date = ?
        ''',
            (currency.upper(), date),
        )
        result = cursor.fetchone()
        return dict(result) if result else None
