#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests pour les fonctionnalités de monétisation du générateur de clips "Best Of".
"""

import unittest
from flask import Flask
from flask_testing import TestCase
from api import create_app
from api.models import db, User, Clip
from datetime import datetime, timedelta
import os
import tempfile

class MonetizationTestCase(TestCase):
    """Tests pour les fonctionnalités de monétisation."""
    
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
        
        # Créer des utilisateurs de test avec différents plans
        free_user = User(
            name='Free User',
            email='free@example.com',
            plan='free',
            clips_generated_this_month=2
        )
        free_user.set_password('password123')
        
        premium_user = User(
            name='Premium User',
            email='premium@example.com',
            plan='premium',
            clips_generated_this_month=15,
            subscription_start_date=datetime.utcnow() - timedelta(days=15),
            subscription_end_date=datetime.utcnow() + timedelta(days=15)
        )
        premium_user.set_password('password123')
        
        pro_user = User(
            name='Pro User',
            email='pro@example.com',
            plan='pro',
            clips_generated_this_month=25,
            subscription_start_date=datetime.utcnow() - timedelta(days=15),
            subscription_end_date=datetime.utcnow() + timedelta(days=15),
            custom_logo='/path/to/logo.png'
        )
        pro_user.set_password('password123')
        
        db.session.add_all([free_user, premium_user, pro_user])
        db.session.commit()
    
    def tearDown(self):
        """Nettoie la base de données après chaque test."""
        db.session.remove()
        db.drop_all()
    
    def test_plan_limits(self):
        """Teste les limites de génération de clips selon le plan."""
        free_user = User.query.filter_by(email='free@example.com').first()
        premium_user = User.query.filter_by(email='premium@example.com').first()
        pro_user = User.query.filter_by(email='pro@example.com').first()
        
        # Vérifier les limites de clips
        self.assertEqual(free_user.get_clip_limit(), 3)
        self.assertEqual(premium_user.get_clip_limit(), 20)
        self.assertEqual(pro_user.get_clip_limit(), float('inf'))
        
        # Vérifier si les utilisateurs peuvent générer des clips
        self.assertTrue(free_user.can_generate_clip('short'))  # 2/3 clips générés
        self.assertFalse(free_user.can_generate_clip('long'))  # Plan gratuit ne permet pas les clips longs
        
        self.assertTrue(premium_user.can_generate_clip('short'))  # 15/20 clips générés
        self.assertTrue(premium_user.can_generate_clip('long'))  # Plan premium permet les clips longs
        
        self.assertTrue(pro_user.can_generate_clip('short'))  # Clips illimités
        self.assertTrue(pro_user.can_generate_clip('long'))  # Plan pro permet les clips longs
        
        # Simuler l'atteinte de la limite pour l'utilisateur gratuit
        free_user.clips_generated_this_month = 3
        db.session.commit()
        self.assertFalse(free_user.can_generate_clip('short'))  # 3/3 clips générés
        
        # Simuler l'atteinte de la limite pour l'utilisateur premium
        premium_user.clips_generated_this_month = 20
        db.session.commit()
        self.assertFalse(premium_user.can_generate_clip('short'))  # 20/20 clips générés
        
        # L'utilisateur pro peut toujours générer des clips
        pro_user.clips_generated_this_month = 100
        db.session.commit()
        self.assertTrue(pro_user.can_generate_clip('short'))  # Clips illimités
    
    def test_video_quality(self):
        """Teste la qualité vidéo selon le plan."""
        free_user = User.query.filter_by(email='free@example.com').first()
        premium_user = User.query.filter_by(email='premium@example.com').first()
        pro_user = User.query.filter_by(email='pro@example.com').first()
        
        self.assertEqual(free_user.get_video_quality(), '720p')
        self.assertEqual(premium_user.get_video_quality(), '1080p')
        self.assertEqual(pro_user.get_video_quality(), '4k')
    
    def test_watermark(self):
        """Teste la présence de filigrane selon le plan."""
        free_user = User.query.filter_by(email='free@example.com').first()
        premium_user = User.query.filter_by(email='premium@example.com').first()
        pro_user = User.query.filter_by(email='pro@example.com').first()
        
        self.assertTrue(free_user.has_watermark())
        self.assertFalse(premium_user.has_watermark())
        self.assertFalse(pro_user.has_watermark())
    
    def test_custom_features(self):
        """Teste les fonctionnalités personnalisées selon le plan."""
        free_user = User.query.filter_by(email='free@example.com').first()
        premium_user = User.query.filter_by(email='premium@example.com').first()
        pro_user = User.query.filter_by(email='pro@example.com').first()
        
        # Transitions personnalisées
        self.assertFalse(free_user.can_use_custom_transitions())
        self.assertTrue(premium_user.can_use_custom_transitions())
        self.assertTrue(pro_user.can_use_custom_transitions())
        
        # Logo personnalisé
        self.assertFalse(free_user.can_use_custom_logo())
        self.assertFalse(premium_user.can_use_custom_logo())
        self.assertTrue(pro_user.can_use_custom_logo())
        
        # API dédiée
        self.assertFalse(free_user.can_access_api())
        self.assertFalse(premium_user.can_access_api())
        self.assertTrue(pro_user.can_access_api())
    
    def test_clip_storage(self):
        """Teste la durée de stockage des clips selon le plan."""
        free_user = User.query.filter_by(email='free@example.com').first()
        premium_user = User.query.filter_by(email='premium@example.com').first()
        pro_user = User.query.filter_by(email='pro@example.com').first()
        
        self.assertEqual(free_user.get_clip_storage_days(), 30)
        self.assertEqual(premium_user.get_clip_storage_days(), 90)
        self.assertEqual(pro_user.get_clip_storage_days(), 3650)  # 10 ans
    
    def test_clip_expiration(self):
        """Teste l'expiration des clips."""
        free_user = User.query.filter_by(email='free@example.com').first()
        
        # Créer un clip expiré
        expired_clip = Clip(
            user_id=free_user.id,
            youtube_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            title='Test Clip',
            mode='short',
            status='completed',
            expiration_date=datetime.utcnow() - timedelta(days=1)
        )
        
        # Créer un clip non expiré
        valid_clip = Clip(
            user_id=free_user.id,
            youtube_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            title='Test Clip 2',
            mode='short',
            status='completed',
            expiration_date=datetime.utcnow() + timedelta(days=10)
        )
        
        db.session.add_all([expired_clip, valid_clip])
        db.session.commit()
        
        self.assertTrue(expired_clip.is_expired())
        self.assertFalse(valid_clip.is_expired())
    
    def test_subscription_status(self):
        """Teste le statut des abonnements."""
        free_user = User.query.filter_by(email='free@example.com').first()
        premium_user = User.query.filter_by(email='premium@example.com').first()
        pro_user = User.query.filter_by(email='pro@example.com').first()
        
        # L'utilisateur gratuit a toujours un abonnement "actif"
        self.assertTrue(free_user.is_subscription_active())
        
        # Les utilisateurs premium et pro ont des abonnements actifs
        self.assertTrue(premium_user.is_subscription_active())
        self.assertTrue(pro_user.is_subscription_active())
        
        # Simuler un abonnement expiré
        expired_user = User(
            name='Expired User',
            email='expired@example.com',
            plan='premium',
            subscription_start_date=datetime.utcnow() - timedelta(days=45),
            subscription_end_date=datetime.utcnow() - timedelta(days=15)
        )
        expired_user.set_password('password123')
        db.session.add(expired_user)
        db.session.commit()
        
        self.assertFalse(expired_user.is_subscription_active())
    
    def test_monthly_counter_reset(self):
        """Teste la réinitialisation du compteur mensuel."""
        free_user = User.query.filter_by(email='free@example.com').first()
        
        self.assertEqual(free_user.clips_generated_this_month, 2)
        
        free_user.reset_monthly_counter()
        
        self.assertEqual(free_user.clips_generated_this_month, 0)
    
    def test_plan_upgrade(self):
        """Teste la mise à niveau du plan."""
        free_user = User.query.filter_by(email='free@example.com').first()
        
        self.assertEqual(free_user.plan, 'free')
        self.assertIsNone(free_user.subscription_start_date)
        self.assertIsNone(free_user.subscription_end_date)
        
        # Mettre à niveau vers premium
        free_user.upgrade_plan('premium')
        
        self.assertEqual(free_user.plan, 'premium')
        self.assertIsNotNone(free_user.subscription_start_date)
        self.assertIsNotNone(free_user.subscription_end_date)
        
        # Vérifier que la date de fin est environ 30 jours après la date de début
        delta = free_user.subscription_end_date - free_user.subscription_start_date
        self.assertAlmostEqual(delta.days, 30, delta=1)

if __name__ == '__main__':
    unittest.main()
