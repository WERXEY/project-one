# Plan d'implémentation du système d'authentification avec Flask-Login

## 1. Configuration de Flask-Login

### Mise à jour de `__init__.py`
```python
from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from api.models import db, User

def create_app(app=None):
    if app is None:
        app = Flask(__name__)
    
    # Configuration de l'application
    app.config.from_object('config.Config')
    
    # Initialisation de la base de données
    db.init_app(app)
    
    # Création des tables si elles n'existent pas
    with app.app_context():
        db.create_all()
    
    # Configuration de Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    # Activation de CORS pour permettre les requêtes cross-origin
    CORS(app)
    
    # Enregistrement des blueprints
    from api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Enregistrement du blueprint d'authentification
    from api.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    return app
```

## 2. Création du blueprint d'authentification (`auth.py`)

```python
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from api.models import db, User
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            flash('Vérifiez vos identifiants et réessayez.')
            return render_template('login.html', error='Identifiants invalides')
        
        # Mise à jour de la date de dernière connexion
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=remember)
        next_page = request.args.get('next')
        
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('index')
            
        return redirect(next_page)
        
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        plan = request.form.get('plan', 'free')
        terms = request.form.get('terms')
        
        # Validation des données
        if not name or not email or not password or not confirm_password:
            return render_template('register.html', error='Tous les champs sont obligatoires')
            
        if password != confirm_password:
            return render_template('register.html', error='Les mots de passe ne correspondent pas')
            
        if len(password) < 8:
            return render_template('register.html', error='Le mot de passe doit contenir au moins 8 caractères')
            
        if not terms:
            return render_template('register.html', error='Vous devez accepter les conditions d\'utilisation')
            
        # Vérification si l'email existe déjà
        user = User.query.filter_by(email=email).first()
        if user:
            return render_template('register.html', error='Cet email est déjà utilisé')
            
        # Création du nouvel utilisateur
        new_user = User(
            name=name,
            email=email,
            plan=plan
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        # Connexion automatique après inscription
        login_user(new_user)
        
        return redirect(url_for('index'))
        
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    # À implémenter
    return render_template('forgot_password.html')
```

## 3. Mise à jour des routes principales (`routes.py`)

Ajouter les routes pour les pages principales et protéger les routes nécessitant une authentification :

```python
from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from api.controllers.clip_controller import generate_short_clip, generate_long_clip, get_clip_status, get_clip_info
from api.models import Clip

# Création du blueprint pour l'API
api_bp = Blueprint('api', __name__)

# Routes de l'API existantes...

# Routes pour les pages principales
@api_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@api_bp.route('/pricing', methods=['GET'])
def pricing():
    return render_template('pricing.html')

@api_bp.route('/my-clips', methods=['GET'])
@login_required
def my_clips():
    user_clips = Clip.query.filter_by(user_id=current_user.id).order_by(Clip.created_at.desc()).all()
    return render_template('my_clips.html', clips=user_clips)

@api_bp.route('/view-clip/<clip_id>', methods=['GET'])
@login_required
def view_clip(clip_id):
    clip = Clip.query.get_or_404(clip_id)
    
    # Vérifier si l'utilisateur est autorisé à voir ce clip
    if clip.user_id != current_user.id:
        return redirect(url_for('api.my_clips'))
        
    return render_template('view_clip.html', clip=clip)

# Mise à jour des routes API pour prendre en compte l'authentification
@api_bp.route('/clips', methods=['POST'])
@login_required
def create_clip():
    data = request.get_json()
    
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'No data provided'
        }), 400
    
    url = data.get('url')
    mode = data.get('mode', 'short')
    transitions = data.get('transitions', True)
    
    if not url:
        return jsonify({
            'status': 'error',
            'message': 'URL is required'
        }), 400
    
    if mode not in ['short', 'long']:
        return jsonify({
            'status': 'error',
            'message': 'Mode must be either "short" or "long"'
        }), 400
    
    # Vérifier si l'utilisateur peut générer un clip selon son plan
    if not current_user.can_generate_clip(mode):
        return jsonify({
            'status': 'error',
            'message': 'Limite de clips atteinte ou fonctionnalité non disponible avec votre plan'
        }), 403
    
    try:
        if mode == 'short':
            clip_id = generate_short_clip(url, transitions, current_user.id)
        else:
            clip_id = generate_long_clip(url, transitions, current_user.id)
        
        # Incrémenter le compteur de clips générés
        current_user.increment_clip_count()
        
        return jsonify({
            'status': 'success',
            'message': 'Clip generation started',
            'clip_id': clip_id
        }), 202
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
```

## 4. Création du template pour la page de profil (`profile.html`)

