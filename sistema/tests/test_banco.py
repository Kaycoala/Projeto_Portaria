"""Testes do banco de dados. Execute com: python -m unittest discover tests -v"""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.db import conectar, criar_banco


class TesteBanco(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.caminho = Path(self.pasta.name) / "teste.db"
        criar_banco(self.caminho)
        self.db = conectar(self.caminho)

    def tearDown(self):
        self.db.close()
        self.pasta.cleanup()

    # --- funções auxiliares ---
    def nova_pessoa(self, cpf="11111111111", nome="Ana"):
        cur = self.db.execute(
            "INSERT INTO pessoa (nome, cpf, tipo) VALUES (?, ?, 'morador')", (nome, cpf))
        return cur.lastrowid

    def novo_usuario(self, login="porteiro1"):
        perfil = self.db.execute("SELECT id FROM perfil WHERE nome='porteiro'").fetchone()[0]
        cur = self.db.execute(
            "INSERT INTO usuario (login, senha_hash, perfil_id) VALUES (?, 'x', ?)", (login, perfil))
        return cur.lastrowid

    # --- testes ---
    def test_perfis_iniciais_criados(self):
        nomes = {l[0] for l in self.db.execute("SELECT nome FROM perfil")}
        self.assertEqual(nomes, {"administrador", "aprovador", "porteiro", "funcionario"})

    def test_criar_banco_duas_vezes_nao_duplica_perfis(self):
        criar_banco(self.caminho)
        total = self.db.execute("SELECT COUNT(*) FROM perfil").fetchone()[0]
        self.assertEqual(total, 4)

    def test_cpf_duplicado_e_rejeitado(self):
        self.nova_pessoa("22222222222")
        with self.assertRaises(sqlite3.IntegrityError):
            self.nova_pessoa("22222222222", nome="Outra")

    def test_placa_duplicada_e_rejeitada(self):
        dono = self.nova_pessoa()
        sql = "INSERT INTO veiculo (placa, modelo, cor, pessoa_id) VALUES (?, 'Gol', 'Preto', ?)"
        self.db.execute(sql, ("ABC1D23", dono))
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(sql, ("ABC1D23", dono))

    def test_veiculo_com_proprietario_inexistente_e_rejeitado(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO veiculo (placa, modelo, cor, pessoa_id) VALUES ('XYZ9A99','Uno','Azul',999)")

    def test_tipo_de_pessoa_invalido_e_rejeitado(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO pessoa (nome, cpf, tipo) VALUES ('X','333','alienigena')")

    def test_status_de_autorizacao_invalido_e_rejeitado(self):
        pessoa = self.nova_pessoa()
        vis = self.db.execute(
            "INSERT INTO visitante (nome, cpf, pessoa_visitada_id, motivo) VALUES ('V','9',?, 'Reunião')",
            (pessoa,)).lastrowid
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO autorizacao (visitante_id, status) VALUES (?, 'talvez')", (vis,))

    def test_autorizacao_nasce_pendente(self):
        pessoa = self.nova_pessoa()
        vis = self.db.execute(
            "INSERT INTO visitante (nome, cpf, pessoa_visitada_id, motivo) VALUES ('V','9',?, 'Reunião')",
            (pessoa,)).lastrowid
        aut = self.db.execute("INSERT INTO autorizacao (visitante_id) VALUES (?)", (vis,)).lastrowid
        status = self.db.execute("SELECT status FROM autorizacao WHERE id=?", (aut,)).fetchone()[0]
        self.assertEqual(status, "pendente")

    def test_registro_de_acesso_valido(self):
        pessoa, porteiro = self.nova_pessoa(), self.novo_usuario()
        self.db.execute(
            "INSERT INTO registro_acesso (tipo, pessoa_id, entrada_em, porteiro_id) "
            "VALUES ('pessoa', ?, '2026-11-04 08:00:00', ?)", (pessoa, porteiro))

    def test_registro_de_acesso_sem_alvo_e_rejeitado(self):
        porteiro = self.novo_usuario()
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO registro_acesso (tipo, entrada_em, porteiro_id) "
                "VALUES ('pessoa', '2026-11-04 08:00:00', ?)", (porteiro,))

    def test_saida_antes_da_entrada_e_rejeitada(self):
        pessoa, porteiro = self.nova_pessoa(), self.novo_usuario()
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO registro_acesso (tipo, pessoa_id, entrada_em, saida_em, porteiro_id) "
                "VALUES ('pessoa', ?, '2026-11-04 09:00:00', '2026-11-04 08:00:00', ?)",
                (pessoa, porteiro))

    def test_ocorrencia_sem_descricao_e_rejeitada(self):
        porteiro = self.novo_usuario()
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO ocorrencia (data_hora, descricao, registrado_por_id) "
                "VALUES ('2026-11-04 10:00:00', '   ', ?)", (porteiro,))

    def test_ocorrencia_com_pessoas_envolvidas(self):
        porteiro, p1, p2 = self.novo_usuario(), self.nova_pessoa("1"), self.nova_pessoa("2")
        oc = self.db.execute(
            "INSERT INTO ocorrencia (data_hora, descricao, registrado_por_id) "
            "VALUES ('2026-11-04 10:00:00', 'Discussão na entrada', ?)", (porteiro,)).lastrowid
        for p in (p1, p2):
            self.db.execute("INSERT INTO ocorrencia_pessoa VALUES (?, ?)", (oc, p))
        total = self.db.execute(
            "SELECT COUNT(*) FROM ocorrencia_pessoa WHERE ocorrencia_id=?", (oc,)).fetchone()[0]
        self.assertEqual(total, 2)


class TesteAplicacao(unittest.TestCase):
    def test_app_cria_banco_na_primeira_execucao_e_exige_login(self):
        from app import create_app
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "novo.db"
            app = create_app({"DATABASE": str(caminho), "TESTING": True, "SECRET_KEY": "teste"})
            self.assertTrue(caminho.exists())
            cliente = app.test_client()
            self.assertEqual(cliente.get("/login").status_code, 200)
            self.assertEqual(cliente.get("/").status_code, 302)


if __name__ == "__main__":
    unittest.main()
