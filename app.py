from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO
import os

# Inicializando o app e as extensões
app = Flask(__name__)
app.config['SECRET_KEY'] = 'minha_chave_secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///imobiliaria.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
socketio = SocketIO(app)
login_manager.login_view = 'login'

# Tabelas do Banco de Dados

# Usuário (Admin, Corretor)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'admin' ou 'corretor'
    creci = db.Column(db.String(50), nullable=True)  # CRECI para corretores

# Imóvel
class Imovel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    endereco = db.Column(db.String(200), nullable=False)
    preco = db.Column(db.Float, nullable=False)

# Cadastro de Clientes
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    telefone = db.Column(db.String(20), nullable=True)
    endereco = db.Column(db.String(200), nullable=True)

# Criando as tabelas
with app.app_context():
    db.create_all()

# Gerenciador de Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rota para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login falhou. Verifique seu nome de usuário e senha.', 'danger')
    return render_template('login.html')

# Rota para dashboard (página protegida)
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# Rota para logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# Rota para cadastro de imóveis
@app.route('/cadastro_imovel', methods=['GET', 'POST'])
@login_required
def cadastro_imovel():
    if request.method == 'POST':
        nome = request.form['nome']
        endereco = request.form['endereco']
        preco = float(request.form['preco'])
        imovel = Imovel(nome=nome, endereco=endereco, preco=preco)
        db.session.add(imovel)
        db.session.commit()

        # Emitir evento de animação para o front-end
        socketio.emit('imovel_cadastrado', {'nome': nome, 'endereco': endereco, 'preco': preco})
        
        flash(f'Imóvel {nome} cadastrado com sucesso!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('cadastro_imovel.html')

# Rota para cadastro de clientes
@app.route('/cadastro_cliente', methods=['GET', 'POST'])
@login_required
def cadastro_cliente():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        endereco = request.form['endereco']
        cliente = Cliente(nome=nome, email=email, telefone=telefone, endereco=endereco)
        db.session.add(cliente)
        db.session.commit()
        flash(f'Cliente {nome} cadastrado com sucesso!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('cadastro_cliente.html')

# Rota para exibir a quantidade de imóveis cadastrados
@app.route('/metas')
@login_required
def metas():
    if current_user.role == 'admin':
        imoveis_cadastrados = Imovel.query.count()
        return render_template('metas.html', imoveis_cadastrados=imoveis_cadastrados)
    else:
        flash('Você não tem permissão para acessar essa página.', 'danger')
        return redirect(url_for('dashboard'))

# Rodando o app com SocketIO
if __name__ == '__main__':
    socketio.run(app, debug=True)

