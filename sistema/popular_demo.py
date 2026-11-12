"""Cria dados FICTÍCIOS para demonstração (prints e vídeo).

NÃO use em um banco com dados reais. O script só roda se o banco ainda não tiver pessoas
cadastradas (use --forcar para ignorar essa proteção).

Uso (dentro de `sistema`):
    venv\\Scripts\\python.exe criar_admin.py        (se ainda não existir um administrador)
    venv\\Scripts\\python.exe popular_demo.py

Cria os usuários  porteiro / demo123  e  gerente / demo123,  pessoas, veículos, visitantes
(aguardando, autorizados e negado), entradas e saídas dos últimos dias e ocorrências.
Tudo é criado pelas mesmas regras do sistema (não há atalhos no banco, exceto recuar as datas
dos registros antigos para o histórico ter vários dias).
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

from app.db import conectar, criar_banco
from app.services import (acesso_service, autorizacao_service, ocorrencia_service,
                          pessoa_service, usuario_service, veiculo_service, visitante_service)
from app.services.erros import ErroNegocio

CAMINHO = Path(__file__).resolve().parent / "instance" / "portaria.db"
SENHA_DEMO = "demo123"

PESSOAS = [  # (nome, endereço/setor, tipo)
    ("Ana Beatriz Lima", "Bloco A, ap. 101", "morador"),
    ("Carlos Eduardo Ramos", "Bloco A, ap. 203", "morador"),
    ("Fernanda Alves Pinto", "Bloco B, ap. 305", "morador"),
    ("Roberto Nascimento", "Bloco C, ap. 402", "morador"),
    ("Marcos Vinícius Pereira", "Zeladoria", "funcionario"),
    ("Luciana Martins", "Administração", "funcionario"),
    ("Paulo Henrique Souza", "Manutenção elétrica", "prestador"),
    ("Juliana Castro", "Limpeza", "prestador"),
]
VEICULOS = [  # (placa, modelo, cor, índice do proprietário em PESSOAS)
    ("ABC1D23", "Honda Civic", "Prata", 0),
    ("FGH4I56", "Fiat Argo", "Branco", 1),
    ("JKL7M89", "Volkswagen Polo", "Vermelho", 2),
    ("NOP2Q34", "Toyota Corolla", "Preto", 3),
    ("RST5U67", "Chevrolet Onix", "Azul", 4),
]


def gerar_cpf(numero_base):
    """CPF com dígitos verificadores corretos, gerado a partir de um número (dados fictícios)."""
    digitos = [int(c) for c in f"{numero_base:09d}"]
    for tamanho in (9, 10):
        soma = sum(d * (tamanho + 1 - i) for i, d in enumerate(digitos[:tamanho]))
        resto = (soma * 10) % 11
        digitos.append(0 if resto == 10 else resto)
    return "".join(str(d) for d in digitos)


def _recuar(db, registro_id, dias, hora_entrada, minutos_dentro):
    """Move um registro para alguns dias atrás (para o histórico ter vários dias)."""
    entrada = (datetime.now() - timedelta(days=dias)).replace(
        hour=hora_entrada, minute=(registro_id * 7) % 60, second=0, microsecond=0)
    saida = entrada + timedelta(minutes=minutos_dentro)
    db.execute("UPDATE registro_acesso SET entrada_em = ?, saida_em = ? WHERE id = ?",
               (entrada.strftime("%Y-%m-%d %H:%M:%S"), saida.strftime("%Y-%m-%d %H:%M:%S"), registro_id))
    db.commit()


def _usuario(db, login, perfil):
    existente = db.execute("SELECT id FROM usuario WHERE login = ?", (login,)).fetchone()
    if existente:
        return existente["id"]
    return usuario_service.criar_usuario(db, login, SENHA_DEMO,
                                         usuario_service.perfil_id_por_nome(db, perfil))


def popular(caminho, forcar=False):
    """Cria os dados de demonstração. Devolve um resumo (dicionário)."""
    criar_banco(caminho)
    db = conectar(caminho)
    try:
        if not forcar and db.execute("SELECT COUNT(*) FROM pessoa").fetchone()[0] > 0:
            raise ErroNegocio("O banco já tem pessoas cadastradas. Por segurança, nada foi criado "
                              "(use --forcar apenas em um banco de testes).")

        porteiro = _usuario(db, "porteiro", "porteiro")
        gerente = _usuario(db, "gerente", "aprovador")
        hoje = datetime.now().date().isoformat()

        ids = []
        for i, (nome, local, tipo) in enumerate(PESSOAS):
            telefone = f"1699{(i + 1) * 1111111:07d}"[:11]
            email = nome.split()[0].lower().replace("é", "e") + "@exemplo.com.br"
            ids.append(pessoa_service.criar_pessoa(db, nome, gerar_cpf(111222330 + i * 37),
                                                   telefone, email, local, tipo))
        veiculos = [veiculo_service.criar_veiculo(db, placa, modelo, cor, ids[dono])
                    for placa, modelo, cor, dono in VEICULOS]

        def visitante(nome, n, visitada, motivo):
            return visitante_service.criar_visitante(
                db, nome, gerar_cpf(555666770 + n * 41), f"1698{n * 1234567:07d}"[:11], ids[visitada], motivo)

        pedro, aut_pedro = visitante("Pedro Almeida", 1, 0, "Visita familiar")
        camila, aut_camila = visitante("Camila Duarte", 2, 1, "Entrega de documentos")
        visitante("Rafael Gomes", 3, 2, "Reunião de condomínio")        # fica aguardando
        visitante("Beatriz Nogueira", 4, 3, "Instalação de internet")   # fica aguardando
        _, aut_tiago = visitante("Tiago Moreira", 5, 0, "Visita sem aviso")
        autorizacao_service.aprovar(db, aut_pedro, gerente, hoje, "", "Visita combinada com a moradora")
        autorizacao_service.aprovar(db, aut_camila, gerente, hoje, "", "")
        autorizacao_service.negar(db, aut_tiago, gerente, "Morador não autorizou a visita")

        # --- movimentação dos últimos dias (histórico e relatórios) ---
        for dias in range(5, 0, -1):
            for k, pessoa in enumerate((0, 1, 4, 5, 6)):
                registro = acesso_service.registrar_entrada_pessoa(db, ids[pessoa], porteiro, "")
                acesso_service.registrar_saida(db, registro)
                _recuar(db, registro, dias, 7 + k, 90 + 25 * k)
            for k, veiculo in enumerate((0, 1, 3)):
                registro = acesso_service.registrar_entrada_veiculo(db, veiculos[veiculo], porteiro, "")
                acesso_service.registrar_saida(db, registro)
                _recuar(db, registro, dias, 17 + k, 40 + 10 * k)

        # --- movimentação de hoje ---
        registro = acesso_service.registrar_entrada_visitante(db, pedro, porteiro, "Foi ao ap. 101")
        acesso_service.registrar_saida(db, registro)
        acesso_service.registrar_entrada_visitante(db, camila, porteiro, "")            # continua dentro
        for pessoa in (0, 4):                                                          # continuam dentro
            acesso_service.registrar_entrada_pessoa(db, ids[pessoa], porteiro, "")
        saiu = acesso_service.registrar_entrada_pessoa(db, ids[6], porteiro, "Troca de lâmpadas")
        acesso_service.registrar_saida(db, saiu)
        acesso_service.registrar_entrada_veiculo(db, veiculos[0], porteiro, "")         # continua dentro
        saiu = acesso_service.registrar_entrada_veiculo(db, veiculos[1], porteiro, "")
        acesso_service.registrar_saida(db, saiu)

        ontem = (datetime.now() - timedelta(days=1)).replace(hour=14, minute=30).strftime("%Y-%m-%dT%H:%M")
        ocorrencia_service.criar_ocorrencia(
            db, ontem, "Visitante tentou entrar sem autorização e foi orientado a aguardar a liberação do morador.",
            [ids[0]], porteiro)
        ocorrencia_service.criar_ocorrencia(
            db, ocorrencia_service.agora_para_formulario(),
            "Portão da garagem demorou a abrir; manutenção acionada.", [ids[4]], porteiro)

        return {"pessoas": len(ids), "veiculos": len(veiculos), "visitantes": 5,
                "senha": SENHA_DEMO, "usuarios": ["porteiro", "gerente"]}
    finally:
        db.close()


if __name__ == "__main__":
    try:
        resumo = popular(CAMINHO, forcar="--forcar" in sys.argv)
    except ErroNegocio as erro:
        print(f"Erro: {erro}")
        sys.exit(1)
    print("Dados de demonstração criados (todos fictícios).")
    print(f"  {resumo['pessoas']} pessoas, {resumo['veiculos']} veículos, {resumo['visitantes']} visitantes.")
    print(f"  Usuários: porteiro e gerente (senha {resumo['senha']}). O administrador é o que você criou.")
