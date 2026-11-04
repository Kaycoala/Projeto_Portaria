"""Testes de login, usuários e permissões.
Execute com: python -m unittest discover tests -v
"""
import re
import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.db import conectar
from app.permissoes import PERMISSOES, tem_permissao
from app.services import usuario_service
from app.services.usuario_service import criar_usuario, perfil_id_por_nome

# Nos testes, usa menos repetições no hash para rodar mais rápido (no sistema real o padrão é mantido).
usuario_service.METODO_HASH = "pbkdf2:sha256:1000"

SENHA = "senha123"
USUARIOS = {"admin": "administrador", "porteiro1": "porteiro",
            "gerente1": "aprovador", "func1": "funcionario"}


class BaseTeste(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.caminho = Path(self.pasta.name) / "teste.db"
        self.app = create_app({"DATABASE": str(self.caminho), "TESTING": True, "SECRET_KEY": "teste"})
        db = conectar(self.caminho)
        for login, perfil in USUARIOS.items():
            criar_usuario(db, login, SENHA, perfil_id_por_nome(db, perfil))
        db.close()

    def tearDown(self):
        self.pasta.cleanup()

    # --- auxiliares ---
    def consultar(self, sql, parametros=()):
        db = conectar(self.caminho)
        try:
            return db.execute(sql, parametros).fetchall()
        finally:
            db.close()

    def id_de(self, login):
        return self.consultar("SELECT id FROM usuario WHERE login=?", (login,))[0]["id"]

    def perfil_id(self, nome):
        return self.consultar("SELECT id FROM perfil WHERE nome=?", (nome,))[0]["id"]

    def token(self, cliente):
        html = cliente.get("/", follow_redirects=True).get_data(as_text=True)
        return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)

    def entrar(self, login, senha=SENHA):
        cliente = self.app.test_client()
        resposta = cliente.post("/login", data={
            "login": login, "senha": senha, "csrf_token": self.token(cliente)})
        return cliente, resposta

    def enviar(self, cliente, url, dados=None):
        corpo = dict(dados or {})
        corpo["csrf_token"] = self.token(cliente)
        return cliente.post(url, data=corpo)


class TesteLogin(BaseTeste):
    def test_sem_login_redireciona_para_tela_de_login(self):
        for url in ("/", "/usuarios/"):
            resposta = self.app.test_client().get(url)
            self.assertEqual(resposta.status_code, 302)
            self.assertIn("/login", resposta.headers["Location"])

    def test_tela_de_login_e_publica(self):
        self.assertEqual(self.app.test_client().get("/login").status_code, 200)

    def test_login_correto_libera_acesso(self):
        cliente, resposta = self.entrar("porteiro1")
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(cliente.get("/").status_code, 200)

    def test_senha_errada_nao_entra(self):
        cliente, resposta = self.entrar("porteiro1", "errada")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Login ou senha inválidos", resposta.get_data(as_text=True))
        self.assertEqual(cliente.get("/").status_code, 302)

    def test_login_inexistente_nao_entra(self):
        _, resposta = self.entrar("fantasma")
        self.assertIn("Login ou senha inválidos", resposta.get_data(as_text=True))

    def test_login_ignora_maiusculas(self):
        cliente, resposta = self.entrar("PORTEIRO1")
        self.assertEqual(resposta.status_code, 302)

    def test_usuario_inativo_nao_entra(self):
        db = conectar(self.caminho)
        db.execute("UPDATE usuario SET ativo=0 WHERE login='func1'")
        db.commit()
        db.close()
        _, resposta = self.entrar("func1")
        self.assertIn("Login ou senha inválidos", resposta.get_data(as_text=True))

    def test_logout_encerra_a_sessao(self):
        cliente, _ = self.entrar("porteiro1")
        self.enviar(cliente, "/logout")
        self.assertEqual(cliente.get("/").status_code, 302)

    def test_senha_e_guardada_com_hash(self):
        senha_hash = self.consultar("SELECT senha_hash FROM usuario WHERE login='admin'")[0][0]
        self.assertNotEqual(senha_hash, SENHA)
        self.assertTrue(senha_hash.startswith("pbkdf2:sha256"))

    def test_formulario_sem_token_csrf_e_recusado(self):
        resposta = self.app.test_client().post("/login", data={"login": "admin", "senha": SENHA})
        self.assertEqual(resposta.status_code, 400)

    def test_usuario_desativado_perde_a_sessao_ativa(self):
        porteiro, _ = self.entrar("porteiro1")
        self.assertEqual(porteiro.get("/").status_code, 200)
        admin, _ = self.entrar("admin")
        self.enviar(admin, f"/usuarios/{self.id_de('porteiro1')}/alternar")
        self.assertEqual(porteiro.get("/").status_code, 302)


