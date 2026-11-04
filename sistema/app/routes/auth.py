from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from app.db import get_db
from app.services.usuario_service import autenticar

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.usuario is not None:
        return redirect(url_for("main.inicio"))
    login_digitado = ""
    if request.method == "POST":
        login_digitado = request.form.get("login", "")
        usuario_id = autenticar(get_db(), login_digitado, request.form.get("senha", ""))
        if usuario_id is not None:
            session.clear()
            session["usuario_id"] = usuario_id
            return redirect(url_for("main.inicio"))
        flash("Login ou senha inválidos.", "erro")
    return render_template("auth/login.html", login=login_digitado)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Você saiu do sistema.", "sucesso")
    return redirect(url_for("auth.login"))
