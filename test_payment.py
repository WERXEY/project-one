#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests pour le système de paiement du générateur de clips "Best Of".
"""

import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from flask_testing import TestCase
from api import create_app
from api.models import db, User
from api.payment import fulfill_order, update_subscription, cancel_subscription
from datetime import datetime, timedelta
import os
import tempfile
import json

class PaymentTestCase(TestCase):
    """Tests pour le système de paiement."""
    
    def create_app(self):
        """Crée une instance de l'application pour les tests."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = 'test-key'
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['STRIPE_PUBLIC_KEY'] = 'pk_test_test'
        app.config['STRIPE_SECRET_KEY'] = 'sk_test_test'
        
        app = create_app(app)
        return app
    
    def setUp(self):
        """Initialise la base de données avant chaque test."""
        db.create_all()
        
        # Créer un utilisateur de test
        user = User(
            id='test_user_id',
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
    
    def test_checkout_page(self):
        """Teste l'accès à la page de paiement."""
        # D'abord se connecter
        self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123',
        })
        
        # Accéder à la page de paiement pour le plan premium
        response = self.client.get('/checkout/premium')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Premium', response.data)
        self.assertIn(b'9,99', response.data)
    
    def test_checkout_page_unauthenticated(self):
        """Teste l'accès à la page de paiement sans être connecté."""
        response = self.client.get('/checkout/premium', follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Veuillez vous connecter', response.data)
    
    @patch('stripe.checkout.Session.create')
    def test_create_checkout_session(self, mock_create):
        """Teste la création d'une session de paiement."""
        # Configurer le mock
        mock_create.return_value = MagicMock(id='test_session_id')
        
        # D'abord se connecter
        self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123',
        })
        
        # Créer une session de paiement
        response = self.client.post('/create-checkout-session', data={
            'plan': 'premium'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['id'], 'test_session_id')
        
        # Vérifier que Stripe a été appelé avec les bons paramètres
        mock_create.assert_called_once()
        args, kwargs = mock_create.call_args
        self.assertEqual(kwargs['mode'], 'subscription')
        self.assertEqual(kwargs['client_reference_id'], 'test_user_id')
        self.assertEqual(kwargs['customer_email'], 'test@example.com')
    
    @patch('stripe.checkout.Session.retrieve')
    @patch('stripe.Subscription.retrieve')
    def test_payment_success(self, mock_sub_retrieve, mock_session_retrieve):
        """Teste le traitement d'un paiement réussi."""
        # Configurer les mocks
        mock_session = MagicMock()
        mock_session.subscription = 'test_subscription_id'
        mock_session_retrieve.return_value = mock_session
        
        mock_subscription = MagicMock()
        mock_subscription.plan.id = 'price_premium'
        mock_subscription.id = 'test_subscription_id'
        mock_subscription.current_period_start = int(datetime.now().timestamp())
        mock_subscription.current_period_end = int((datetime.now() + timedelta(days=30)).timestamp())
        mock_sub_retrieve.return_value = mock_subscription
        
        # D'abord se connecter
        self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123',
        })
        
        # Simuler un retour de paiement réussi
        response = self.client.get('/success?session_id=test_session_id', follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'activ', response.data)  # "activé" en français
        
        # Vérifier que l'utilisateur a été mis à jour
        user = User.query.filter_by(email='test@example.com').first()
        self.assertEqual(user.plan, 'premium')
        self.assertEqual(user.payment_id, 'test_subscription_id')
        self.assertIsNotNone(user.subscription_start_date)
        self.assertIsNotNone(user.subscription_end_date)
    
    def test_payment_cancel(self):
        """Teste l'annulation d'un paiement."""
        # D'abord se connecter
        self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123',
        })
        
        # Simuler une annulation de paiement
        response = self.client.get('/cancel', follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'annul', response.data)  # "annulé" en français
    
    def test_fulfill_order(self):
        """Teste la fonction fulfill_order."""
        # Créer une session de paiement simulée
        session = {
            'client_reference_id': 'test_user_id',
            'subscription': 'test_subscription_id'
        }
        
        # Créer un abonnement simulé
        subscription = MagicMock()
        subscription.plan.id = 'price_premium'
        subscription.id = 'test_subscription_id'
        subscription.current_period_start = int(datetime.now().timestamp())
        subscription.current_period_end = int((datetime.now() + timedelta(days=30)).timestamp())
        
        # Patcher stripe.Subscription.retrieve
        with patch('stripe.Subscription.retrieve', return_value=subscription):
            # Appeler la fonction
            fulfill_order(session)
        
        # Vérifier que l'utilisateur a été mis à jour
        user = User.query.filter_by(id='test_user_id').first()
        self.assertEqual(user.plan, 'premium')
        self.assertEqual(user.payment_id, 'test_subscription_id')
        self.assertIsNotNone(user.subscription_start_date)
        self.assertIsNotNone(user.subscription_end_date)
    
    def test_update_subscription(self):
        """Teste la fonction update_subscription."""
        # Créer un utilisateur avec un abonnement
        user = User.query.filter_by(id='test_user_id').first()
        user.plan = 'premium'
        user.payment_id = 'test_subscription_id'
        user.subscription_start_date = datetime.now() - timedelta(days=15)
        user.subscription_end_date = datetime.now() + timedelta(days=15)
        db.session.commit()
        
        # Créer un abonnement simulé avec un plan mis à jour
        subscription = MagicMock()
        subscription.id = 'test_subscription_id'
        subscription.plan.id = 'price_pro'
        subscription.current_period_start = int((datetime.now() - timedelta(days=1)).timestamp())
        subscription.current_period_end = int((datetime.now() + timedelta(days=29)).timestamp())
        
        # Appeler la fonction
        update_subscription(subscription)
        
        # Vérifier que l'utilisateur a été mis à jour
        user = User.query.filter_by(id='test_user_id').first()
        self.assertEqual(user.plan, 'pro')
        self.assertIsNotNone(user.subscription_start_date)
        self.assertIsNotNone(user.subscription_end_date)
    
    def test_cancel_subscription(self):
        """Teste la fonction cancel_subscription."""
        # Créer un utilisateur avec un abonnement
        user = User.query.filter_by(id='test_user_id').first()
        user.plan = 'premium'
        user.payment_id = 'test_subscription_id'
        user.subscription_start_date = datetime.now() - timedelta(days=15)
        user.subscription_end_date = datetime.now() + timedelta(days=15)
        db.session.commit()
        
        # Créer un abonnement simulé
        subscription = MagicMock()
        subscription.id = 'test_subscription_id'
        
        # Appeler la fonction
        cancel_subscription(subscription)
        
        # Vérifier que l'utilisateur conserve son plan jusqu'à la fin de la période
        user = User.query.filter_by(id='test_user_id').first()
        self.assertEqual(user.plan, 'premium')
        self.assertEqual(user.payment_id, 'test_subscription_id')
        self.assertIsNotNone(user.subscription_start_date)
        self.assertIsNotNone(user.subscription_end_date)

if __name__ == '__main__':
    unittest.main()
