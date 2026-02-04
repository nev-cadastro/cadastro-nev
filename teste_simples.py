from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///teste.db'
app.config['SECRET_KEY'] = 'teste123'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)

with app.app_context():
    db.create_all()
    print("✅ Banco de dados criado com sucesso!")
    
    # Testar conexão
    user = User(username='teste', email='teste@teste.com')
    db.session.add(user)
    db.session.commit()
    print("✅ Usuário de teste criado!")