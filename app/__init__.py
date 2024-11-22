from flask import Flask
from app.controllers.garbage_controller import garbage_bp

def create_app():
    """Cria a aplicação Flask."""
    app = Flask(__name__)
    app.register_blueprint(garbage_bp)
    return app
