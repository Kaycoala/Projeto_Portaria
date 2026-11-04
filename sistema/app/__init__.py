from flask import Flask


def create_app():
    """Cria e configura a aplicação Flask."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "troque-esta-chave-em-producao"

    from app.routes.main import main_bp
    app.register_blueprint(main_bp)

    return app
