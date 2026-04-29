import sqlite3
from datetime import datetime

def get_db():
    return sqlite3.connect('events.db')

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # Таблица пользователей
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            avatar TEXT,
            bio TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица мероприятий
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            location TEXT NOT NULL,
            created_by INTEGER NOT NULL,
            max_participants INTEGER DEFAULT 20,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')
    
    # Таблица участников
    c.execute('''
        CREATE TABLE IF NOT EXISTS event_members (
            user_id INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (event_id) REFERENCES events(id),
            PRIMARY KEY (user_id, event_id)
        )
    ''')
    
    # Таблица сообщений
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT,
            image TEXT,
            reply_to INTEGER,
            edited BOOLEAN DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES events(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# === ФУНКЦИИ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ===
def create_user(username, password):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return user_id
    except:
        conn.close()
        return None

def get_user_by_username(username):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    if user:
        return {'id': user[0], 'username': user[1], 'password': user[2], 
                'avatar': user[3], 'bio': user[4], 'created_at': user[5], 'last_seen': user[6]}
    return None

def get_user_by_id(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return {'id': user[0], 'username': user[1], 'password': user[2],
                'avatar': user[3], 'bio': user[4], 'created_at': user[5], 'last_seen': user[6]}
    return None

def update_user_profile(user_id, bio=None, avatar=None):
    conn = get_db()
    c = conn.cursor()
    if avatar:
        c.execute('UPDATE users SET avatar = ?, bio = COALESCE(?, bio) WHERE id = ?', (avatar, bio, user_id))
    else:
        c.execute('UPDATE users SET bio = COALESCE(?, bio) WHERE id = ?', (bio, user_id))
    conn.commit()
    conn.close()

# === ФУНКЦИИ ДЛЯ МЕРОПРИЯТИЙ ===
def get_all_events():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT e.*, (SELECT COUNT(*) FROM event_members WHERE event_id = e.id) as participants_count,
               u.username, u.avatar
        FROM events e JOIN users u ON e.created_by = u.id ORDER BY e.id DESC
    ''')
    events = c.fetchall()
    conn.close()
    return [{'id': e[0], 'title': e[1], 'description': e[2], 'date': e[3], 'location': e[4],
             'created_by': e[5], 'max_participants': e[6], 'created_at': e[7], 'participants': e[8],
             'creator_name': e[9], 'creator_avatar': e[10]} for e in events]

def add_event(title, description, date, location, created_by, max_participants):
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO events (title, description, date, location, created_by, max_participants) VALUES (?, ?, ?, ?, ?, ?)',
              (title, description, date, location, created_by, max_participants))
    conn.commit()
    conn.close()

def join_event(user_id, event_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO event_members (user_id, event_id) VALUES (?, ?)', (user_id, event_id))
    conn.commit()
    conn.close()

def leave_event(user_id, event_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM event_members WHERE user_id = ? AND event_id = ?', (user_id, event_id))
    conn.commit()
    c.execute('SELECT COUNT(*) FROM event_members WHERE event_id = ?', (event_id,))
    if c.fetchone()[0] == 0:
        c.execute('DELETE FROM events WHERE id = ?', (event_id,))
        c.execute('DELETE FROM messages WHERE event_id = ?', (event_id,))
        conn.commit()
    conn.close()

def is_member(user_id, event_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT 1 FROM event_members WHERE user_id = ? AND event_id = ?', (user_id, event_id))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_user_events(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT e.*, (SELECT COUNT(*) FROM event_members WHERE event_id = e.id) as participants_count,
               u.username, u.avatar
        FROM events e JOIN event_members em ON e.id = em.event_id
        JOIN users u ON e.created_by = u.id WHERE em.user_id = ? ORDER BY e.id DESC
    ''', (user_id,))
    events = c.fetchall()
    conn.close()
    return [{'id': e[0], 'title': e[1], 'description': e[2], 'date': e[3], 'location': e[4],
             'created_by': e[5], 'max_participants': e[6], 'created_at': e[7], 'participants': e[8],
             'creator_name': e[9], 'creator_avatar': e[10]} for e in events]

# === ФУНКЦИИ ДЛЯ СООБЩЕНИЙ ===
def save_message(event_id, user_id, message, image=None, reply_to=None):
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO messages (event_id, user_id, message, image, reply_to) VALUES (?, ?, ?, ?, ?)',
              (event_id, user_id, message, image, reply_to))
    conn.commit()
    msg_id = c.lastrowid
    conn.close()
    return msg_id

def get_messages(event_id, limit=50):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT m.id, m.message, m.image, m.reply_to, m.edited, m.timestamp,
               u.username, u.avatar, u.id
        FROM messages m JOIN users u ON m.user_id = u.id
        WHERE m.event_id = ? ORDER BY m.timestamp DESC LIMIT ?
    ''', (event_id, limit))
    messages = c.fetchall()
    conn.close()
    result = []
    for m in reversed(messages):
        result.append({
            'id': m[0], 'message': m[1], 'image': m[2], 'reply_to': m[3],
            'edited': bool(m[4]), 'timestamp': datetime.strptime(m[5], '%Y-%m-%d %H:%M:%S').strftime('%H:%M') if m[5] else '',
            'username': m[6], 'avatar': m[7], 'user_id': m[8]
        })
    return result

def edit_message(message_id, user_id, new_text):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT user_id FROM messages WHERE id = ?', (message_id,))
    result = c.fetchone()
    if result and result[0] == user_id:
        c.execute('UPDATE messages SET message = ?, edited = 1 WHERE id = ?', (new_text, message_id))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def delete_message(message_id, user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT user_id FROM messages WHERE id = ?', (message_id,))
    result = c.fetchone()
    if result and result[0] == user_id:
        c.execute('DELETE FROM messages WHERE id = ?', (message_id,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False