```html
{% extends "base.html" %}

{% block title %}Mon profil - Générateur de clips "Best Of"{% endblock %}

{% block content %}
<div class="container">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header">
                    <h2 class="mb-0">Mon profil</h2>
                </div>
                <div class="card-body">
                    <div class="row mb-4">
                        <div class="col-md-4">
                            <strong>Nom :</strong>
                        </div>
                        <div class="col-md-8">
                            {{ current_user.name }}
                        </div>
                    </div>
                    
                    <div class="row mb-4">
                        <div class="col-md-4">
                            <strong>Email :</strong>
                        </div>
                        <div class="col-md-8">
                            {{ current_user.email }}
                        </div>
                    </div>
                    
                    <div class="row mb-4">
                        <div class="col-md-4">
                            <strong>Formule :</strong>
                        </div>
                        <div class="col-md-8">
                            {% if current_user.plan == 'free' %}
                                <span class="badge bg-secondary">Gratuit</span>
                            {% elif current_user.plan == 'premium' %}
                                <span class="badge bg-primary">Premium</span>
                            {% elif current_user.plan == 'pro' %}
                                <span class="badge bg-success">Pro</span>
                            {% endif %}
                        </div>
                    </div>
                    
                    <div class="row mb-4">
                        <div class="col-md-4">
                            <strong>Clips générés ce mois-ci :</strong>
                        </div>
                        <div class="col-md-8">
                            {{ current_user.clips_generated_this_month }} / 
                            {% if current_user.plan == 'pro' %}
                                <span>Illimité</span>
                            {% else %}
                                <span>{{ current_user.get_clip_limit() }}</span>
                            {% endif %}
                        </div>
                    </div>
                    
                    <div class="row mb-4">
                        <div class="col-md-4">
                            <strong>Date d'inscription :</strong>
                        </div>
                        <div class="col-md-8">
                            {{ current_user.created_at.strftime('%d/%m/%Y') }}
                        </div>
                    </div>
                    
                    <div class="row mb-4">
                        <div class="col-md-4">
                            <strong>Dernière connexion :</strong>
                        </div>
                        <div class="col-md-8">
                            {{ current_user.last_login.strftime('%d/%m/%Y à %H:%M') }}
                        </div>
                    </div>
                </div>
                <div class="card-footer">
                    <div class="d-flex justify-content-between">
                        <a href="{{ url_for('auth.change_password') }}" class="btn btn-outline-primary">Changer mon mot de passe</a>
                        <a href="{{ url_for('api.pricing') }}" class="btn btn-primary">Gérer mon abonnement</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

## 5. Création du template pour la page de mot de passe oublié (`forgot_password.html`)

```html
{% extends "base.html" %}

{% block title %}Mot de passe oublié - Générateur de clips "Best Of"{% endblock %}

{% block content %}
<div class="container">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="form-container">
                <h2 class="text-center mb-4">Réinitialisation du mot de passe</h2>
                
                {% if error %}
                <div class="alert alert-danger" role="alert">
                    {{ error }}
                </div>
                {% endif %}
                
                {% if success %}
                <div class="alert alert-success" role="alert">
                    {{ success }}
                </div>
                {% endif %}
                
                <form method="post" action="{{ url_for('auth.forgot_password') }}">
                    <div class="mb-3">
                        <label for="email" class="form-label">Email</label>
                        <input type="email" class="form-control" id="email" name="email" required>
                        <div class="form-text">Nous vous enverrons un lien de réinitialisation à cette adresse.</div>
                    </div>
                    
                    <div class="d-grid gap-2">
                        <button type="submit" class="btn btn-primary">Réinitialiser mon mot de passe</button>
                    </div>
                </form>
                
                <hr>
                
                <div class="text-center">
                    <a href="{{ url_for('auth.login') }}">Retour à la connexion</a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

## 6. Mise à jour du template de base (`base.html`)

Ajouter la gestion de l'authentification dans la barre de navigation :

```html
<!-- Partie à ajouter dans la barre de navigation -->
<ul class="navbar-nav ms-auto">
    {% if current_user.is_authenticated %}
        <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                {{ current_user.name }}
            </a>
            <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="navbarDropdown">
                <li><a class="dropdown-item" href="{{ url_for('api.my_clips') }}">Mes clips</a></li>
                <li><a class="dropdown-item" href="{{ url_for('auth.profile') }}">Mon profil</a></li>
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item" href="{{ url_for('auth.logout') }}">Déconnexion</a></li>
            </ul>
        </li>
    {% else %}
        <li class="nav-item">
            <a class="nav-link" href="{{ url_for('auth.login') }}">Connexion</a>
        </li>
        <li class="nav-item">
            <a class="nav-link btn btn-primary text-white" href="{{ url_for('auth.register') }}">Inscription</a>
        </li>
    {% endif %}
</ul>
```

## 7. Mise à jour des contrôleurs de clips (`clip_controller.py`)

Modifier les fonctions pour prendre en compte l'utilisateur connecté :

```python
def generate_short_clip(url, transitions=True, user_id=None):
    """
    Génère un clip court à partir d'une URL YouTube.
    
    Args:
        url: URL de la vidéo YouTube
        transitions: Booléen indiquant si les transitions doivent être ajoutées
        user_id: ID de l'utilisateur qui génère le clip
        
    Returns:
        ID du clip généré
    """
    # Créer un nouvel enregistrement de clip dans la base de données
    clip = Clip(
        youtube_url=url,
        mode='short',
        transitions=transitions,
        status='pending'
    )
    
    if user_id:
        clip.user_id = user_id
    
    db.session.add(clip)
    db.session.commit()
    
    # Lancer la génération du clip en arrière-plan
    # ...
    
    return clip.id

def generate_long_clip(url, transitions=True, user_id=None):
    """
    Génère un clip long à partir d'une URL YouTube.
    
    Args:
        url: URL de la vidéo YouTube
        transitions: Booléen indiquant si les transitions doivent être ajoutées
        user_id: ID de l'utilisateur qui génère le clip
        
    Returns:
        ID du clip généré
    """
    # Créer un nouvel enregistrement de clip dans la base de données
    clip = Clip(
        youtube_url=url,
        mode='long',
        transitions=transitions,
        status='pending'
    )
    
    if user_id:
        clip.user_id = user_id
    
    db.session.add(clip)
    db.session.commit()
    
    # Lancer la génération du clip en arrière-plan
    # ...
    
    return clip.id
```

## 8. Mise à jour de la configuration (`config.py`)

Ajouter les configurations nécessaires pour Flask-Login :

```python
# Ajouter dans la classe Config
SESSION_TYPE = 'filesystem'
PERMANENT_SESSION_LIFETIME = timedelta(days=31)
REMEMBER_COOKIE_DURATION = timedelta(days=31)
```

## 9. Dépendances requises

Installer les dépendances nécessaires :

```bash
pip install flask-login
```
