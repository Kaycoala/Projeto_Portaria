from flask import Blueprint, render_template

from app.auth import pode
from app.db import get_db
from app.services import dashboard_service

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def inicio():
    """Dashboard: os números vêm do banco. Cada perfil vê só o que pode usar (RNF-04)."""
    resumo, ultimas = None, []
    if pode("ver_painel"):
        db = get_db()
        resumo = dashboard_service.resumo(db)
        if pode("consultar_historico"):
            ultimas = dashboard_service.ultimas_movimentacoes(db)
    return render_template("index.html", resumo=resumo, ultimas=ultimas)
