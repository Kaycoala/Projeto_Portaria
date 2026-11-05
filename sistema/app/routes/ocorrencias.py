from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from app.auth import exige_permissao, pode
from app.db import get_db
from app.services import ocorrencia_service as servico
from app.services.erros import ErroNegocio

ocorrencias_bp = Blueprint("ocorrencias", __name__, url_prefix="/ocorrencias")


def _formulario(titulo, valores, editando=None):
    db = get_db()
    marcadas = [int(i) for i in valores["pessoas"] if str(i).isdigit()]
    return render_template("ocorrencias/form.html", titulo=titulo, valores=valores, editando=editando,
                           pessoas=servico.listar_pessoas_para_escolha(db, marcadas),
                           marcadas=marcadas, agora=servico.agora_para_formulario())


def _valores_do_formulario():
    return {"data_hora": request.form.get("data_hora", ""),
            "descricao": request.form.get("descricao", ""),
            "pessoas": request.form.getlist("pessoas")}


@ocorrencias_bp.route("/")
@exige_permissao("registrar_ocorrencia")
def listar():
    filtros = {"data_de": request.args.get("data_de", "").strip(),
               "data_ate": request.args.get("data_ate", "").strip()}
    ocorrencias = []
    try:
        ocorrencias = servico.listar_ocorrencias(
            get_db(), **filtros, incluir_excluidas=pode("administrar_registros"))
    except ErroNegocio as erro:
        flash(str(erro), "erro")
    return render_template("ocorrencias/lista.html", ocorrencias=ocorrencias, filtros=filtros)


@ocorrencias_bp.route("/nova", methods=["GET", "POST"])
@exige_permissao("registrar_ocorrencia")
def nova():
    valores = {"data_hora": servico.agora_para_formulario(), "descricao": "", "pessoas": []}
    if request.method == "POST":
        valores = _valores_do_formulario()
        try:
            servico.criar_ocorrencia(get_db(), valores["data_hora"], valores["descricao"],
                                     valores["pessoas"], g.usuario["id"])
            flash("Ocorrência registrada com sucesso.", "sucesso")
            return redirect(url_for("ocorrencias.listar"))
        except ErroNegocio as erro:
            flash(str(erro), "erro")
    return _formulario("Nova ocorrência", valores)


# Alterar ou excluir ocorrências é restrito ao administrador (RN-05).
@ocorrencias_bp.route("/<int:ocorrencia_id>/editar", methods=["GET", "POST"])
@exige_permissao("administrar_registros")
def editar(ocorrencia_id):
    db = get_db()
    ocorrencia = servico.buscar_ocorrencia(db, ocorrencia_id)
    if ocorrencia is None or not ocorrencia["ativo"]:
        abort(404)
    valores = {"data_hora": servico.para_formulario(ocorrencia["data_hora"]),
               "descricao": ocorrencia["descricao"],
               "pessoas": [str(i) for i in servico.ids_envolvidos(db, ocorrencia_id)]}
    if request.method == "POST":
        valores = _valores_do_formulario()
        try:
            servico.atualizar_ocorrencia(db, ocorrencia_id, valores["data_hora"],
                                         valores["descricao"], valores["pessoas"])
            flash("Ocorrência atualizada com sucesso.", "sucesso")
            return redirect(url_for("ocorrencias.listar"))
        except ErroNegocio as erro:
            flash(str(erro), "erro")
    return _formulario("Editar ocorrência", valores, editando=ocorrencia)


@ocorrencias_bp.route("/<int:ocorrencia_id>/excluir", methods=["POST"])
@exige_permissao("administrar_registros")
def excluir(ocorrencia_id):
    try:
        servico.excluir_ocorrencia(get_db(), ocorrencia_id)
        flash("Ocorrência excluída. Ela continua guardada para consulta administrativa.", "sucesso")
    except ErroNegocio as erro:
        flash(str(erro), "erro")
    return redirect(url_for("ocorrencias.listar"))
