from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.auth import exige_permissao, pode
from app.db import get_db
from app.services import historico_service as servico
from app.services.erros import ErroNegocio

historico_bp = Blueprint("historico", __name__, url_prefix="/historico")

FILTROS = ("nome", "cpf", "placa", "data_de", "data_ate", "tipo")


@historico_bp.route("/")
@exige_permissao("consultar_historico")
def listar():
    filtros = {c: request.args.get(c, "").strip() for c in FILTROS}
    registros, tem_mais = [], False
    try:
        registros, tem_mais = servico.listar_historico(
            get_db(), **filtros, incluir_excluidos=pode("administrar_registros"))
    except ErroNegocio as erro:
        flash(str(erro), "erro")
    return render_template("historico/lista.html", filtros=filtros, registros=registros,
                           tem_mais=tem_mais, limite=servico.LIMITE, tipos=servico.TIPOS,
                           filtrado=any(filtros.values()))


# Alterar ou excluir registros de acesso é restrito ao administrador (RN-05, RN-08).
@historico_bp.route("/<int:registro_id>/editar", methods=["GET", "POST"])
@exige_permissao("administrar_registros")
def editar(registro_id):
    db = get_db()
    registro = servico.buscar_registro(db, registro_id)
    if registro is None or not registro["ativo"]:
        abort(404)
    observacao = registro["observacao"] or ""
    if request.method == "POST":
        observacao = request.form.get("observacao", "")
        try:
            servico.atualizar_observacao(db, registro_id, observacao)
            flash("Observação atualizada com sucesso.", "sucesso")
            return redirect(url_for("historico.listar"))
        except ErroNegocio as erro:
            flash(str(erro), "erro")
    return render_template("historico/editar.html", registro=registro, observacao=observacao,
                           descricao=servico.descrever(registro))


@historico_bp.route("/<int:registro_id>/excluir", methods=["POST"])
@exige_permissao("administrar_registros")
def excluir(registro_id):
    try:
        servico.excluir_registro(get_db(), registro_id)
        flash("Registro de acesso excluído. Ele continua guardado para consulta administrativa.", "sucesso")
    except ErroNegocio as erro:
        flash(str(erro), "erro")
    return redirect(url_for("historico.listar"))
