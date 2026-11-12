from flask import Blueprint, Response, flash, redirect, render_template, request, url_for

from app.auth import exige_permissao
from app.db import get_db
from app.services import relatorio_service as servico
from app.services.erros import ErroNegocio

relatorios_bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")


def _periodo():
    padrao_de, padrao_ate = servico.periodo_padrao()
    return (request.args.get("data_de", padrao_de).strip(),
            request.args.get("data_ate", padrao_ate).strip())


# Relatórios são exclusivos do administrador (RF-10).
@relatorios_bp.route("/")
@exige_permissao("ver_relatorios")
def gerar():
    data_de, data_ate = _periodo()
    relatorio = None
    try:
        relatorio = servico.gerar_relatorio(get_db(), data_de, data_ate)
    except ErroNegocio as erro:
        flash(str(erro), "erro")
    return render_template("relatorios/relatorio.html", relatorio=relatorio,
                           filtros={"data_de": data_de, "data_ate": data_ate},
                           atalhos={"7": servico.ultimos_dias(7), "30": servico.ultimos_dias(30)})


@relatorios_bp.route("/csv")
@exige_permissao("ver_relatorios")
def baixar_csv():
    data_de, data_ate = _periodo()
    try:
        relatorio = servico.gerar_relatorio(get_db(), data_de, data_ate)
    except ErroNegocio as erro:
        flash(str(erro), "erro")
        return redirect(url_for("relatorios.gerar", data_de=data_de, data_ate=data_ate))
    conteudo = "\ufeff" + servico.gerar_csv(relatorio)      # BOM: acentos corretos no Excel
    return Response(conteudo, mimetype="text/csv", headers={
        "Content-Disposition": f'attachment; filename="{servico.nome_arquivo_csv(relatorio)}"'})
