"""Regras de negócio de entrada e saída (RF-03, RF-04, RF-07, RN-02, RN-03, RN-04, RN-08).

Os registros de acesso nunca são apagados: a saída só preenche o horário de saída.
"""
from datetime import date

from app.services.autorizacao_service import formatar_data
from app.services.erros import ErroNegocio

# Em aberto = entrou e ainda não saiu.
EM_ABERTO = "saida_em IS NULL AND ativo = 1"

SQL_DENTRO = (
    "SELECT r.id, r.tipo, r.entrada_em, r.observacao, "
    "       pe.nome AS pessoa_nome, pe.tipo AS pessoa_tipo, "
    "       vi.nome AS visitante_nome, vp.nome AS visitado_nome, "
    "       ve.placa, ve.modelo, ve.cor, vo.nome AS proprietario_nome, "
    "       u.login AS porteiro_login "
    "FROM registro_acesso r "
    "JOIN usuario u ON u.id = r.porteiro_id "
    "LEFT JOIN pessoa pe ON r.tipo = 'pessoa' AND pe.id = r.pessoa_id "
    "LEFT JOIN visitante vi ON vi.id = r.visitante_id "
    "LEFT JOIN pessoa vp ON vp.id = vi.pessoa_visitada_id "
    "LEFT JOIN veiculo ve ON ve.id = r.veiculo_id "
    "LEFT JOIN pessoa vo ON vo.id = ve.pessoa_id "
)


# ---------- consultas para a tela da portaria ----------

def listar_dentro(db):
    """Quem está dentro agora (entrada registrada e saída ainda não), os mais antigos primeiro."""
    return db.execute(
        SQL_DENTRO + "WHERE r.saida_em IS NULL AND r.ativo = 1 ORDER BY r.entrada_em, r.id"
    ).fetchall()


def listar_pessoas_para_entrada(db):
    return db.execute(
        "SELECT id, nome, tipo FROM pessoa WHERE ativo = 1 AND id NOT IN "
        f"(SELECT pessoa_id FROM registro_acesso WHERE tipo = 'pessoa' AND {EM_ABERTO}) "
        "ORDER BY nome COLLATE NOCASE").fetchall()


def listar_visitantes_para_entrada(db):
    """Visitantes que não estão dentro, com a situação da última autorização (mais recentes primeiro)."""
    return db.execute(
        "SELECT v.id, v.nome, a.status, a.data_inicio, a.data_fim "
        "FROM visitante v "
        "LEFT JOIN autorizacao a ON a.id = (SELECT MAX(id) FROM autorizacao WHERE visitante_id = v.id) "
        "WHERE v.id NOT IN "
        f"(SELECT visitante_id FROM registro_acesso WHERE tipo = 'visitante' AND {EM_ABERTO}) "
        "ORDER BY v.id DESC").fetchall()


def listar_veiculos_para_entrada(db):
    return db.execute(
        "SELECT v.id, v.placa, v.modelo, p.nome AS proprietario "
        "FROM veiculo v JOIN pessoa p ON p.id = v.pessoa_id "
        "WHERE v.ativo = 1 AND p.ativo = 1 AND v.id NOT IN "
        f"(SELECT veiculo_id FROM registro_acesso WHERE tipo = 'veiculo' AND {EM_ABERTO}) "
        "ORDER BY v.placa").fetchall()


def buscar_registro(db, registro_id):
    return db.execute(SQL_DENTRO + "WHERE r.id = ?", (registro_id,)).fetchone()


def descrever(registro):
    """Texto curto para as mensagens (ex.: 'Maria da Silva', 'Carlos (visitante)', 'ABC-1234')."""
    if registro["tipo"] == "pessoa":
        return registro["pessoa_nome"]
    if registro["tipo"] == "visitante":
        return f"{registro['visitante_nome']} (visitante)"
    placa = registro["placa"]
    return f"{placa[:3]}-{placa[3:]} ({registro['modelo']})" if len(placa) == 7 else placa


# ---------- entradas ----------

def _inteiro(valor, mensagem):
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ErroNegocio(mensagem)


def _registrar_entrada(db, tipo, coluna, alvo_id, pessoa_id, porteiro_id, observacao, ja_dentro):
    """Grava a entrada com a data e hora atuais (RN-02).

    A conferência de "já está dentro" e a gravação acontecem no mesmo comando,
    para que a mesma pessoa/visitante/veículo nunca fique dentro duas vezes.
    `tipo` e `coluna` vêm do código (nunca do usuário).
    """
    cursor = db.execute(
        "INSERT INTO registro_acesso (tipo, pessoa_id, " + coluna + ", entrada_em, porteiro_id, observacao) "
        "SELECT ?, ?, ?, datetime('now', 'localtime'), ?, ? "
        "WHERE NOT EXISTS (SELECT 1 FROM registro_acesso WHERE tipo = ? AND " + coluna + " = ? "
        "AND saida_em IS NULL AND ativo = 1)",
        (tipo, pessoa_id, alvo_id, porteiro_id, (observacao or "").strip() or None, tipo, alvo_id))
    if cursor.rowcount == 0:
        db.rollback()
        raise ErroNegocio(ja_dentro)
    db.commit()
    return cursor.lastrowid


