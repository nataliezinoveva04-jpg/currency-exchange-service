import pytest
import sqlite3
import os
import sys
import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock

# Добавляем путь к корневой папке проекта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import init_db, save_rate, get_saved_rate, get_db_connection, DB_NAME

@pytest.fixture
def temp_db():
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()
    
    with patch('db.DB_NAME', temp_file.name):
        init_db()
        yield temp_file.name
    
    try:
        os.unlink(temp_file.name)
    except (PermissionError, FileNotFoundError):
        pass

def test_init_db_creates_table(temp_db):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rates'")
        result = cursor.fetchone()
        assert result is not None
        assert result['name'] == 'rates'

def test_save_rate_new_record(temp_db):
    save_rate('USD', 75.5)
    record = get_saved_rate('USD')
    assert record is not None
    assert record['currency'] == 'USD'
    assert record['rate'] == 75.5

def test_save_rate_update_existing(temp_db):
    save_rate('EUR', 85.0)
    save_rate('EUR', 86.5)
    record = get_saved_rate('EUR')
    assert record is not None
    assert record['rate'] == 86.5

def test_save_rate_date_format(temp_db):
    test_date = '2024-01-15'
    save_rate('GBP', 90.0, test_date)
    record = get_saved_rate('GBP', test_date)
    assert record is not None
    assert record['date'] == test_date

def test_save_rate_multiple_currencies(temp_db):
    currencies = {'USD': 75.5, 'EUR': 86.5, 'GBP': 90.0}
    for currency, rate in currencies.items():
        save_rate(currency, rate)
    
    for currency in currencies:
        record = get_saved_rate(currency)
        assert record is not None
        assert record['rate'] == currencies[currency]

def test_save_rate_edge_cases(temp_db):
    save_rate('MIN', 0.0001)
    record = get_saved_rate('MIN')
    assert record is not None
    assert record['rate'] == 0.0001
    
    save_rate('MAX', 999999.99)
    record = get_saved_rate('MAX')
    assert record is not None
    assert record['rate'] == 999999.99

def test_save_rate_database_connection_error(temp_db):
    with patch('db.get_db_connection') as mock_conn:
        mock_conn.side_effect = sqlite3.OperationalError("Connection error")
        with pytest.raises(Exception, match="Database error"):
            save_rate('USD', 75.5)

def test_save_rate_commit_error(temp_db):
    with patch('sqlite3.Connection.commit') as mock_commit:
        mock_commit.side_effect = sqlite3.OperationalError("Commit error")
        with pytest.raises(Exception, match="Database error"):
            save_rate('USD', 75.5)

def test_save_rate_parameter_types(temp_db):
    save_rate('USD', 75.5)
    record = get_saved_rate('USD')
    assert record is not None
    
    with pytest.raises(ValueError, match="Currency must be a 3-letter string"):
        save_rate(123, 75.5)
    
    with pytest.raises(ValueError, match="Rate must be a positive number"):
        save_rate('USD', 'invalid')

def test_save_rate_sql_injection_protection(temp_db):
    malicious_currency = "USD'; DROP TABLE rates; --"
    save_rate(malicious_currency, 75.5)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rates'")
        result = cursor.fetchone()
        assert result is not None

def test_get_saved_rate_success(temp_db):
    save_rate('USD', 75.5)
    record = get_saved_rate('USD')
    assert record is not None
    assert record['currency'] == 'USD'
    assert record['rate'] == 75.5
    assert 'date' in record

def test_get_saved_rate_default_currency(temp_db):
    save_rate('USD', 75.5)
    record = get_saved_rate('usd')
    assert record is not None
    assert record['currency'] == 'USD'

def test_get_saved_rate_nonexistent_currency(temp_db):
    record = get_saved_rate('XYZ')
    assert record is None

def test_get_saved_rate_empty_database(temp_db):
    record = get_saved_rate('USD')
    assert record is None

def test_get_saved_rate_multiple_currencies(temp_db):
    save_rate('USD', 75.5)
    save_rate('EUR', 86.5)
    
    record_usd = get_saved_rate('USD')
    record_eur = get_saved_rate('EUR')
    
    assert record_usd is not None
    assert record_eur is not None
    assert record_usd['rate'] != record_eur['rate']

def test_get_saved_rate_case_sensitivity(temp_db):
    save_rate('USD', 75.5)
    record_upper = get_saved_rate('USD')
    record_lower = get_saved_rate('usd')
    assert record_upper is not None
    assert record_lower is not None
    assert record_upper['currency'] == record_lower['currency']

def test_get_saved_rate_sql_injection_protection(temp_db):
    malicious_input = "USD' OR '1'='1"
    record = get_saved_rate(malicious_input)
    assert record is None
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM rates")
        result = cursor.fetchone()
        assert result['count'] == 0

def test_get_saved_rate_database_connection_error(temp_db):
    with patch('db.get_db_connection') as mock_conn:
        mock_conn.side_effect = sqlite3.OperationalError("Connection error")
        with pytest.raises(sqlite3.OperationalError):
            get_saved_rate('USD')
