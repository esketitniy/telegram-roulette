from flask import Flask, request, jsonify, render_template
import json
import random
import hmac
import hashlib
from urllib.parse import unquote
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-secret-key')

# ЗАМЕНИ НА СВОЙ ТОКЕН БОТА!
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

def init_db():
    conn = sqlite3.connect('roulette.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance INTEGER DEFAULT 100,
            total_won INTEGER DEFAULT 0,
            total_lost INTEGER DEFAULT 0,
            games_played INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            bet_amount INTEGER,
            bet_type TEXT,
            bet_value TEXT,
            result_number INTEGER,
            payout INTEGER,
            profit INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()

def verify_telegram_data(init_data):
    try:
        parsed_data = dict(x.split('=', 1) for x in init_data.split('&'))
        check_hash = parsed_data.pop('hash', '')
        
        data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(parsed_data.items())])
        secret_key = hmac.new("WebAppData".encode(), BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        return calculated_hash == check_hash
    except:
        return False

def get_or_create_user(user_data):
    conn = sqlite3.connect('roulette.db')
    cursor = conn.cursor()
    
    user_id = user_data['id']
    username = user_data.get('username', '')
    first_name = user_data.get('first_name', '')
    
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute('''
            INSERT INTO users (user_id, username, first_name) 
            VALUES (?, ?, ?)
        ''', (user_id, username, first_name))
        conn.commit()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
    
    conn.close()
    return user

class RouletteGame:
    def __init__(self):
        self.numbers = list(range(37))
        self.red_numbers = [
