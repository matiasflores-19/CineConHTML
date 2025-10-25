from flask import Flask, render_template, request, redirect, url_for, flash, abort, session
from models import db, Movie, Ticket, User
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config.from_object('config')

os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)

db.init_app(app)

with app.app_context():
    db.create_all()
    # Crear usuario admin por defecto si no existe
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', password=generate_password_hash('admin123'))
        db.session.add(admin_user)
        db.session.commit()

# Decorador para requerir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, inicie sesión para acceder a esta página', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('index'))

@app.route('/movies')
def movies_list():
    q = request.args.get('q', '')
    if q:
        movies = Movie.query.filter((Movie.title.contains(q)) | (Movie.genre.contains(q))).all()
    else:
        movies = Movie.query.order_by(Movie.created_at.desc()).all()
    return render_template('movies_list.html', movies=movies, q=q)

@app.route('/movies/new', methods=['GET', 'POST'])
@login_required
def movie_new():
    if request.method == 'POST':
        title = request.form['title'].strip()
        description = request.form.get('description', '')
        try:
            duration = int(request.form['duration'])
        except ValueError:
            flash('Duración inválida', 'error')
            return redirect(url_for('movie_new'))
        genre = request.form.get('genre', '')
        seats_total = int(request.form.get('seats_total', 100))

        movie = Movie(title=title, description=description, duration=duration, genre=genre, seats_total=seats_total)
        db.session.add(movie)
        db.session.commit()
        flash('Película creada correctamente', 'success')
        return redirect(url_for('movies_list'))
    return render_template('movie_form.html', action='Crear')

@app.route('/movies/<int:movie_id>/edit', methods=['GET', 'POST'])
@login_required
def movie_edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    if request.method == 'POST':
        movie.title = request.form['title'].strip()
        movie.description = request.form.get('description', '')
        try:
            movie.duration = int(request.form['duration'])
            movie.seats_total = int(request.form.get('seats_total', movie.seats_total))
        except ValueError:
            flash('Campos numéricos inválidos', 'error')
            return redirect(url_for('movie_edit', movie_id=movie_id))
        movie.genre = request.form.get('genre', '')
        db.session.commit()
        flash('Película actualizada', 'success')
        return redirect(url_for('movies_list'))
    return render_template('movie_form.html', action='Editar', movie=movie)

@app.route('/movies/<int:movie_id>/delete', methods=['POST'])
@login_required
def movie_delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('Película eliminada', 'success')
    return redirect(url_for('movies_list'))

@app.route('/movies/<int:movie_id>')
def movie_detail(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    return render_template('movie_detail.html', movie=movie)

@app.route('/movies/<int:movie_id>/buy', methods=['GET', 'POST'])
def buy_ticket(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    if request.method == 'POST':
        buyer_name = request.form.get('buyer_name', 'Anonimo')
        try:
            quantity = int(request.form.get('quantity', 1))
        except ValueError:
            flash('Cantidad inválida', 'error')
            return redirect(url_for('buy_ticket', movie_id=movie_id))

        if quantity <= 0:
            flash('La cantidad debe ser positiva', 'error')
            return redirect(url_for('buy_ticket', movie_id=movie_id))

        if quantity > movie.seats_available():
            flash(f'Sólo quedan {movie.seats_available()} asientos disponibles', 'error')
            return redirect(url_for('buy_ticket', movie_id=movie_id))

        ticket = Ticket(movie_id=movie.id, buyer_name=buyer_name, quantity=quantity)
        movie.seats_sold += quantity
        db.session.add(ticket)
        db.session.commit()
        flash('Compra realizada con éxito', 'success')
        return redirect(url_for('movie_detail', movie_id=movie.id))

    return render_template('buy_ticket.html', movie=movie)

@app.route('/cartelera')
def cartelera():
    movies = Movie.query.order_by(Movie.created_at.desc()).all()
    return render_template('cartelera.html', movies=movies)

if __name__ == '__main__':
    app.run(debug=True)