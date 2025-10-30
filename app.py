from flask import Flask, render_template, request, session, jsonify, redirect, url_for
import json
import os
from datetime import datetime
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

# File paths
USERS_FILE = 'users.json'
WITHDRAWALS_FILE = 'withdrawals.json'
NOTIFICATIONS_FILE = 'notifications.json'
CONFIG_FILE = 'config.json'
ADMIN_PASSWORD = "admin1234"

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "adstoearn138@gmail.com"
SENDER_PASSWORD = "turs dohb nbiw iygv"

def get_client_ip():
    forwarded = request.headers.get('X-Forwarded-For') or request.headers.get('X-Real-IP')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or 'unknown'

def send_verification_email(to_email, verification_token):
    """Send verification email with HTML content"""
    verification_link = f"http://127.0.0.1:5000/verify/{verification_token}"
    
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 10px; }}
            .header {{ text-align: center; color: #ff8c00; font-size: 28px; font-weight: bold; margin-bottom: 20px; }}
            .content {{ color: #333; line-height: 1.6; margin-bottom: 30px; }}
            .button {{ display: inline-block; padding: 15px 30px; background-color: #ff8c00; color: #ffffff; text-decoration: none; border-radius: 5px; font-weight: bold; }}
            .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">Welcome to CashReward!</div>
            <div class="content">
                <p>Hello,</p>
                <p>Thank you for signing up with CashReward. Please verify your email address by clicking the button below:</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{verification_link}" class="button">Verify Email Address</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #ff8c00;">{verification_link}</p>
                <p>This link will expire in 24 hours.</p>
            </div>
            <div class="footer">
                <p>If you didn't create this account, please ignore this email.</p>
                <p>&copy; 2025 CashReward. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    msg = MIMEMultipart('alternative')
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = "Verify Your CashReward Account"
    
    msg.attach(MIMEText(html_message, 'html'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"Verification email sent to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def initialize_files():
    """Initialize JSON files if they don't exist"""
    files_data = {
        USERS_FILE: {},
        WITHDRAWALS_FILE: {},
        NOTIFICATIONS_FILE: [],
        CONFIG_FILE: {
            'minWithdrawal': 5000,
            'dailyAdLimit': 10,
            'coinValueCoins': 1000,
            'coinValueInr': 10,
            'paymentMethods': ['BKASH', 'NAGAD']
        }
    }
    
    for file_path, default_data in files_data.items():
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2)

def read_json(file_path):
    """Read JSON file and return data"""
    if not os.path.exists(file_path):
        return {} if file_path != NOTIFICATIONS_FILE else []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {} if file_path != NOTIFICATIONS_FILE else []

def write_json(file_path, data):
    """Write data to JSON file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
@app.route('/admin/')
def admin():
    return render_template('admin.html')

@app.route('/verify/<token>')
def verify_email(token):
    """Verify user email"""
    users = read_json(USERS_FILE)
    
    for user_id, user in users.items():
        if user.get('verificationToken') == token:
            if user.get('isVerified'):
                return "<h1>Email already verified!</h1><p>You can close this window and login to CashReward.</p>"
            
            users[user_id]['isVerified'] = True
            users[user_id]['verificationToken'] = None
            write_json(USERS_FILE, users)
            
            return "<h1>Email Verified Successfully!</h1><p>Your account has been activated. You can now login to CashReward.</p>"
    
    return "<h1>Invalid or Expired Link</h1><p>Please request a new verification email.</p>"

# API routes for main app
@app.route('/api/<action>', methods=['POST'])
def api_handler(action):
    initialize_files()
    
    if action == 'signup':
        return handle_signup()
    elif action == 'login':
        return handle_login()
    elif action == 'logout':
        return handle_logout()
    elif action == 'get_user_data':
        return handle_get_user_data()
    elif action == 'get_config':
        return handle_get_config()
    elif action == 'update_balance':
        return handle_update_balance()
    elif action == 'get_notifications':
        return handle_get_notifications()
    elif action == 'get_withdrawal_history':
        return handle_get_withdrawal_history()
    elif action == 'submit_withdrawal':
        return handle_submit_withdrawal()
    elif action == 'apply_referral':
        return handle_apply_referral()
    elif action == 'update_ad_count':
        return handle_update_ad_count()
    else:
        return jsonify({'success': False, 'message': 'Unknown action'})

# API routes for admin
@app.route('/admin_api/<action>', methods=['POST'])
def admin_api_handler(action):
    if action == 'login':
        return handle_admin_login()
    elif action == 'logout':
        return handle_admin_logout()
    
    # Check if admin is logged in
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    initialize_files()
    
    if action == 'get_dashboard_data':
        return handle_get_dashboard_data()
    elif action == 'get_users':
        return handle_admin_get_users()
    elif action == 'get_withdrawals':
        return handle_admin_get_withdrawals()
    elif action == 'get_settings':
        return handle_admin_get_settings()
    elif action == 'toggle_block_user':
        return handle_toggle_block_user()
    elif action == 'handle_withdrawal':
        return handle_admin_handle_withdrawal()
    elif action == 'send_notification':
        return handle_send_notification()
    elif action == 'save_settings':
        return handle_save_settings()
    else:
        return jsonify({'success': False, 'message': 'Unknown action'})

# Main app handlers
def handle_signup():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    client_ip = get_client_ip()
    
    users = read_json(USERS_FILE)
    
    for user in users.values():
        if user['email'] == email:
            return jsonify({'success': False, 'message': 'User already exists'})
        existing_ips = []
        if user.get('signupIp'):
            existing_ips.append(user.get('signupIp'))
        existing_ips.extend(user.get('ipHistory', []))
        if client_ip and client_ip != 'unknown' and client_ip in existing_ips:
            return jsonify({'success': False, 'message': 'Multiple accounts from the same IP are not allowed'})
    
    verification_token = str(uuid.uuid4())
    
    user_id = str(uuid.uuid4())
    referral_code = email[:3].upper() + str(abs(hash(email)))[-4:]
    
    ip_history = []
    if client_ip and client_ip != 'unknown':
        ip_history.append(client_ip)
    
    new_user = {
        'id': user_id,
        'name': name,
        'email': email,
        'password': password,
        'balance': 50,
        'referralCode': referral_code,
        'referredBy': None,
        'lastNotificationCheck': datetime.now().isoformat(),
        'createdAt': datetime.now().isoformat(),
        'dailyAdCount': 0,
        'lastAdWatchDate': datetime.now().strftime('%Y-%m-%d'),
        'isBlocked': False,
        'isVerified': False,
        'verificationToken': verification_token,
        'signupIp': client_ip,
        'lastLoginIp': client_ip,
        'ipHistory': ip_history
    }
    
    users[user_id] = new_user
    write_json(USERS_FILE, users)
    
    send_verification_email(email, verification_token)
    
    return jsonify({
        'success': True,
        'message': 'Account created! Please check your email to verify your account.',
        'requiresVerification': True
    })

def handle_login():
    email = request.form.get('email')
    password = request.form.get('password')
    client_ip = get_client_ip()
    
    users = read_json(USERS_FILE)
    user = None
    user_id = None
    
    for uid, u in users.items():
        if u['email'] == email:
            user = u
            user_id = uid
            break
    
    if user and user['password'] == password:
        if not user.get('isVerified', False):
            return jsonify({'success': False, 'message': 'Please verify your email first. Check your inbox.'})
        
        if user.get('isBlocked'):
            return jsonify({'success': False, 'message': 'Your account has been blocked'})
        
        if user_id:
            if client_ip and client_ip != 'unknown':
                history = user.get('ipHistory', [])
                if client_ip not in history:
                    history.append(client_ip)
                user['ipHistory'] = history
            if not user.get('signupIp'):
                user['signupIp'] = client_ip
            user['lastLoginIp'] = client_ip
            users[user_id] = user
            write_json(USERS_FILE, users)
        
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        return jsonify({'success': True, 'user_id': user['id']})
    else:
        return jsonify({'success': False, 'message': 'Invalid email or password'})

def handle_logout():
    session.clear()
    return jsonify({'success': True})

def handle_get_user_data():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False})
    
    users = read_json(USERS_FILE)
    user = users.get(user_id)
    
    if user:
        user_copy = user.copy()
        user_copy.pop('password', None)
        user_copy.pop('verificationToken', None)
        return jsonify({'success': True, 'user': user_copy})
    else:
        return jsonify({'success': False})

def handle_get_config():
    config = read_json(CONFIG_FILE)
    return jsonify({'success': True, 'config': config})

def handle_update_balance():
    user_id = session.get('user_id')
    amount = int(request.form.get('amount', 0))
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    users = read_json(USERS_FILE)
    if user_id in users:
        users[user_id]['balance'] = users[user_id].get('balance', 0) + amount
        write_json(USERS_FILE, users)
        return jsonify({'success': True, 'new_balance': users[user_id]['balance']})
    else:
        return jsonify({'success': False, 'message': 'User not found'})

def handle_get_notifications():
    notifications = read_json(NOTIFICATIONS_FILE)
    user_id = session.get('user_id')
    
    if user_id:
        users = read_json(USERS_FILE)
        if user_id in users:
            users[user_id]['lastNotificationCheck'] = datetime.now().isoformat()
            write_json(USERS_FILE, users)
    
    return jsonify({'success': True, 'notifications': list(reversed(notifications))})

def handle_get_withdrawal_history():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False})
    
    withdrawals = read_json(WITHDRAWALS_FILE)
    user_withdrawals = [w for w in withdrawals.values() if w.get('userId') == user_id]
    
    return jsonify({'success': True, 'withdrawals': list(reversed(user_withdrawals))})

def handle_submit_withdrawal():
    user_id = session.get('user_id')
    amount = int(request.form.get('amount', 0))
    method = request.form.get('method')
    payment_detail = request.form.get('payment_detail')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    users = read_json(USERS_FILE)
    config = read_json(CONFIG_FILE)
    
    if user_id not in users:
        return jsonify({'success': False, 'message': 'User not found'})
    
    min_withdrawal = config.get('minWithdrawal', 5000)
    
    if amount < min_withdrawal:
        return jsonify({'success': False, 'message': f"Minimum withdrawal is {min_withdrawal} coins"})
    
    if users[user_id]['balance'] < amount:
        return jsonify({'success': False, 'message': 'Insufficient balance'})
    
    users[user_id]['balance'] -= amount
    write_json(USERS_FILE, users)
    
    withdrawals = read_json(WITHDRAWALS_FILE)
    withdrawal_id = str(uuid.uuid4())
    
    new_withdrawal = {
        'id': withdrawal_id,
        'userId': user_id,
        'userName': users[user_id]['name'],
        'userEmail': users[user_id]['email'],
        'amount': amount,
        'method': method,
        'paymentDetail': payment_detail,
        'status': 'pending',
        'requestedAt': datetime.now().isoformat()
    }
    
    withdrawals[withdrawal_id] = new_withdrawal
    write_json(WITHDRAWALS_FILE, withdrawals)
    
    return jsonify({'success': True, 'new_balance': users[user_id]['balance']})

def handle_apply_referral():
    user_id = session.get('user_id')
    referral_code = request.form.get('code', '').upper().strip()
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    users = read_json(USERS_FILE)
    
    if user_id not in users:
        return jsonify({'success': False, 'message': 'User not found'})
    
    if users[user_id].get('referredBy'):
        return jsonify({'success': False, 'message': 'You have already used a referral code'})
    
    if users[user_id]['referralCode'] == referral_code:
        return jsonify({'success': False, 'message': 'You cannot use your own referral code'})
    
    referrer = None
    for u in users.values():
        if u['referralCode'] == referral_code:
            referrer = u
            break
    
    if not referrer:
        return jsonify({'success': False, 'message': 'Invalid referral code'})
    
    users[user_id]['balance'] += 100
    users[user_id]['referredBy'] = referral_code
    users[referrer['id']]['balance'] += 100
    
    write_json(USERS_FILE, users)
    
    return jsonify({'success': True, 'message': 'Referral code applied successfully! You received 100 coins.'})

def handle_update_ad_count():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False})
    
    users = read_json(USERS_FILE)
    today = datetime.now().strftime('%Y-%m-%d')
    
    if user_id in users:
        if users[user_id].get('lastAdWatchDate') != today:
            users[user_id]['dailyAdCount'] = 0
            users[user_id]['lastAdWatchDate'] = today
        
        users[user_id]['dailyAdCount'] = users[user_id].get('dailyAdCount', 0) + 1
        write_json(USERS_FILE, users)
        
        return jsonify({'success': True, 'dailyAdCount': users[user_id]['dailyAdCount']})
    else:
        return jsonify({'success': False})

# Admin handlers
def handle_admin_login():
    password = request.form.get('password')
    if password == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Invalid password'})

def handle_admin_logout():
    session.pop('admin_logged_in', None)
    return jsonify({'success': True})

def handle_get_dashboard_data():
    try:
        users = read_json(USERS_FILE)
        withdrawals = read_json(WITHDRAWALS_FILE)
        
        # Ensure proper dict format
        if not isinstance(users, dict):
            users = {}
        if not isinstance(withdrawals, dict):
            withdrawals = {}
        
        # Handle both dict and list formats for withdrawals
        pending_withdrawals = [w for w in withdrawals.values() if w.get('status') == 'pending']
        
        user_count = len(users)
        
        return jsonify({
            'success': True,
            'total_users': user_count,
            'pending_withdrawals': len(pending_withdrawals)
        })
    except Exception as e:
        print(f"Dashboard data error: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e),
            'total_users': 0,
            'pending_withdrawals': 0
        })

def handle_admin_get_users():
    users = read_json(USERS_FILE)
    # Ensure it's always a dict
    if not isinstance(users, dict):
        users = {}
    return jsonify({'success': True, 'users': users})

def handle_admin_get_withdrawals():
    withdrawals = read_json(WITHDRAWALS_FILE)
    pending_withdrawals = {k: v for k, v in withdrawals.items() if v.get('status') == 'pending'}
    return jsonify({'success': True, 'withdrawals': pending_withdrawals})

def handle_admin_get_settings():
    config = read_json(CONFIG_FILE)
    # Ensure it's always a dict
    if not isinstance(config, dict):
        config = {
            'minWithdrawal': 5000,
            'dailyAdLimit': 10,
            'coinValueCoins': 1000,
            'coinValueInr': 10,
            'paymentMethods': ['UPI', 'Paytm', 'PhonePe']
        }
        write_json(CONFIG_FILE, config)
    return jsonify({'success': True, 'config': config})

def handle_toggle_block_user():
    user_id = request.form.get('user_id')
    is_blocked = request.form.get('is_blocked') == 'true'
    
    users = read_json(USERS_FILE)
    if user_id in users:
        users[user_id]['isBlocked'] = not is_blocked
        write_json(USERS_FILE, users)
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'User not found'})

def handle_admin_handle_withdrawal():
    request_id = request.form.get('request_id')
    new_status = request.form.get('new_status')
    
    withdrawals = read_json(WITHDRAWALS_FILE)
    users = read_json(USERS_FILE)
    
    if request_id in withdrawals:
        withdrawals[request_id]['status'] = new_status
        
        if new_status == 'rejected':
            request_data = withdrawals[request_id]
            user_id = request_data['userId']
            if user_id in users:
                users[user_id]['balance'] += request_data['amount']
        
        write_json(WITHDRAWALS_FILE, withdrawals)
        write_json(USERS_FILE, users)
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Request not found'})

def handle_send_notification():
    title = request.form.get('title')
    message = request.form.get('message')
    
    notifications = read_json(NOTIFICATIONS_FILE)
    new_notification = {
        'id': str(uuid.uuid4()),
        'title': title,
        'message': message,
        'createdAt': datetime.now().isoformat()
    }
    
    notifications.append(new_notification)
    write_json(NOTIFICATIONS_FILE, notifications)
    return jsonify({'success': True})

def handle_save_settings():
    min_withdrawal = int(request.form.get('minWithdrawal', 5000))
    daily_ad_limit = int(request.form.get('dailyAdLimit', 10))
    coin_value_coins = int(request.form.get('coinValueCoins', 1000))
    coin_value_inr = int(request.form.get('coinValueInr', 10))
    payment_methods = [m.strip() for m in request.form.get('paymentMethods', '').split(',') if m.strip()]
    
    config = {
        'minWithdrawal': min_withdrawal,
        'dailyAdLimit': daily_ad_limit,
        'coinValueCoins': coin_value_coins,
        'coinValueInr': coin_value_inr,
        'paymentMethods': payment_methods
    }
    
    write_json(CONFIG_FILE, config)
    return jsonify({'success': True})

if __name__ == '__main__':
    initialize_files()
    app.run(debug=True)