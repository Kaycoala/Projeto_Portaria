"""Regras de negócio das ocorrências (RF-09, RN-05, RN-10)."""
from datetime import datetime, timedelta

from app.services.erros import ErroNegocio
from app.services.historico_service import _escapar_like, intervalo_de_datas  # noqa: F401

DESCRICAO_MINIMA = 5
DESCRICAO_MAXIMA = 2000

SQL_OCORRENCIAS = (
    "SELECT o.id, o.data_hora, o.descricao, o.ativo, u.login AS registrador, "
    "  (SELECT group_concat(nome, ', ') FROM ("
    "     SELECT p.nome FROM ocorrencia_pessoa op JOIN pessoa p ON p.id = op.pessoa_id "
    "     WHERE op.ocorrencia_id = o.id ORDER BY p.nome COLLATE NOCASE)) AS envolvidos "
    "FROM ocorrencia o JOIN usuario u ON u.id = o.registrado_por_id "
)


def agora_para_formulario():
    """Data e hora atuais no formato do campo datetime-local (AAAA-MM-DDTHH:MM)."""
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


def para_formulario(data_hora):
    """'2026-11-04 20:30:00' -> '2026-11-04T20:30'."""
    return (data_hora or "")[:16].replace(" ", "T")


def listar_ocorrencias(db, data_de="", data_ate="", incluir_excluidas=False):
    condicoes, parametros = [], []
    inicio, fim = intervalo_de_datas(data_de, data_ate)
    if inicio:
        condicoes.append("o.data_hora >= ?")
        parametros.append(inicio)
    if fim:
        condicoes.append("o.data_hora < ?")
        parametros.append(fim)
    if not incluir_excluidas:
        condicoes.append("o.ativo = 1")
    sql = SQL_OCORRENCIAS
    if condicoes:
        sql += "WHERE " + " AND ".join(condicoes) + " "
    sql += "ORDER BY o.data_hora DESC, o.id DESC"
    return db.execute(sql, parametros).fetchall()


def buscar_ocorrencia(db, ocorrencia_id):
    return db.execute(SQL_OCORRENCIAS + "WHERE o.id = ?", (ocorrencia_id,)).fetchone()


def ids_envolvidos(db, ocorrencia_id):
    linhas = db.execute("SELECT pessoa_id FROM ocorrencia_pessoa WHERE ocorrencia_id = ?",
                        (ocorrencia_id,)).fetchall()
    return [linha["pessoa_id"] for linha in linhas]


def listar_pessoas_para_escolha(db, incluir_ids=()):
    """Pessoas ativas (mais as que já estavam ligadas à ocorrência, mesmo se inativas)."""
    incluir_ids = list(incluir_ids)
    marcas = ",".join("?" * len(incluir_ids))
    sql = "SELECT id, nome, tipo, ativo FROM pessoa WHERE ativo = 1"
    if incluir_ids:
        sql += f" OR id IN ({marcas})"
    sql += " ORDER BY nome COLLATE NOCASE"
    return db.execute(sql, incluir_ids).fetchall()


def _validar(db, data_hora, descricao, pessoa_ids, ja_ligadas=()):
    descricao = (descricao or "").strip()
    if len(descricao) < DESCRICAO_MINIMA:
        raise ErroNegocio(f"Descreva a ocorrência (mínimo de {DESCRICAO_MINIMA} letras).")  # RN-10
    if len(descricao) > DESCRICAO_MAXIMA:
        raise ErroNegocio(f"A descrição pode ter no máximo {DESCRICAO_MAXIMA} caracteres.")

    data_hora = (data_hora or "").strip()
    if not data_hora:
        momento = datetime.now()
    else:
        try:
            momento = datetime.fromisoformat(data_hora)
        except ValueError:
            raise ErroNegocio("A data e o horário da ocorrência são inválidos.")
        if momento > datetime.now() + timedelta(minutes=1):
            raise ErroNegocio("A data e o horário da ocorrência não podem estar no futuro.")

    ids = []
    for valor in pessoa_ids or []:
        try:
            numero = int(valor)
        except (TypeError, ValueError):
            raise ErroNegocio("Pessoa envolvida inválida.")
        if numero not in ids:
            ids.append(numero)
    for numero in ids:
        pessoa = db.execute("SELECT ativo FROM pessoa WHERE id = ?", (numero,)).fetchone()
        if pessoa is None:
            raise ErroNegocio("Uma das pessoas envolvidas não foi encontrada.")
        if not pessoa["ativo"] and numero not in ja_ligadas:
            raise ErroNegocio("Uma das pessoas envolvidas está com o cadastro inativo.")

    return momento.strftime("%Y-%m-%d %H:%M:%S"), descricao, ids


def criar_ocorrencia(db, data_hora, descricao, pessoa_ids, usuario_id):
    data_hora, descricao, ids = _validar(db, data_hora, descricao, pessoa_ids)
    try:
        cursor = db.execute(
            "INSERT INTO ocorrencia (data_hora, descricao, registrado_por_id) VALUES (?, ?, ?)",
            (data_hora, descricao, usuario_id))
        for pessoa_id in ids:
            db.execute("INSERT INTO ocorrencia_pessoa (ocorrencia_id, pessoa_id) VALUES (?, ?)",
                       (cursor.lastrowid, pessoa_id))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return cursor.lastrowid


def atualizar_ocorrencia(db, ocorrencia_id, data_hora, descricao, pessoa_ids):
    ocorrencia = db.execute("SELECT ativo FROM ocorrencia WHERE id = ?", (ocorrencia_id,)).fetchone()
    if ocorrencia is None or not ocorrencia["ativo"]:
        raise ErroNegocio("Ocorrência não encontrada ou já excluída.")
    data_hora, descricao, ids = _validar(db, data_hora, descricao, pessoa_ids,
                                         ja_ligadas=ids_envolvidos(db, ocorrencia_id))
    try:
        db.execute("UPDATE ocorrencia SET data_hora = ?, descricao = ? WHERE id = ?",
                   (data_hora, descricao, ocorrencia_id))
        db.execute("DELETE FROM ocorrencia_pessoa WHERE ocorrencia_id = ?", (ocorrencia_id,))
        for pessoa_id in ids:
            db.execute("INSERT INTO ocorrencia_pessoa (ocorrencia_id, pessoa_id) VALUES (?, ?)",
                       (ocorrencia_id, pessoa_id))
        db.commit()
    except Exception:
        db.rollback()
        raise


def excluir_ocorrencia(db, ocorrencia_id):
    """Exclusão lógica: a ocorrência continua no banco para consulta administrativa."""
    cursor = db.execute("UPDATE ocorrencia SET ativo = 0 WHERE id = ? AND ativo = 1", (ocorrencia_id,))
    if cursor.rowcount == 0:
        db.rollback()
        raise ErroNegocio("Ocorrência não encontrada ou já excluída.")
    db.commit()
