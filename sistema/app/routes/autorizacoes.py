from datetime import date

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from app.auth import exige_permissao
from app.db import get_db
from app.services import autorizacao_service as servico
from app.services.erros import ErroNegocio

autorizacoes_bp = Blueprint("autorizacoes", __name__, url_prefix="/autorizacoes")

FILTROS = (("pendente", "Pendentes"), ("aprovada", "Autorizadas"),
           ("negada", "Negadas"), ("todas", "Todas"))


@autorizacoes_bp.route("/")
@exige_permissao("autorizar_visitantes")
def listar():
    status = request.args.get("status", "pendente")
    if status not in dict(FILTROS):
        status = "pendente"
    db = get_db()
    return render_template("autorizacoes/lista.html", status=status, filtros=FILTROS,
                           autorizacoes=servico.listar_autorizacoes(db, status),
                           contagem=servico.contar_por_status(db))


@autorizacoes_bp.route("/<int:autorizacao_id>", methods=["GET", "POST"])
@exige_permissao("autorizar_visitantes")
def decidir(autorizacao_id):
    db = get_db()
    autorizacao = servico.buscar_autorizacao(db, autorizacao_id)
    if autorizacao is None:
        abort(404)
    valores = {"data_inicio": date.today().isoformat(), "data_fim": "", "observacao": ""}
    if request.method == "POST":
        valores = {c: request.form.get(c, "") for c in valores}
        acao = request.form.get("acao")
        try:
            if acao == "aprovar":
                servico.aprovar(db, autorizacao_id, g.usuario["id"], valores["data_inicio"],
                                valores["data_fim"], valores["observacao"])
                flash("Visitante autorizado. A decisão foi registrada.", "sucesso")
            elif acao == "negar":
                servico.negar(db, autorizacao_id, g.usuario["id"], valores["observacao"])
                flash("Entrada negada. A decisão foi registrada.", "sucesso")
            else:
                raise ErroNegocio("Escolha autorizar ou negar.")
            return redirect(url_for("autorizacoes.listar"))
        except ErroNegocio as erro:
            flash(str(erro), "erro")
            autorizacao = servico.buscar_autorizacao(db, autorizacao_id)   # pode ter mudado
    return render_template("autorizacoes/decidir.html", autorizacao=autorizacao, valores=valores,
                           hoje=date.today().isoformat())
