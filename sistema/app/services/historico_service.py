"""Histórico de acessos (RF-08, UC03) e correções feitas pelo administrador (RN-05, RN-08).

A consulta só lê os dados. Registros "excluídos" continuam no banco (exclusão lógica)
e só o administrador consegue vê-los.
"""
from datetime import date, timedelta

from app.services.erros import ErroNegocio
from app.services.pessoa_service import somente_digitos
from app.services.veiculo_service import normalizar_placa

LIMITE = 200   # máximo de linhas na tela (mantém a consulta rápida, RNF-01)

TIPOS = {"pessoa": "Pessoa", "visitante": "Visitante", "veiculo": "Veículo"}

SQL_HISTORICO = (
    "SELECT r.id, r.tipo, r.entrada_em, r.saida_em, r.observacao, r.ativo, "
    "       pe.nome AS pessoa_nome, pe.tipo AS pessoa_tipo, pe.cpf AS pessoa_cpf, "
    "       vi.nome AS visitante_nome, vi.cpf AS visitante_cpf, vp.nome AS visitado_nome, "
    "       ve.placa, ve.modelo, ve.cor, vo.nome AS proprietario_nome, vo.cpf AS proprietario_cpf, "
    "       u.login AS porteiro_login "
    "FROM registro_acesso r "
    "JOIN usuario u ON u.id = r.porteiro_id "
    "LEFT JOIN pessoa pe ON r.tipo = 'pessoa' AND pe.id = r.pessoa_id "
    "LEFT JOIN visitante vi ON vi.id = r.visitante_id "
    "LEFT JOIN pessoa vp ON vp.id = vi.pessoa_visitada_id "
    "LEFT JOIN veiculo ve ON ve.id = r.veiculo_id "
    "LEFT JOIN pessoa vo ON vo.id = ve.pessoa_id "
)


def nome_tipo_acesso(tipo):
    return TIPOS.get(tipo, tipo)


def _escapar_like(texto):
    """Para que % e _ digitados na busca sejam tratados como letras comuns."""
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _ler_data(texto, nome_campo):
    try:
        return date.fromisoformat(texto)
    except ValueError:
        raise ErroNegocio(f"A data {nome_campo} é inválida.")


def intervalo_de_datas(data_de, data_ate):
    """Devolve (início, fim_exclusivo) em texto, ou None para o que não foi informado.

    Também usado pelas ocorrências. Levanta ErroNegocio se a data for inválida.
    """
    data_de = (data_de or "").strip()
    data_ate = (data_ate or "").strip()
    inicio = _ler_data(data_de, "inicial") if data_de else None
    fim = _ler_data(data_ate, "final") if data_ate else None
    if inicio and fim and inicio > fim:
        raise ErroNegocio("A data inicial não pode ser depois da data final.")
    return (f"{inicio.isoformat()} 00:00:00" if inicio else None,
            f"{(fim + timedelta(days=1)).isoformat()} 00:00:00" if fim else None)


def listar_historico(db, nome="", cpf="", placa="", data_de="", data_ate="", tipo="",
                     incluir_excluidos=False):
    """Pesquisa o histórico. Devolve (linhas, tem_mais).

    `tem_mais` é True quando existem mais registros do que o limite mostrado.
    """
    condicoes, parametros = [], []

    nome = " ".join((nome or "").split())
    if nome:
        condicoes.append("(pe.nome LIKE ? ESCAPE '\\' OR vi.nome LIKE ? ESCAPE '\\' "
                         "OR vo.nome LIKE ? ESCAPE '\\')")
        parametros += [f"%{_escapar_like(nome)}%"] * 3

    cpf = (cpf or "").strip()
    if cpf:
        digitos = somente_digitos(cpf)
        if not digitos:
            raise ErroNegocio("Para filtrar por CPF, digite números.")
        condicoes.append("(pe.cpf LIKE ? OR vi.cpf LIKE ? OR vo.cpf LIKE ?)")
        parametros += [f"%{digitos}%"] * 3

    placa = normalizar_placa(placa)
    if placa:
        condicoes.append("ve.placa LIKE ? ESCAPE '\\'")
        parametros.append(f"%{_escapar_like(placa)}%")

    inicio, fim = intervalo_de_datas(data_de, data_ate)
    if inicio:
        condicoes.append("r.entrada_em >= ?")
        parametros.append(inicio)
    if fim:
        condicoes.append("r.entrada_em < ?")
        parametros.append(fim)

    tipo = (tipo or "").strip()
    if tipo:
        if tipo not in TIPOS:
            raise ErroNegocio("Tipo de acesso inválido.")
        condicoes.append("r.tipo = ?")
        parametros.append(tipo)

    if not incluir_excluidos:
        condicoes.append("r.ativo = 1")

    sql = SQL_HISTORICO
    if condicoes:
        sql += "WHERE " + " AND ".join(condicoes) + " "
    sql += "ORDER BY r.entrada_em DESC, r.id DESC LIMIT ?"
    linhas = db.execute(sql, parametros + [LIMITE + 1]).fetchall()
    return linhas[:LIMITE], len(linhas) > LIMITE


# ---------- correções (somente administrador, RN-05) ----------

def buscar_registro(db, registro_id):
    return db.execute(SQL_HISTORICO + "WHERE r.id = ?", (registro_id,)).fetchone()


def descrever(registro):
    """Texto curto para mensagens e cabeçalhos."""
    if registro["tipo"] == "pessoa":
        return registro["pessoa_nome"]
    if registro["tipo"] == "visitante":
        return f"{registro['visitante_nome']} (visitante)"
    placa = registro["placa"]
    return f"{placa[:3]}-{placa[3:]} ({registro['modelo']})" if len(placa) == 7 else placa


def atualizar_observacao(db, registro_id, observacao):
    """Só a observação pode ser corrigida; horários e vínculos ficam como foram registrados."""
    observacao = (observacao or "").strip()
    if len(observacao) > 300:
        raise ErroNegocio("A observação pode ter no máximo 300 caracteres.")
    cursor = db.execute("UPDATE registro_acesso SET observacao = ? WHERE id = ? AND ativo = 1",
                        (observacao or None, registro_id))
    if cursor.rowcount == 0:
        db.rollback()
        raise ErroNegocio("Registro de acesso não encontrado ou já excluído.")
    db.commit()


def excluir_registro(db, registro_id):
    """Exclusão lógica: o registro some das consultas comuns, mas continua no banco (RN-08)."""
    cursor = db.execute("UPDATE registro_acesso SET ativo = 0 WHERE id = ? AND ativo = 1",
                        (registro_id,))
    if cursor.rowcount == 0:
        db.rollback()
        raise ErroNegocio("Registro de acesso não encontrado ou já excluído.")
    db.commit()
