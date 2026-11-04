from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.auth import exige_permissao
from app.db import get_db
from app.services import pessoa_service as servico
from app.services.erros import ErroNegocio

pessoas_bp = Blueprint("pessoas", __name__, url_prefix="/pessoas")

CAMPOS = ("nome", "cpf", "telefone", "email", "endereco_setor", "tipo")


def _formulario(titulo, valores, editando=None):
    return render_template("pessoas/form.html", titulo=titulo, valores=valores,
                           editando=editando, tipos=servico.TIPOS)


@pessoas_bp.route("/")
@exige_permissao("gerenciar_cadastros")
def listar():
    busca = request.args.get("busca", "").strip()
    return render_template("pessoas/lista.html", busca=busca,
                           pessoas=servico.listar_pessoas(get_db(), busca))


@pessoas_bp.route("/nova", methods=["GET", "POST"])
@exige_permissao("gerenciar_cadastros")
def nova():
    valores = {c: "" for c in CAMPOS}
    if request.method == "POST":
        valores = {c: request.form.get(c, "") for c in CAMPOS}
        try:
            servico.criar_pessoa(get_db(), **valores)
            flash("Pessoa cadastrada com sucesso.", "sucesso")
            return redirect(url_for("pessoas.listar"))
        except ErroNegocio as erro:
            flash(str(erro), "erro")
    return _formulario("Nova pessoa", valores)


@pessoas_bp.route("/<int:pessoa_id>/editar", methods=["GET", "POST"])
@exige_permissao("gerenciar_cadastros")
def editar(pessoa_id):
    db = get_db()
    pessoa = servico.buscar_pessoa(db, pessoa_id)
    if pessoa is None:
        abort(404)
    valores = {c: pessoa[c] or "" for c in CAMPOS}
    if request.method == "POST":
        valores = {c: request.form.get(c, "") for c in CAMPOS}
        try:
            servico.atualizar_pessoa(db, pessoa_id, **valores)
            flash("Pessoa atualizada com sucesso.", "sucesso")
            return redirect(url_for("pessoas.listar"))
        except ErroNegocio as erro:
            flash(str(erro), "erro")
    return _formulario("Editar pessoa", valores, editando=pessoa)


@pessoas_bp.route("/<int:pessoa_id>/alternar", methods=["POST"])
@exige_permissao("gerenciar_cadastros")
def alternar(pessoa_id):
    try:
        ativo = servico.alternar_ativo(get_db(), pessoa_id)
        flash("Pessoa ativada." if ativo else "Pessoa desativada.", "sucesso")
    except ErroNegocio as erro:
        flash(str(erro), "erro")
    return redirect(url_for("pessoas.listar"))
