import pytest
from unittest.mock import patch, MagicMock
from app import calculate_loan, convert, update_db
from db import get_saved_rate

def test_calculate_loan_success():
    result = calculate_loan(100000, 10, 12)
    assert 'monthly_payment' in result
    assert 'total_payment' in result
    assert 'total_interest' in result
    assert result['monthly_payment'] > 0
    assert result['total_payment'] > 100000

def test_calculate_loan_invalid_loan_amount():
    with pytest.raises(ValueError, match="Loan amount must be a positive number"):
        calculate_loan(-1000, 10, 12)
    
    with pytest.raises(ValueError, match="Loan amount must be a positive number"):
        calculate_loan("invalid", 10, 12)
    
    with pytest.raises(ValueError, match="Loan amount must be a positive number"):
        calculate_loan(0, 10, 12)

def test_convert_success():
    result = convert(100, 'USD', 'EUR', 0.85)
    assert result == 85.0

def test_convert_none_rate():
    with pytest.raises(ValueError, match="Rate cannot be None"):
        convert(100, 'USD', 'EUR', None)

def test_convert_exception():
    with pytest.raises(ValueError, match="Amount must be a positive number"):
        convert(-100, 'USD', 'EUR', 0.85)
    
    with pytest.raises(ValueError, match="Rate must be a number"):
        convert(100, 'USD', 'EUR', "invalid")

def test_update_db_success():
    mock_data = {
        'Valute': {
            'USD': {'Value': 75.5},
            'EUR': {'Value': 86.5}
        }
    }
    
    with patch('app.fetch_rates', return_value=mock_data):
        with patch('app.save_rate') as mock_save:
            result = update_db()
            assert result['status'] == 'success'
            assert result['saved_count'] == 2
            assert mock_save.call_count == 2

def test_update_db_empty_rates():
    mock_data = {'Valute': {}}
    
    with patch('app.fetch_rates', return_value=mock_data):
        result = update_db()
        assert result['status'] == 'error'
        assert result['message'] == 'Valute data is empty'

def test_update_db_fetch_error():
    with patch('app.fetch_rates', side_effect=Exception("API Error")):
        result = update_db()
        assert result['status'] == 'error'
        assert 'API Error' in result['message']
