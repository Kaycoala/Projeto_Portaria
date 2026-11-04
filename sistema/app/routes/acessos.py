from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app.auth import exige_permissao
from app.db import get_db
from app.services import acesso_service as servico
from app.services.erros import ErroNegocio

acessos_bp = Blueprint("acessos", __name__, url_prefix="/acessos")


@acessos_bp.route("/")
@exige_permissao("registrar_acesso")
def portaria():
    db = get_db()
    return render_template("acessos/portaria.html",
                           dentro=servico.listar_dentro(db),
                           pessoas=servico.listar_pessoas_para_entrada(db),
                           visitantes=servico.listar_visitantes_para_entrada(db),
                           veiculos=servico.listar_veiculos_para_entrada(db))


def _entrada(funcao, campo, mensagem):
    """Executa uma entrada e volta para a tela da portaria com a mensagem."""
    try:
        registro_id = funcao(get_db(), request.form.get(campo), g.usuario["id"],
                             request.form.get("observacao", ""))
        quem = servico.descrever(servico.buscar_registro(get_db(), registro_id))
        flash(f"{mensagem}: {quem}.", "sucesso")
    except ErroNegocio as erro:
        flash(str(erro), "erro")
    return redirect(url_for("acessos.portaria"))


@acessos_bp.route("/entrada/pessoa", methods=["POST"])
@exige_permissao("registrar_acesso")
def entrada_pessoa():
    return _entrada(servico.registrar_entrada_pessoa, "pessoa_id", "Entrada registrada")


@acessos_bp.route("/entrada/visitante", methods=["POST"])
@exige_permissao("registrar_acesso")
def entrada_visitante():
    return _entrada(servico.registrar_entrada_visitante, "visitante_id", "Entrada registrada")


@acessos_bp.route("/entrada/veiculo", methods=["POST"])
@exige_permissao("registrar_acesso")
def entrada_veiculo():
    return _entrada(servico.registrar_entrada_veiculo, "veiculo_id", "Entrada registrada")


@acessos_bp.route("/<int:registro_id>/saida", methods=["POST"])
@exige_permissao("registrar_acesso")
def saida(registro_id):
    try:
        registro = servico.registrar_saida(get_db(), registro_id)
        flash(f"Saída registrada: {servico.descrever(registro)}.", "sucesso")
    except ErroNegocio as erro:
        flash(str(erro), "erro")
    return redirect(url_for("acessos.portaria"))
