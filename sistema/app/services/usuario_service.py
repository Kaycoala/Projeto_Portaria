"""Regras de negócio dos usuários e do login."""
import re

from werkzeug.security import check_password_hash, generate_password_hash

from app.services.erros import ErroNegocio

METODO_HASH = "pbkdf2:sha256"
SENHA_MINIMA = 6
PADRAO_LOGIN = re.compile(r"^[a-z0-9_.]{3,30}$")

SQL_USUARIOS = (
    "SELECT u.id, u.login, u.ativo, u.perfil_id, u.pessoa_id, "
    "       p.nome AS perfil, pe.nome AS pessoa_nome "
    "FROM usuario u JOIN perfil p ON p.id = u.perfil_id "
    "LEFT JOIN pessoa pe ON pe.id = u.pessoa_id "
)


def listar_perfis(db):
    return db.execute("SELECT id, nome FROM perfil ORDER BY id").fetchall()


def perfil_id_por_nome(db, nome):
    linha = db.execute("SELECT id FROM perfil WHERE nome = ?", (nome,)).fetchone()
    if linha is None:
        raise ErroNegocio(f"Perfil '{nome}' não existe.")
    return linha["id"]


def listar_usuarios(db):
    return db.execute(SQL_USUARIOS + "ORDER BY u.login").fetchall()


def buscar_usuario(db, usuario_id):
    return db.execute(SQL_USUARIOS + "WHERE u.id = ?", (usuario_id,)).fetchone()


def _contar_admins_ativos(db, excluindo_id=None):
    sql = ("SELECT COUNT(*) FROM usuario u JOIN perfil p ON p.id = u.perfil_id "
           "WHERE p.nome = 'administrador' AND u.ativo = 1")
    parametros = ()
    if excluindo_id is not None:
        sql += " AND u.id <> ?"
        parametros = (excluindo_id,)
    return db.execute(sql, parametros).fetchone()[0]


def _validar(db, login, perfil_id, pessoa_id, senha, senha_obrigatoria, usuario_id=None):
    """Confere os dados e devolve (login, perfil_id, pessoa_id) já limpos."""
    login = (login or "").strip().lower()
    if not PADRAO_LOGIN.match(login):
        raise ErroNegocio("O login deve ter de 3 a 30 caracteres: letras minúsculas, números, ponto ou _.")

    if senha_obrigatoria or senha:
        if len(senha or "") < SENHA_MINIMA:
            raise ErroNegocio(f"A senha deve ter pelo menos {SENHA_MINIMA} caracteres.")

    try:
        perfil_id = int(perfil_id)
    except (TypeError, ValueError):
        raise ErroNegocio("Escolha um perfil.")
    if db.execute("SELECT 1 FROM perfil WHERE id = ?", (perfil_id,)).fetchone() is None:
        raise ErroNegocio("Perfil inválido.")

    if pessoa_id in (None, ""):
        pessoa_id = None
    else:
        try:
            pessoa_id = int(pessoa_id)
        except ValueError:
            raise ErroNegocio("Pessoa inválida.")
        if db.execute("SELECT 1 FROM pessoa WHERE id = ?", (pessoa_id,)).fetchone() is None:
            raise ErroNegocio("Pessoa vinculada não encontrada.")

    existente = db.execute("SELECT id FROM usuario WHERE login = ?", (login,)).fetchone()
    if existente is not None and existente["id"] != usuario_id:
        raise ErroNegocio("Já existe um usuário com este login.")

    return login, perfil_id, pessoa_id


def criar_usuario(db, login, senha, perfil_id, pessoa_id=None):
    login, perfil_id, pessoa_id = _validar(db, login, perfil_id, pessoa_id, senha, True)
    cursor = db.execute(
        "INSERT INTO usuario (login, senha_hash, perfil_id, pessoa_id) VALUES (?, ?, ?, ?)",
        (login, generate_password_hash(senha, method=METODO_HASH), perfil_id, pessoa_id))
    db.commit()
    return cursor.lastrowid


def atualizar_usuario(db, usuario_id, login, perfil_id, pessoa_id, senha=None):
    atual = buscar_usuario(db, usuario_id)
    if atual is None:
        raise ErroNegocio("Usuário não encontrado.")
    login, perfil_id, pessoa_id = _validar(
        db, login, perfil_id, pessoa_id, senha, False, usuario_id)

    novo_perfil = db.execute("SELECT nome FROM perfil WHERE id = ?", (perfil_id,)).fetchone()["nome"]
    if (atual["perfil"] == "administrador" and atual["ativo"] and novo_perfil != "administrador"
            and _contar_admins_ativos(db, excluindo_id=usuario_id) == 0):
        raise ErroNegocio("Este é o único administrador ativo: o perfil dele não pode ser alterado.")

    db.execute("UPDATE usuario SET login = ?, perfil_id = ?, pessoa_id = ? WHERE id = ?",
               (login, perfil_id, pessoa_id, usuario_id))
    if senha:
        db.execute("UPDATE usuario SET senha_hash = ? WHERE id = ?",
                   (generate_password_hash(senha, method=METODO_HASH), usuario_id))
    db.commit()


def alternar_ativo(db, usuario_id, usuario_logado_id):
    """Ativa ou desativa um usuário. Devolve True se ficou ativo."""
    atual = buscar_usuario(db, usuario_id)
    if atual is None:
        raise ErroNegocio("Usuário não encontrado.")
    if atual["ativo"]:
        if usuario_id == usuario_logado_id:
            raise ErroNegocio("Você não pode desativar o seu próprio usuário.")
        if atual["perfil"] == "administrador" and _contar_admins_ativos(db, excluindo_id=usuario_id) == 0:
            raise ErroNegocio("Este é o único administrador ativo e não pode ser desativado.")
    novo = 0 if atual["ativo"] else 1
    db.execute("UPDATE usuario SET ativo = ? WHERE id = ?", (novo, usuario_id))
    db.commit()
    return bool(novo)


def autenticar(db, login, senha):
    """Devolve o id do usuário se login e senha estiverem corretos e ele estiver ativo."""
    login = (login or "").strip().lower()
    linha = db.execute(
        "SELECT id, senha_hash, ativo FROM usuario WHERE login = ?", (login,)).fetchone()
    if linha and linha["ativo"] and check_password_hash(linha["senha_hash"], senha or ""):
        return linha["id"]
    return None
