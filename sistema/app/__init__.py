import secrets
from pathlib import Path

from flask import Flask, g, render_template


def _chave_secreta(pasta):
    """Gera (uma vez) e reaproveita a chave que protege a sessão de login."""
    arquivo = Path(pasta) / "chave_secreta.txt"
    if not arquivo.exists():
        arquivo.write_text(secrets.token_hex(32))
    return arquivo.read_text().strip()


def create_app(config_teste=None):
    """Cria e configura a aplicação Flask."""
    app = Flask(__name__)
    app.config["DATABASE"] = str(Path(app.instance_path) / "portaria.db")
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    if config_teste:
        app.config.update(config_teste)
    if not app.config.get("SECRET_KEY"):
        Path(app.instance_path).mkdir(parents=True, exist_ok=True)
        app.config["SECRET_KEY"] = _chave_secreta(app.instance_path)

    from app import db
    db.init_app(app)
    # Primeira execução: cria o banco automaticamente se ele ainda não existir.
    if not Path(app.config["DATABASE"]).exists():
        db.criar_banco(app.config["DATABASE"])

    from app.auth import exigir_login, pode
    from app.permissoes import nome_perfil
    from app.seguranca import token_csrf, verificar_csrf

    app.before_request(verificar_csrf)
    app.before_request(exigir_login)
    app.jinja_env.filters["nome_perfil"] = nome_perfil

    from app.services import autorizacao_service, pessoa_service, veiculo_service
    app.jinja_env.filters["nome_status"] = autorizacao_service.nome_status
    app.jinja_env.filters["data_br"] = autorizacao_service.formatar_data
    app.jinja_env.filters["nome_tipo"] = pessoa_service.nome_tipo
    app.jinja_env.filters["formatar_cpf"] = pessoa_service.formatar_cpf
    app.jinja_env.filters["formatar_placa"] = veiculo_service.formatar_placa

    @app.context_processor
    def variaveis_dos_templates():
        return {"usuario": g.get("usuario"), "pode": pode, "csrf_token": token_csrf}

    from app.routes.acessos import acessos_bp
    from app.routes.auth import auth_bp
    from app.routes.autorizacoes import autorizacoes_bp
    from app.routes.historico import historico_bp
    from app.routes.main import main_bp
    from app.routes.ocorrencias import ocorrencias_bp
    from app.routes.pessoas import pessoas_bp
    from app.routes.relatorios import relatorios_bp
    from app.routes.usuarios import usuarios_bp
    from app.routes.veiculos import veiculos_bp
    from app.routes.visitantes import visitantes_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(pessoas_bp)
    app.register_blueprint(veiculos_bp)
    app.register_blueprint(visitantes_bp)
    app.register_blueprint(autorizacoes_bp)
    app.register_blueprint(acessos_bp)
    app.register_blueprint(historico_bp)
    app.register_blueprint(ocorrencias_bp)
    app.register_blueprint(relatorios_bp)

    @app.errorhandler(400)
    def erro_400(e):
        return render_template("erro.html", codigo=400, mensagem=e.description), 400

    @app.errorhandler(403)
    def erro_403(e):
        return render_template("erro.html", codigo=403,
                               mensagem="Você não tem permissão para acessar esta página."), 403

    @app.errorhandler(404)
    def erro_404(e):
        return render_template("erro.html", codigo=404, mensagem="Página não encontrada."), 404

    return app
