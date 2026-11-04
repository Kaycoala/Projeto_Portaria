from pathlib import Path

from flask import Flask


def create_app(config_teste=None):
    """Cria e configura a aplicação Flask."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "troque-esta-chave-em-producao"
    app.config["DATABASE"] = str(Path(app.instance_path) / "portaria.db")
    if config_teste:
        app.config.update(config_teste)

    from app import db
    db.init_app(app)
    # Primeira execução: cria o banco automaticamente se ele ainda não existir.
    if not Path(app.config["DATABASE"]).exists():
        db.criar_banco(app.config["DATABASE"])

    from app.routes.main import main_bp
    app.register_blueprint(main_bp)

    return app
