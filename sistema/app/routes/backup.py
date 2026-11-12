from flask import Blueprint, current_app, flash, redirect, render_template, url_for

from app.auth import exige_permissao
from app.services import backup_service as servico
from app.services.erros import ErroNegocio

backup_bp = Blueprint("backup", __name__, url_prefix="/backup")


@backup_bp.route("/")
@exige_permissao("gerenciar_backup")
def listar():
    pasta = current_app.config["BACKUP_DIR"]
    return render_template("backup/lista.html", backups=servico.listar_backups(pasta),
                           situacao=servico.situacao(pasta), manter=current_app.config["BACKUP_MANTER"])


@backup_bp.route("/fazer", methods=["POST"])
@exige_permissao("gerenciar_backup")
def fazer():
    try:
        resultado = servico.fazer_backup(current_app.config["DATABASE"], current_app.config["BACKUP_DIR"],
                                         current_app.config["BACKUP_MANTER"])
        flash(f"Backup criado com sucesso: {resultado['nome']} ({resultado['tamanho_texto']}).", "sucesso")
    except ErroNegocio as erro:
        flash(str(erro), "erro")
    return redirect(url_for("backup.listar"))