class TestePermissoes(BaseTeste):
    def test_somente_admin_acessa_usuarios(self):
        esperado = {"admin": 200, "porteiro1": 403, "gerente1": 403, "func1": 403}
        for login, codigo in esperado.items():
            cliente, _ = self.entrar(login)
            self.assertEqual(cliente.get("/usuarios/").status_code, codigo, login)

    def test_todos_os_perfis_veem_a_pagina_inicial(self):
        for login in USUARIOS:
            cliente, _ = self.entrar(login)
            self.assertEqual(cliente.get("/").status_code, 200, login)

    def test_nao_admin_nao_consegue_criar_usuario_por_post(self):
        cliente, _ = self.entrar("porteiro1")
        resposta = self.enviar(cliente, "/usuarios/novo", {
            "login": "intruso", "senha": "abc123", "perfil_id": self.perfil_id("administrador")})
        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(self.consultar("SELECT 1 FROM usuario WHERE login='intruso'"), [])

    def test_menu_so_mostra_usuarios_para_admin(self):
        admin, _ = self.entrar("admin")
        porteiro, _ = self.entrar("porteiro1")
        self.assertIn("/usuarios/", admin.get("/").get_data(as_text=True))
        self.assertNotIn("/usuarios/", porteiro.get("/").get_data(as_text=True))

    def test_matriz_de_permissoes(self):
        self.assertTrue(tem_permissao("porteiro", "registrar_acesso"))
        self.assertFalse(tem_permissao("porteiro", "autorizar_visitantes"))
        self.assertTrue(tem_permissao("aprovador", "autorizar_visitantes"))
        self.assertFalse(tem_permissao("aprovador", "registrar_acesso"))
        self.assertTrue(tem_permissao("aprovador", "consultar_historico"))
        self.assertFalse(tem_permissao("porteiro", "ver_relatorios"))
        self.assertFalse(tem_permissao("porteiro", "administrar_registros"))
        for permissao in PERMISSOES:
            self.assertFalse(tem_permissao("funcionario", permissao), permissao)
            self.assertTrue(tem_permissao("administrador", permissao), permissao)


class TesteGerenciarUsuarios(BaseTeste):
    def setUp(self):
        super().setUp()
        self.admin, _ = self.entrar("admin")

    def dados(self, **extra):
        base = {"login": "novo.user", "senha": "abc123",
                "perfil_id": self.perfil_id("porteiro"), "pessoa_id": ""}
        base.update(extra)
        return base

    def test_admin_cria_usuario_que_consegue_entrar(self):
        resposta = self.enviar(self.admin, "/usuarios/novo", self.dados())
        self.assertEqual(resposta.status_code, 302)
        _, login = self.entrar("novo.user", "abc123")
        self.assertEqual(login.status_code, 302)

    def test_login_duplicado_e_recusado(self):
        resposta = self.enviar(self.admin, "/usuarios/novo", self.dados(login="porteiro1"))
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Já existe um usuário com este login", resposta.get_data(as_text=True))

    def test_senha_curta_e_recusada(self):
        resposta = self.enviar(self.admin, "/usuarios/novo", self.dados(senha="123"))
        self.assertIn("pelo menos 6 caracteres", resposta.get_data(as_text=True))
        self.assertEqual(self.consultar("SELECT 1 FROM usuario WHERE login='novo.user'"), [])

    def test_login_invalido_e_recusado(self):
        resposta = self.enviar(self.admin, "/usuarios/novo", self.dados(login="Nome Com Espaço"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(self.consultar("SELECT 1 FROM usuario")), len(USUARIOS))

    def test_editar_sem_senha_mantem_a_senha(self):
        uid = self.id_de("func1")
        self.enviar(self.admin, f"/usuarios/{uid}/editar", self.dados(login="func1", senha="", perfil_id=self.perfil_id("funcionario")))
        _, login = self.entrar("func1")
        self.assertEqual(login.status_code, 302)

    def test_editar_troca_login_perfil_e_senha(self):
        uid = self.id_de("func1")
        self.enviar(self.admin, f"/usuarios/{uid}/editar", self.dados(login="func.novo", senha="novaSenha1"))
        _, antigo = self.entrar("func1")
        self.assertEqual(antigo.status_code, 200)
        _, novo = self.entrar("func.novo", "novaSenha1")
        self.assertEqual(novo.status_code, 302)
        self.assertEqual(self.consultar("SELECT p.nome FROM usuario u JOIN perfil p ON p.id=u.perfil_id WHERE u.id=?", (uid,))[0][0], "porteiro")

    def test_desativar_usuario_impede_login(self):
        self.enviar(self.admin, f"/usuarios/{self.id_de('func1')}/alternar")
        _, resposta = self.entrar("func1")
        self.assertEqual(resposta.status_code, 200)

    def test_reativar_usuario_permite_login(self):
        uid = self.id_de("func1")
        self.enviar(self.admin, f"/usuarios/{uid}/alternar")
        self.enviar(self.admin, f"/usuarios/{uid}/alternar")
        _, resposta = self.entrar("func1")
        self.assertEqual(resposta.status_code, 302)

    def test_admin_nao_pode_desativar_a_si_mesmo(self):
        resposta = self.enviar(self.admin, f"/usuarios/{self.id_de('admin')}/alternar")
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(self.consultar("SELECT ativo FROM usuario WHERE login='admin'")[0][0], 1)

    def test_unico_admin_nao_pode_ser_rebaixado(self):
        uid = self.id_de("admin")
        resposta = self.enviar(self.admin, f"/usuarios/{uid}/editar", self.dados(login="admin", senha=""))
        self.assertIn("único administrador", resposta.get_data(as_text=True))
        self.assertEqual(self.consultar("SELECT p.nome FROM usuario u JOIN perfil p ON p.id=u.perfil_id WHERE u.id=?", (uid,))[0][0], "administrador")

    def test_pode_rebaixar_admin_quando_existe_outro(self):
        self.enviar(self.admin, "/usuarios/novo", self.dados(login="admin2", perfil_id=self.perfil_id("administrador")))
        uid = self.id_de("admin")
        self.enviar(self.admin, f"/usuarios/{uid}/editar", self.dados(login="admin", senha=""))
        self.assertEqual(self.consultar("SELECT p.nome FROM usuario u JOIN perfil p ON p.id=u.perfil_id WHERE u.id=?", (uid,))[0][0], "porteiro")

    def test_editar_usuario_inexistente_da_404(self):
        self.assertEqual(self.admin.get("/usuarios/9999/editar").status_code, 404)


if __name__ == "__main__":
    unittest.main()
