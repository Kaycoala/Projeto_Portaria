"""Login, usuário atual e proteção das páginas."""
from functools import wraps

from flask import abort, g, redirect, request, session, url_for

from app.db import get_db
from app.permissoes import tem_permissao

ROTAS_PUBLICAS = {"auth.login", "static"}


def carregar_usuario():
    """Descobre quem está logado (ou ninguém) a cada requisição."""
    g.usuario = None
    usuario_id = session.get("usuario_id")
    if usuario_id is None:
        return
    linha = get_db().execute(
        "SELECT u.id, u.login, u.pessoa_id, p.nome AS perfil "
        "FROM usuario u JOIN perfil p ON p.id = u.perfil_id "
        "WHERE u.id = ? AND u.ativo = 1", (usuario_id,)).fetchone()
    if linha is None:           # usuário desativado ou removido: encerra a sessão
        session.clear()
    g.usuario = linha


def exigir_login():
    """Executa antes de toda página: sem login, só /login é permitido (RNF-02)."""
    carregar_usuario()
    if request.endpoint is None or request.endpoint in ROTAS_PUBLICAS:
        return None
    if g.usuario is None:
        return redirect(url_for("auth.login"))
    return None


def pode(permissao):
    return g.get("usuario") is not None and tem_permissao(g.usuario["perfil"], permissao)


def exige_permissao(permissao):
    """Decorador: bloqueia a página (erro 403) se o perfil não tiver a permissão (RNF-04)."""
    def decorador(funcao):
        @wraps(funcao)
        def interna(*args, **kwargs):
            if not pode(permissao):
                abort(403)
            return funcao(*args, **kwargs)
        return interna
    return decorador
