from flask import Flask, request, jsonify
from datetime import datetime
import os
from db import save_rate, get_saved_rate, init_db
from api import fetch_rates

app = Flask(__name__)
init_db()


def calculate_loan(loan_amount, interest_rate, months):
    """Расчёт кредита"""
    if not isinstance(loan_amount, (int, float)) or loan_amount <= 0:
        raise ValueError("Loan amount must be a positive number")
    if not isinstance(interest_rate, (int, float)) or interest_rate < 0:
        raise ValueError("Interest rate must be a non-negative number")
    if not isinstance(months, int) or months <= 0:
        raise ValueError("Months must be a positive integer")

    monthly_rate = interest_rate / 12 / 100
    if monthly_rate == 0:
        monthly_payment = loan_amount / months
    else:
        monthly_payment = (
            loan_amount * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
        )
    total_payment = monthly_payment * months
    return {
        'monthly_payment': round(monthly_payment, 2),
        'total_payment': round(total_payment, 2),
        'total_interest': round(total_payment - loan_amount, 2),
    }


def convert(amount, from_currency, to_currency, rate):
    """Конвертация валют"""
    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ValueError("Amount must be a positive number")
    if rate is None:
        raise ValueError("Rate cannot be None")
    if not isinstance(rate, (int, float)):
        raise ValueError("Rate must be a number")

    return round(amount * rate, 2)


def update_db():
    """Обновление БД курсами валют"""
    try:
        data = fetch_rates()
        if not data:
            return {"status": "error", "message": "No data received from API"}

        valute_data = data.get('Valute', {})
        if not valute_data:
            return {"status": "error", "message": "Valute data is empty"}

        saved_count = 0
        for currency_code, currency_info in valute_data.items():
            if currency_info.get('Value'):
                save_rate(currency_code, currency_info['Value'])
                saved_count += 1

        return {"status": "success", "saved_count": saved_count}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.route('/calculate_loan', methods=['POST'])
def loan_route():
    try:
        data = request.json
        result = calculate_loan(data['loan_amount'], data['interest_rate'], data['months'])
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/convert', methods=['POST'])
def convert_route():
    try:
        data = request.json
        rate = get_saved_rate(data['to_currency'])
        if not rate:
            return jsonify({'error': 'Rate not found'}), 404
        result = convert(data['amount'], data['from_currency'], data['to_currency'], rate['rate'])
        return jsonify({'converted_amount': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/update', methods=['POST'])
def update_route():
    result = update_db()
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
