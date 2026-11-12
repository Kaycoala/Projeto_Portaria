"""Testes do script de dados de demonstração e correções da V1.0.0.
Execute com: python -m unittest discover tests -v
"""
import re
import tempfile
import unittest
from pathlib import Path

import popular_demo
from app import create_app
from app.db import conectar
from app.services import usuario_service
from app.services.erros import ErroNegocio

usuario_service.METODO_HASH = "pbkdf2:sha256:1000"   # hash mais leve só nos testes


class TesteDadosDeDemonstracao(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.caminho = Path(self.pasta.name) / "demo.db"

    def tearDown(self):
        self.pasta.cleanup()

    def contar(self, sql):
        db = conectar(self.caminho)
        try:
            return db.execute(sql).fetchone()[0]
        finally:
            db.close()

    def test_cria_dados_coerentes_com_as_regras_do_sistema(self):
        resumo = popular_demo.popular(self.caminho)
        self.assertEqual(resumo["pessoas"], 8)
        self.assertEqual(self.contar("SELECT COUNT(*) FROM pessoa"), 8)
        self.assertEqual(self.contar("SELECT COUNT(*) FROM veiculo"), 5)
        self.assertEqual(self.contar("SELECT COUNT(*) FROM visitante"), 5)
        # 2 visitantes aguardando, 2 autorizados e 1 negado
        self.assertEqual(self.contar("SELECT COUNT(*) FROM autorizacao WHERE status='pendente'"), 2)
        self.assertEqual(self.contar("SELECT COUNT(*) FROM autorizacao WHERE status='aprovada'"), 2)
        self.assertEqual(self.contar("SELECT COUNT(*) FROM autorizacao WHERE status='negada'"), 1)
        # existe gente "dentro agora" e histórico de vários dias
        self.assertGreater(self.contar("SELECT COUNT(*) FROM registro_acesso WHERE saida_em IS NULL"), 0)
        self.assertGreaterEqual(
            self.contar("SELECT COUNT(DISTINCT substr(entrada_em, 1, 10)) FROM registro_acesso"), 5)
        self.assertEqual(self.contar("SELECT COUNT(*) FROM ocorrencia"), 2)
        self.assertEqual(self.contar("SELECT COUNT(*) FROM registro_acesso WHERE saida_em < entrada_em"), 0)

    def test_cpfs_gerados_sao_validos_e_unicos(self):
        popular_demo.popular(self.caminho)
        self.assertEqual(self.contar("SELECT COUNT(DISTINCT cpf) FROM pessoa"), 8)
        self.assertEqual(popular_demo.gerar_cpf(529982247), "52998224725")   # CPF de teste conhecido: dígitos verificadores corretos

    def test_nao_roda_em_banco_que_ja_tem_pessoas(self):
        popular_demo.popular(self.caminho)
        with self.assertRaisesRegex(ErroNegocio, "já tem pessoas"):
            popular_demo.popular(self.caminho)
        self.assertEqual(self.contar("SELECT COUNT(*) FROM pessoa"), 8)

    def test_usuarios_de_demonstracao_conseguem_entrar(self):
        popular_demo.popular(self.caminho)
        app = create_app({"DATABASE": str(self.caminho), "TESTING": True, "SECRET_KEY": "teste"})
        for login in ("porteiro", "gerente"):
            cliente = app.test_client()
            token = re.search(r'name="csrf_token" value="([^"]+)"',
                              cliente.get("/login").get_data(as_text=True)).group(1)
            resposta = cliente.post("/login", data={"login": login, "senha": "demo123", "csrf_token": token})
            self.assertEqual(resposta.status_code, 302, login)


class TesteCorrecoesV100(unittest.TestCase):
    def test_csv_tem_charset_uma_unica_vez(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "t.db"
            app = create_app({"DATABASE": str(caminho), "TESTING": True, "SECRET_KEY": "teste"})
            db = conectar(caminho)
            usuario_service.criar_usuario(db, "admin", "senha123",
                                          usuario_service.perfil_id_por_nome(db, "administrador"))
            db.close()
            cliente = app.test_client()
            token = re.search(r'name="csrf_token" value="([^"]+)"',
                              cliente.get("/login").get_data(as_text=True)).group(1)
            cliente.post("/login", data={"login": "admin", "senha": "senha123", "csrf_token": token})
            tipo = cliente.get("/relatorios/csv").headers["Content-Type"]
            self.assertEqual(tipo.count("charset"), 1, tipo)
            self.assertTrue(tipo.startswith("text/csv"))


if __name__ == "__main__":
    unittest.main()