def registrar_entrada_pessoa(db, pessoa_id, porteiro_id, observacao=""):
    pessoa_id = _inteiro(pessoa_id, "Escolha a pessoa que está entrando.")
    pessoa = db.execute("SELECT ativo FROM pessoa WHERE id = ?", (pessoa_id,)).fetchone()
    if pessoa is None:
        raise ErroNegocio("Pessoa não encontrada. Cadastre-a antes de liberar a entrada.")  # RN-01
    if not pessoa["ativo"]:
        raise ErroNegocio("O cadastro desta pessoa está inativo. Regularize o cadastro antes da entrada.")
    return _registrar_entrada(db, "pessoa", "pessoa_id", pessoa_id, pessoa_id, porteiro_id,
                              observacao, "Esta pessoa já está dentro. Registre a saída antes de uma nova entrada.")


def conferir_autorizacao_do_visitante(db, visitante_id, hoje=None):
    """Levanta ErroNegocio se o visitante não tiver autorização válida para hoje (RN-03, RN-09)."""
    hoje = hoje or date.today()
    ultima = db.execute(
        "SELECT status, data_inicio, data_fim FROM autorizacao WHERE visitante_id = ? "
        "ORDER BY id DESC LIMIT 1", (visitante_id,)).fetchone()
    if ultima is None:
        raise ErroNegocio("Este visitante não tem solicitação de autorização.")
    if ultima["status"] == "pendente":
        raise ErroNegocio("Entrada bloqueada: o visitante está aguardando autorização do responsável.")
    if ultima["status"] == "negada":
        raise ErroNegocio("Entrada bloqueada: a entrada deste visitante foi negada pelo responsável.")
    inicio = date.fromisoformat(ultima["data_inicio"])
    fim = date.fromisoformat(ultima["data_fim"])
    if hoje < inicio:
        raise ErroNegocio("Entrada bloqueada: a autorização só vale a partir de "
                          f"{formatar_data(ultima['data_inicio'])}.")
    if hoje > fim:
        raise ErroNegocio(f"Entrada bloqueada: a autorização venceu em {formatar_data(ultima['data_fim'])}. "
                          "Peça uma nova solicitação.")


def registrar_entrada_visitante(db, visitante_id, porteiro_id, observacao=""):
    visitante_id = _inteiro(visitante_id, "Escolha o visitante que está entrando.")
    if db.execute("SELECT 1 FROM visitante WHERE id = ?", (visitante_id,)).fetchone() is None:
        raise ErroNegocio("Visitante não encontrado.")
    conferir_autorizacao_do_visitante(db, visitante_id)
    return _registrar_entrada(db, "visitante", "visitante_id", visitante_id, None, porteiro_id,
                              observacao, "Este visitante já está dentro. Registre a saída antes de uma nova entrada.")


def registrar_entrada_veiculo(db, veiculo_id, porteiro_id, observacao=""):
    veiculo_id = _inteiro(veiculo_id, "Escolha o veículo que está entrando.")
    veiculo = db.execute(
        "SELECT v.ativo, v.pessoa_id, p.ativo AS proprietario_ativo FROM veiculo v "
        "JOIN pessoa p ON p.id = v.pessoa_id WHERE v.id = ?", (veiculo_id,)).fetchone()
    if veiculo is None:
        raise ErroNegocio("Veículo não encontrado. Cadastre-o antes de liberar a entrada.")
    if not veiculo["ativo"]:
        raise ErroNegocio("O cadastro deste veículo está inativo.")
    if not veiculo["proprietario_ativo"]:
        raise ErroNegocio("O proprietário deste veículo está com o cadastro inativo.")
    return _registrar_entrada(db, "veiculo", "veiculo_id", veiculo_id, veiculo["pessoa_id"], porteiro_id,
                              observacao, "Este veículo já está dentro. Registre a saída antes de uma nova entrada.")


# ---------- saída ----------

def registrar_saida(db, registro_id):
    """Preenche o horário de saída (RN-04). Só vale para quem tem entrada sem saída (RF-04)."""
    registro = buscar_registro(db, registro_id)
    if registro is None:
        raise ErroNegocio("Registro de entrada não encontrado.")
    cursor = db.execute(
        "UPDATE registro_acesso SET saida_em = datetime('now', 'localtime') "
        "WHERE id = ? AND saida_em IS NULL AND ativo = 1", (registro_id,))
    if cursor.rowcount == 0:
        db.rollback()
        raise ErroNegocio("A saída deste registro já foi registrada.")
    db.commit()
    return registro
