import requests
import json
from typing import Optional, Dict, Any

API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"

def fetch_rates() -> Optional[Dict[str, Any]]:
    """Получение курсов валют из внешнего API"""
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data or 'Valute' not in data:
            return None
        
        if data.get('success') is False:
            return None
            
        return data
    except requests.exceptions.HTTPError as e:
        raise Exception(f"HTTP error occurred: {e}")
    except requests.exceptions.ConnectionError:
        raise Exception("Connection error: Unable to reach API")
    except requests.exceptions.Timeout:
        raise Exception("Timeout error: API request took too long")
    except requests.exceptions.SSLError:
        raise Exception("SSL error: Certificate verification failed")
    except json.JSONDecodeError:
        raise Exception("Malformed JSON response from API")
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")
