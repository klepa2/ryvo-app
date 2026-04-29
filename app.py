from flask import Flask
from modules.routes import bp
from modules.database import init_db
from datetime import timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# Регистрируем маршруты
app.register_blueprint(bp)

# Создаём таблицы в базе данных
init_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)