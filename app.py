#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Point d'entrée de l'application pour le générateur de clips "Best Of".
Ce fichier initialise l'application Flask et configure les routes de l'API.
"""

from flask import Flask
from api import create_app

# Création de l'application Flask
app = Flask(__name__)
app = create_app(app)

if __name__ == "__main__":
    # Démarrage du serveur en mode développement
    app.run(host="0.0.0.0", port=5000, debug=True)
