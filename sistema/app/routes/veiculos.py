from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.auth import exige_permissao
from app.db import get_db
from app.services import veiculo_service as servico
from app.services.erros import ErroNegocio

veiculos_bp = Blueprint("veiculos", __name__, url_prefix="/veiculos")

CAMPOS = ("placa", "modelo", "cor", "pessoa_id")


def _formulario(db, titulo, valores, editando=None):
    atual = editando["pessoa_id"] if editando else None
    return render_template("veiculos/form.html", titulo=titulo, valores=valores, editando=editando,
                           proprietarios=servico.listar_proprietarios(db, atual))


@veiculos_bp.route("/")
@exige_permissao("gerenciar_cadastros")
def listar():
    busca = request.args.get("busca", "").strip()
    return render_template("veiculos/lista.html", busca=busca,
                           veiculos=servico.listar_veiculos(get_db(), busca))


@veiculos_bp.route("/novo", methods=["GET", "POST"])
@exige_permissao("gerenciar_cadastros")
def novo():
    db = get_db()
    valores = {c: "" for c in CAMPOS}
    if request.method == "POST":
        valores = {c: request.form.get(c, "") for c in CAMPOS}
        try:
            servico.criar_veiculo(db, **valores)
            flash("Veículo cadastrado com sucesso.", "sucesso")
            return redirect(url_for("veiculos.listar"))
        except ErroNegocio as erro:
            flash(str(erro), "erro")
    return _formulario(db, "Novo veículo", valores)


@veiculos_bp.route("/<int:veiculo_id>/editar", methods=["GET", "POST"])
@exige_permissao("gerenciar_cadastros")
def editar(veiculo_id):
    db = get_db()
    veiculo = servico.buscar_veiculo(db, veiculo_id)
    if veiculo is None:
        abort(404)
    valores = {"placa": servico.formatar_placa(veiculo["placa"]), "modelo": veiculo["modelo"],
               "cor": veiculo["cor"], "pessoa_id": str(veiculo["pessoa_id"])}
    if request.method == "POST":
        valores = {c: request.form.get(c, "") for c in CAMPOS}
        try:
            servico.atualizar_veiculo(db, veiculo_id, **valores)
            flash("Veículo atualizado com sucesso.", "sucesso")
            return redirect(url_for("veiculos.listar"))
        except ErroNegocio as erro:
            flash(str(erro), "erro")
    return _formulario(db, "Editar veículo", valores, editando=veiculo)


@veiculos_bp.route("/<int:veiculo_id>/alternar", methods=["POST"])
@exige_permissao("gerenciar_cadastros")
def alternar(veiculo_id):
    try:
        ativo = servico.alternar_ativo(get_db(), veiculo_id)
        flash("Veículo ativado." if ativo else "Veículo desativado.", "sucesso")
    except ErroNegocio as erro:
        flash(str(erro), "erro")
    return redirect(url_for("veiculos.listar"))
