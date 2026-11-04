from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from app.auth import exige_permissao
from app.db import get_db
from app.services import usuario_service as servico
from app.services.erros import ErroNegocio

usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


def _pessoas(db):
    return db.execute("SELECT id, nome FROM pessoa WHERE ativo = 1 ORDER BY nome").fetchall()


def _formulario(db, titulo, valores, editando=None):
    return render_template("usuarios/form.html", titulo=titulo, valores=valores, editando=editando,
                           perfis=servico.listar_perfis(db), pessoas=_pessoas(db))


@usuarios_bp.route("/")
@exige_permissao("gerenciar_usuarios")
def listar():
    return render_template("usuarios/lista.html", usuarios=servico.listar_usuarios(get_db()))


@usuarios_bp.route("/novo", methods=["GET", "POST"])
@exige_permissao("gerenciar_usuarios")
def novo():
    db = get_db()
    valores = {"login": "", "perfil_id": "", "pessoa_id": ""}
    if request.method == "POST":
        valores = {c: request.form.get(c, "") for c in valores}
        try:
            servico.criar_usuario(db, valores["login"], request.form.get("senha", ""),
                                  valores["perfil_id"], valores["pessoa_id"])
            flash("Usuário cadastrado com sucesso.", "sucesso")
            return redirect(url_for("usuarios.listar"))
        except ErroNegocio as erro:
            flash(str(erro), "erro")
    return _formulario(db, "Novo usuário", valores)


@usuarios_bp.route("/<int:usuario_id>/editar", methods=["GET", "POST"])
@exige_permissao("gerenciar_usuarios")
def editar(usuario_id):
    db = get_db()
    usuario = servico.buscar_usuario(db, usuario_id)
    if usuario is None:
        abort(404)
    valores = {"login": usuario["login"], "perfil_id": str(usuario["perfil_id"]),
               "pessoa_id": str(usuario["pessoa_id"] or "")}
    if request.method == "POST":
        valores = {c: request.form.get(c, "") for c in valores}
        try:
            servico.atualizar_usuario(db, usuario_id, valores["login"], valores["perfil_id"],
                                      valores["pessoa_id"], request.form.get("senha", ""))
            flash("Usuário atualizado com sucesso.", "sucesso")
            return redirect(url_for("usuarios.listar"))
        except ErroNegocio as erro:
            flash(str(erro), "erro")
    return _formulario(db, "Editar usuário", valores, editando=usuario)


@usuarios_bp.route("/<int:usuario_id>/alternar", methods=["POST"])
@exige_permissao("gerenciar_usuarios")
def alternar(usuario_id):
    try:
        ativo = servico.alternar_ativo(get_db(), usuario_id, g.usuario["id"])
        flash("Usuário ativado." if ativo else "Usuário desativado.", "sucesso")
    except ErroNegocio as erro:
        flash(str(erro), "erro")
    return redirect(url_for("usuarios.listar"))
