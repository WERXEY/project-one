#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests pour le système d'authentification du générateur de clips "Best Of".
"""

import unittest
from flask import Flask
from flask_testing import TestCase
from api import create_app
from api.models import db, User
import os
import tempfile

class AuthTestCase(TestCase):
    """Tests pour le système d'authentification."""
    
    def create_app(self):
        """Crée une instance de l'application pour les tests."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = 'test-key'
        app.config['WTF_CSRF_ENABLED'] = False
        
        app = create_app(app)
        return app
    
    def setUp(self):
        """Initialise la base de données avant chaque test."""
        db.create_all()
        
        # Créer un utilisateur de test
        user = User(
            name='Test User',
            email='test@example.com',
            plan='free'
        )
        user.set_password('password123')
        
        db.session.add(user)
        db.session.commit()
    
    def tearDown(self):
        """Nettoie la base de données après chaque test."""
        db.session.remove()
        db.drop_all()
    
    def test_register(self):
        """Teste l'inscription d'un nouvel utilisateur."""
        response = self.client.post('/register', data={
            'name': 'New User',
            'email': 'new@example.com',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123',
            'plan': 'free',
            'terms': 'on'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que l'utilisateur a été créé
        user = User.query.filter_by(email='new@example.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.name, 'New User')
        self.assertEqual(user.plan, 'free')
    
    def test_login(self):
        """Teste la connexion d'un utilisateur."""
        response = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123',
            'remember': 'on'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que l'utilisateur est connecté
        with self.client.session_transaction() as session:
            self.assertIn('_user_id', session)
    
    def test_login_invalid_credentials(self):
        """Teste la connexion avec des identifiants invalides."""
        response = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'wrongpassword',
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Identifiants invalides', response.data)
        
        # Vérifier que l'utilisateur n'est pas connecté
        with self.client.session_transaction() as session:
            self.assertNotIn('_user_id', session)
    
    def test_logout(self):
        """Teste la déconnexion d'un utilisateur."""
        # D'abord se connecter
        self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123',
        })
        
        # Puis se déconnecter
        response = self.client.get('/logout', follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que l'utilisateur est déconnecté
        with self.client.session_transaction() as session:
            self.assertNotIn('_user_id', session)
    
    def test_profile_access(self):
        """Teste l'accès à la page de profil."""
        # D'abord se connecter
        self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123',
        })
        
        # Accéder à la page de profil
        response = self.client.get('/profile')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test User', response.data)
    
    def test_profile_access_unauthenticated(self):
        """Teste l'accès à la page de profil sans être connecté."""
        response = self.client.get('/profile', follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Veuillez vous connecter', response.data)
    
    def test_change_password(self):
        """Teste le changement de mot de passe."""
        # D'abord se connecter
        self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123',
        })
        
        # Changer le mot de passe
        response = self.client.post('/change-password', data={
            'current_password': 'password123',
            'new_password': 'newpassword456',
            'confirm_password': 'newpassword456',
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que le mot de passe a été changé
        user = User.query.filter_by(email='test@example.com').first()
        self.assertTrue(user.check_password('newpassword456'))

if __name__ == '__main__':
    unittest.main()
