from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.auth import exige_permissao
from app.db import get_db
from app.services import autorizacao_service, visitante_service as servico
from app.services.erros import ErroNegocio

visitantes_bp = Blueprint("visitantes", __name__, url_prefix="/visitantes")

CAMPOS = ("nome", "cpf", "telefone", "pessoa_visitada_id", "motivo")


def _formulario(db, titulo, valores, editando=None):
    atual = editando["pessoa_visitada_id"] if editando else None
    return render_template("visitantes/form.html", titulo=titulo, valores=valores, editando=editando,
                           pessoas=servico.listar_pessoas_visitaveis(db, atual))


@visitantes_bp.route("/")
@exige_permissao("cadastrar_visitantes")
def listar():
    busca = request.args.get("busca", "").strip()
    return render_template("visitantes/lista.html", busca=busca,
                           visitantes=servico.listar_visitantes(get_db(), busca))


@visitantes_bp.route("/novo", methods=["GET", "POST"])
@exige_permissao("cadastrar_visitantes")
def novo():
    db = get_db()
    valores = {c: "" for c in CAMPOS}
    if request.method == "POST":
        valores = {c: request.form.get(c, "") for c in CAMPOS}
        try:
            servico.criar_visitante(db, **valores)
            flash("Visitante cadastrado. A solicitação está aguardando autorização.", "sucesso")
            return redirect(url_for("visitantes.listar"))
        except ErroNegocio as erro:
            flash(str(erro), "erro")
    return _formulario(db, "Novo visitante", valores)


# Alterar um visitante já cadastrado é restrito ao administrador (RN-05).
@visitantes_bp.route("/<int:visitante_id>/editar", methods=["GET", "POST"])
@exige_permissao("administrar_registros")
def editar(visitante_id):
    db = get_db()
    visitante = servico.buscar_visitante(db, visitante_id)
    if visitante is None:
        abort(404)
    valores = {"nome": visitante["nome"], "cpf": visitante["cpf"],
               "telefone": visitante["telefone"] or "", "motivo": visitante["motivo"],
               "pessoa_visitada_id": str(visitante["pessoa_visitada_id"])}
    if request.method == "POST":
        valores = {c: request.form.get(c, "") for c in CAMPOS}
        try:
            servico.atualizar_visitante(db, visitante_id, **valores)
            flash("Visitante atualizado com sucesso.", "sucesso")
            return redirect(url_for("visitantes.listar"))
        except ErroNegocio as erro:
            flash(str(erro), "erro")
    return _formulario(db, "Editar visitante", valores, editando=visitante)


@visitantes_bp.route("/<int:visitante_id>/solicitar", methods=["POST"])
@exige_permissao("cadastrar_visitantes")
def solicitar(visitante_id):
    try:
        autorizacao_service.solicitar_nova(get_db(), visitante_id)
        flash("Nova solicitação enviada para autorização.", "sucesso")
    except ErroNegocio as erro:
        flash(str(erro), "erro")
    return redirect(url_for("visitantes.listar"))
