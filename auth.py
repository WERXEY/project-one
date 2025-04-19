#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gestion de l'authentification pour le générateur de clips "Best Of".
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from api.models import db, User
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('api.index'))
        
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
            next_page = url_for('api.index')
            
        return redirect(next_page)
        
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('api.index'))
        
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
        
        return redirect(url_for('api.index'))
        
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('api.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation des données
        if not current_password or not new_password or not confirm_password:
            return render_template('change_password.html', error='Tous les champs sont obligatoires')
            
        if not current_user.check_password(current_password):
            return render_template('change_password.html', error='Mot de passe actuel incorrect')
            
        if new_password != confirm_password:
            return render_template('change_password.html', error='Les nouveaux mots de passe ne correspondent pas')
            
        if len(new_password) < 8:
            return render_template('change_password.html', error='Le mot de passe doit contenir au moins 8 caractères')
            
        # Mise à jour du mot de passe
        current_user.set_password(new_password)
        db.session.commit()
        
        flash('Votre mot de passe a été mis à jour avec succès.')
        return redirect(url_for('auth.profile'))
        
    return render_template('change_password.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('api.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            return render_template('forgot_password.html', error='Veuillez saisir votre adresse email')
            
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Pour des raisons de sécurité, ne pas indiquer si l'email existe ou non
            return render_template('forgot_password.html', success='Si votre adresse email est associée à un compte, vous recevrez un lien de réinitialisation.')
            
        # TODO: Implémenter l'envoi d'email avec un token de réinitialisation
        # Pour l'instant, afficher simplement un message de succès
        return render_template('forgot_password.html', success='Si votre adresse email est associée à un compte, vous recevrez un lien de réinitialisation.')
        
    return render_template('forgot_password.html')
