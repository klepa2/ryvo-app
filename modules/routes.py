from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from .database import (
    create_user, get_user_by_username, get_all_events, add_event, join_event, 
    is_member, get_user_events, leave_event, save_message, get_messages,
    edit_message, delete_message, update_user_profile
)
from .auth import verify_password, get_current_user, hash_password

bp = Blueprint('main', __name__)

# === ГЛАВНЫЕ СТРАНИЦЫ ===
@bp.route('/')
def index():
    user = get_current_user()
    if not user:
        return render_template('landing.html')
    events = get_all_events()
    return render_template('main.html', events=events, user=user, active_tab='all', title='Все мероприятия')

@bp.route('/my-chats')
def my_chats():
    user = get_current_user()
    if not user:
        return redirect(url_for('main.index'))
    events = get_user_events(user['id'])
    return render_template('my_chats.html', events=events, user=user)

@bp.route('/profile')
def profile():
    user = get_current_user()
    if not user:
        return redirect(url_for('main.index'))
    return render_template('profile.html', user=user)

@bp.route('/create', methods=['GET', 'POST'])
def create_event():
    user = get_current_user()
    if not user:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        add_event(request.form['title'], request.form.get('description', ''), request.form['date'], 
                  request.form['location'], user['id'], int(request.form['max_participants']))
        return redirect(url_for('main.index'))
    return render_template('create_event.html')

@bp.route('/join/<int:event_id>')
def join_event_route(event_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('main.index'))
    join_event(user['id'], event_id)
    return redirect(url_for('main.chat_room', event_id=event_id))

@bp.route('/chat/<int:event_id>')
def chat_room(event_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('main.index'))
    if not is_member(user['id'], event_id):
        return redirect(url_for('main.index'))
    return render_template('chat.html', 
                          event_id=event_id, 
                          user_id=user['id'], 
                          username=user['username'])
                          
@bp.route('/leave/<int:event_id>')
def leave_event_route(event_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('main.index'))
    leave_event(user['id'], event_id)
    return redirect(url_for('main.my_chats'))

# === АУТЕНТИФИКАЦИЯ ===
@bp.route('/register-page')
def register_page():
    return render_template('register.html')

@bp.route('/login-page')
def login_page():
    return render_template('login.html')

@bp.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    confirm = request.form.get('confirm_password')
    
    if len(username) < 3:
        return "Имя не менее 3 символов", 400
    if len(password) < 4:
        return "Пароль не менее 4 символов", 400
    if password != confirm:
        return "Пароли не совпадают", 400
        
    hashed = hash_password(password)
    user_id = create_user(username, hashed)
    if user_id:
        session['user_id'] = user_id
        return redirect(url_for('main.index'))
    return "Пользователь уже существует", 400

@bp.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = get_user_by_username(username)
    
    if user and verify_password(password, user['password']):
        session['user_id'] = user['id']
        return redirect(url_for('main.index'))
    return "Неверные данные", 401

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))

# === API ===
@bp.route('/api/messages/<int:event_id>')
def api_get_messages(event_id):
    return {'messages': get_messages(event_id)}

@bp.route('/api/send', methods=['POST'])
def api_send_message():
    data = request.get_json()
    save_message(data['event_id'], data['user_id'], data['message'])
    return {'status': 'ok'}

@bp.route('/api/update-profile', methods=['POST'])
def api_update_profile():
    user = get_current_user()
    if not user:
        return {'error': 'Unauthorized'}, 401
    data = request.get_json()
    update_user_profile(user['id'], bio=data.get('bio'))
    return {'status': 'ok'}

@bp.route('/api/edit-message', methods=['POST'])
def api_edit_message():
    data = request.get_json()
    if edit_message(data['message_id'], data['user_id'], data['message']):
        return {'status': 'ok'}
    return {'error': 'Unauthorized'}, 401

@bp.route('/api/delete-message', methods=['POST'])
def api_delete_message():
    data = request.get_json()
    if delete_message(data['message_id'], data['user_id']):
        return {'status': 'ok'}
    return {'error': 'Unauthorized'}, 401