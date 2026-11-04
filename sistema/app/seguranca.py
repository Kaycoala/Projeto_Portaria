"""Proteção contra formulários falsos (CSRF)."""
import secrets

from flask import abort, request, session


def token_csrf():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


def verificar_csrf():
    """Todo formulário POST precisa enviar o token da sessão."""
    if request.method != "POST":
        return
    enviado = request.form.get("csrf_token", "").encode()
    esperado = session.get("csrf", "").encode()
    if not esperado or not secrets.compare_digest(enviado, esperado):
        abort(400, "Sessão expirada ou formulário inválido. Volte e tente novamente.")
