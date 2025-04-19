#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration pour l'API du générateur de clips "Best Of".
"""

import os

class Config:
    """
    Configuration de base pour l'application.
    """
    # Clé secrète pour la sécurité de l'application
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-testing-only')
    
    # Configuration du stockage des clips
    CLIPS_STORAGE_DIR = os.environ.get('CLIPS_STORAGE_DIR', '/home/ubuntu/clips_storage')
    
    # Configuration de l'API YouTube
    YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY', '')
    
    # Paramètres de génération des clips
    MAX_CLIP_DURATION = 300  # Durée maximale d'un clip en secondes
    DEFAULT_TRANSITIONS = True  # Transitions activées par défaut
    
    # Configuration du serveur
    DEBUG = True
    TESTING = False
    
    # Limites de l'API
    RATE_LIMIT = 100  # Nombre maximum de requêtes par heure
    MAX_CONCURRENT_GENERATIONS = 5  # Nombre maximum de générations simultanées

class TestingConfig(Config):
    """
    Configuration pour les tests.
    """
    TESTING = True
    CLIPS_STORAGE_DIR = '/home/ubuntu/test_clips_storage'
    
    # Paramètres spécifiques aux tests
    TEST_YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Vidéo de test
