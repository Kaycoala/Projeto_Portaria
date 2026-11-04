"""Regras de negócio do cadastro de veículos (RF-02, RN-07)."""
import re
import sqlite3

from app.services.erros import ErroNegocio

# Formato antigo (ABC1234) e formato Mercosul (ABC1D23).
PADRAO_PLACA = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")

SQL_VEICULOS = (
    "SELECT v.id, v.placa, v.modelo, v.cor, v.ativo, v.pessoa_id, "
    "       p.nome AS proprietario, p.ativo AS proprietario_ativo "
    "FROM veiculo v JOIN pessoa p ON p.id = v.pessoa_id "
)


def normalizar_placa(placa):
    """Maiúscula, sem espaços nem traço."""
    return re.sub(r"[\s-]", "", placa or "").upper()


def formatar_placa(placa):
    """ABC-1234 (só para exibir; no banco a placa fica sem traço)."""
    placa = normalizar_placa(placa)
    if len(placa) == 7:
        return f"{placa[:3]}-{placa[3:]}"
    return placa


def listar_veiculos(db, busca="", incluir_inativos=True):
    """Lista veículos. A busca procura na placa, no modelo ou no nome do proprietário."""
    sql = SQL_VEICULOS + "WHERE 1 = 1"
    parametros = []
    if not incluir_inativos:
        sql += " AND v.ativo = 1"
    busca = (busca or "").strip()
    if busca:
        sql += " AND (v.placa LIKE ? OR v.modelo LIKE ? OR p.nome LIKE ?)"
        parametros += [f"%{normalizar_placa(busca)}%", f"%{busca}%", f"%{busca}%"]
    sql += " ORDER BY v.placa"
    return db.execute(sql, parametros).fetchall()


def buscar_veiculo(db, veiculo_id):
    return db.execute(SQL_VEICULOS + "WHERE v.id = ?", (veiculo_id,)).fetchone()


def listar_proprietarios(db, incluir_id=None):
    """Pessoas ativas que podem ser proprietárias (mais a atual, se ela estiver inativa)."""
    return db.execute(
        "SELECT id, nome, cpf FROM pessoa WHERE ativo = 1 OR id = ? ORDER BY nome COLLATE NOCASE",
        (incluir_id,)).fetchall()


def _validar(db, placa, modelo, cor, pessoa_id, veiculo_id=None, proprietario_atual_id=None):
    """Confere os dados e devolve um dicionário já limpo."""
    placa = normalizar_placa(placa)
    if not PADRAO_PLACA.match(placa):
        raise ErroNegocio("Placa inválida. Use o formato ABC-1234 ou ABC1D23.")

    modelo = " ".join((modelo or "").split())
    if not modelo:
        raise ErroNegocio("Informe o modelo do veículo.")

    cor = " ".join((cor or "").split())
    if not cor:
        raise ErroNegocio("Informe a cor do veículo.")

    try:
        pessoa_id = int(pessoa_id)
    except (TypeError, ValueError):
        raise ErroNegocio("Escolha o proprietário do veículo.")
    pessoa = db.execute("SELECT ativo FROM pessoa WHERE id = ?", (pessoa_id,)).fetchone()
    if pessoa is None:
        raise ErroNegocio("Proprietário não encontrado.")
    # Pessoa inativa só é aceita se já era a proprietária deste veículo (não mudou).
    if not pessoa["ativo"] and pessoa_id != proprietario_atual_id:
        raise ErroNegocio("O proprietário escolhido está inativo.")

    existente = db.execute("SELECT id FROM veiculo WHERE placa = ?", (placa,)).fetchone()
    if existente is not None and existente["id"] != veiculo_id:
        raise ErroNegocio("Já existe um veículo com esta placa.")  # RN-07

    return {"placa": placa, "modelo": modelo, "cor": cor, "pessoa_id": pessoa_id}


def criar_veiculo(db, placa, modelo, cor, pessoa_id):
    d = _validar(db, placa, modelo, cor, pessoa_id)
    try:
        cursor = db.execute(
            "INSERT INTO veiculo (placa, modelo, cor, pessoa_id) VALUES (?, ?, ?, ?)",
            (d["placa"], d["modelo"], d["cor"], d["pessoa_id"]))
        db.commit()
    except sqlite3.IntegrityError:    # garantia extra: o banco também não aceita placa repetida
        raise ErroNegocio("Já existe um veículo com esta placa.")
    return cursor.lastrowid


def atualizar_veiculo(db, veiculo_id, placa, modelo, cor, pessoa_id):
    atual = buscar_veiculo(db, veiculo_id)
    if atual is None:
        raise ErroNegocio("Veículo não encontrado.")
    d = _validar(db, placa, modelo, cor, pessoa_id, veiculo_id, atual["pessoa_id"])
    try:
        db.execute("UPDATE veiculo SET placa = ?, modelo = ?, cor = ?, pessoa_id = ? WHERE id = ?",
                   (d["placa"], d["modelo"], d["cor"], d["pessoa_id"], veiculo_id))
        db.commit()
    except sqlite3.IntegrityError:
        raise ErroNegocio("Já existe um veículo com esta placa.")


def alternar_ativo(db, veiculo_id):
    """Ativa ou desativa o veículo (não apaga). Devolve True se ficou ativo."""
    atual = buscar_veiculo(db, veiculo_id)
    if atual is None:
        raise ErroNegocio("Veículo não encontrado.")
    if not atual["ativo"] and not atual["proprietario_ativo"]:
        raise ErroNegocio("Não é possível ativar o veículo: o proprietário está inativo.")
    novo = 0 if atual["ativo"] else 1
    db.execute("UPDATE veiculo SET ativo = ? WHERE id = ?", (novo, veiculo_id))
    db.commit()
    return bool(novo)
