import pytest
import requests
import json
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import fetch_rates, API_URL


def test_fetch_rates_success():
    mock_response = MagicMock()
    mock_response.json.return_value = {'Valute': {'USD': {'Value': 75.5}}}
    mock_response.raise_for_status = MagicMock()

    with patch('requests.get', return_value=mock_response):
        result = fetch_rates()
        assert result is not None
        assert 'Valute' in result
        assert 'USD' in result['Valute']


def test_fetch_rates_success_without_success_field():
    mock_response = MagicMock()
    mock_response.json.return_value = {'Valute': {'EUR': {'Value': 86.5}}}
    mock_response.raise_for_status = MagicMock()

    with patch('requests.get', return_value=mock_response):
        result = fetch_rates()
        assert result is not None
        assert 'Valute' in result


def test_fetch_rates_http_error():
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.HTTPError("404 Not Found")
        with pytest.raises(Exception, match="HTTP error occurred"):
            fetch_rates()


def test_fetch_rates_connection_error():
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        with pytest.raises(Exception, match="Connection error"):
            fetch_rates()


def test_fetch_rates_timeout_error():
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")
        with pytest.raises(Exception, match="Timeout error"):
            fetch_rates()


def test_fetch_rates_empty_valute():
    mock_response = MagicMock()
    mock_response.json.return_value = {'Valute': {}}
    mock_response.raise_for_status = MagicMock()

    with patch('requests.get', return_value=mock_response):
        result = fetch_rates()
        assert result is None


def test_fetch_rates_malformed_json():
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response

        with pytest.raises(Exception, match="Malformed JSON"):
            fetch_rates()


def test_fetch_rates_ssl_error():
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.SSLError("SSL certificate error")
        with pytest.raises(Exception) as exc_info:
            fetch_rates()
        assert "SSL error" in str(exc_info.value)
