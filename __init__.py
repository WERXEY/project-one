#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Initialisation de l'application Flask pour l'API du générateur de clips "Best Of".
"""

from flask import Flask
from flask_cors import CORS

def create_app(app=None):
    """
    Crée et configure l'application Flask.
    
    Args:
        app: Instance Flask existante ou None pour en créer une nouvelle
        
    Returns:
        L'application Flask configurée
    """
    if app is None:
        app = Flask(__name__)
    
    # Configuration de l'application
    app.config.from_object('config.Config')
    
    # Activation de CORS pour permettre les requêtes cross-origin
    CORS(app)
    
    # Enregistrement des blueprints
    from api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app
