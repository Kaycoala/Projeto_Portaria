"""Testes de interface, navegação e correções gerais (V0.9.0).
Execute com: python -m unittest discover tests -v
"""
import re
import unittest
from pathlib import Path

from tests.test_autenticacao import BaseTeste

TEMPLATES = Path(__file__).resolve().parent.parent / "app" / "templates"


class BaseInterface(BaseTeste):
    def pagina(self, cliente, url):
        resposta = cliente.get(url)
        self.assertEqual(resposta.status_code, 200, url)
        return resposta.get_data(as_text=True)

    def links_do_menu(self, html):
        menu = html[html.index('id="menu-lateral"'):html.index("</nav>")]
        return re.findall(r'<a class="nav-link[^"]*" href="([^"]+)"', menu)


class TesteLayoutResponsivo(BaseInterface):
    def test_pagina_tem_viewport_bootstrap_js_e_script_do_sistema(self):
        html = self.pagina(self.entrar("admin")[0], "/")
        self.assertIn('name="viewport"', html)
        self.assertIn("bootstrap.bundle.min.js", html)      # sem ele, o botão de fechar e o menu não funcionam
        self.assertIn("js/app.js", html)

    def test_menu_vira_gaveta_em_telas_pequenas(self):
        html = self.pagina(self.entrar("admin")[0], "/")
        self.assertIn('data-bs-toggle="offcanvas"', html)
        self.assertIn('id="menu-lateral"', html)
        self.assertIn("offcanvas-lg", html)

    def test_tela_de_login_nao_mostra_menu(self):
        html = self.pagina(self.app.test_client(), "/login")
        self.assertNotIn("menu-lateral", html)
        self.assertNotIn("offcanvas", html)

    def test_arquivos_estaticos_sao_servidos(self):
        cliente = self.app.test_client()
        css = cliente.get("/static/css/style.css")
        js = cliente.get("/static/js/app.js")
        self.assertEqual((css.status_code, js.status_code), (200, 200))
        texto_css, texto_js = css.get_data(as_text=True), js.get_data(as_text=True)
        css.close()
        js.close()
        self.assertIn(".sidebar", texto_css)
        self.assertIn("disabled", texto_js)                      # proteção contra clique duplo


class TesteMenu(BaseInterface):
    def test_destaca_a_secao_atual(self):
        cliente = self.entrar("admin")[0]
        casos = {"/": "/", "/pessoas/": "/pessoas/", "/pessoas/nova": "/pessoas/", "/veiculos/": "/veiculos/",
                 "/historico/": "/historico/", "/ocorrencias/nova": "/ocorrencias/", "/relatorios/": "/relatorios/",
                 "/usuarios/novo": "/usuarios/", "/backup/": "/backup/", "/acessos/": "/acessos/"}
        for url, esperado in casos.items():
            with self.subTest(url=url):
                html = self.pagina(cliente, url)
                ativos = re.findall(r'href="([^"]+)" aria-current="page"', html)
                self.assertEqual(ativos, [esperado])

    def test_cada_perfil_ve_so_os_seus_links(self):
        esperado = {
            "admin": ["/", "/acessos/", "/pessoas/", "/veiculos/", "/visitantes/", "/autorizacoes/",
                      "/historico/", "/ocorrencias/", "/relatorios/", "/usuarios/", "/backup/"],
            "porteiro1": ["/", "/acessos/", "/pessoas/", "/veiculos/", "/visitantes/", "/historico/", "/ocorrencias/"],
            "gerente1": ["/", "/autorizacoes/", "/historico/"],
            "func1": ["/"],
        }
        for login, links in esperado.items():
            with self.subTest(login=login):
                self.assertEqual(self.links_do_menu(self.pagina(self.entrar(login)[0], "/")), links)

    def test_todos_os_links_do_menu_abrem_sem_erro(self):
        for login in ("admin", "porteiro1", "gerente1", "func1"):
            cliente = self.entrar(login)[0]
            for link in self.links_do_menu(self.pagina(cliente, "/")):
                with self.subTest(login=login, link=link):
                    self.assertEqual(cliente.get(link).status_code, 200)

    def test_formularios_de_cadastro_abrem(self):
        cliente = self.entrar("admin")[0]
        for url in ("/pessoas/nova", "/veiculos/novo", "/visitantes/novo", "/ocorrencias/nova", "/usuarios/novo"):
            with self.subTest(url=url):
                self.pagina(cliente, url)


class TestePaginasDeErro(BaseInterface):
    def test_pagina_inexistente_mostra_mensagem_amigavel(self):
        resposta = self.entrar("admin")[0].get("/nao-existe")
        self.assertEqual(resposta.status_code, 404)
        self.assertIn("Página não encontrada", resposta.get_data(as_text=True))

    def test_metodo_nao_permitido_mostra_pagina_do_sistema(self):
        resposta = self.entrar("admin")[0].get("/logout")
        corpo = resposta.get_data(as_text=True)
        self.assertEqual(resposta.status_code, 405)
        self.assertIn("não pode ser feita desta forma", corpo)
        self.assertIn("menu-lateral", corpo)          # continua dentro do layout do sistema

    def test_erro_interno_mostra_pagina_simples_sem_detalhes_tecnicos(self):
        def quebra():
            raise RuntimeError("segredo-interno-do-codigo")
        self.app.add_url_rule("/_teste_erro", "teste_erro", quebra)
        self.app.config["PROPAGATE_EXCEPTIONS"] = False
        cliente = self.entrar("admin")[0]
        with self.assertLogs(self.app.logger, level="ERROR"):     # o erro vai para o terminal, não para a tela
            resposta = cliente.get("/_teste_erro")
        corpo = resposta.get_data(as_text=True)
        self.assertEqual(resposta.status_code, 500)
        self.assertIn("erro inesperado", corpo)
        self.assertNotIn("segredo-interno-do-codigo", corpo)
        self.assertNotIn("Traceback", corpo)

    def test_perfil_sem_permissao_recebe_403_amigavel(self):
        resposta = self.entrar("func1")[0].get("/pessoas/")
        self.assertEqual(resposta.status_code, 403)
        self.assertIn("não tem permissão", resposta.get_data(as_text=True))


class TesteMensagens(BaseInterface):
    def test_erro_aparece_em_vermelho_e_sucesso_em_verde(self):
        cliente = self.entrar("admin")[0]
        erro = self.enviar(cliente, "/pessoas/nova", {"nome": "Jo"})
        self.assertIn("alert-danger", erro.get_data(as_text=True))
        ok = self.enviar(cliente, "/pessoas/nova", {
            "nome": "Maria da Silva", "cpf": "11144477735", "tipo": "morador"}, )
        self.assertEqual(ok.status_code, 302)
        self.assertIn("alert-success", cliente.get(ok.headers["Location"]).get_data(as_text=True))


class TesteQualidadeDosTemplates(unittest.TestCase):
    """Conferências automáticas sobre todos os arquivos HTML (evitam esquecimentos nas próximas telas)."""

    def arquivos(self):
        return sorted(TEMPLATES.rglob("*.html"))

    def test_todo_formulario_post_tem_token_csrf(self):
        for arquivo in self.arquivos():
            texto = arquivo.read_text(encoding="utf-8")
            formularios = len(re.findall(r'<form[^>]*method="post"', texto))
            tokens = len(re.findall(r'name="csrf_token"', texto))
            with self.subTest(arquivo=arquivo.name):
                self.assertGreaterEqual(tokens, formularios)

    def test_toda_tabela_rola_na_horizontal_em_tela_pequena(self):
        for arquivo in self.arquivos():
            texto = arquivo.read_text(encoding="utf-8")
            with self.subTest(arquivo=arquivo.name):
                self.assertLessEqual(texto.count("<table"), texto.count("table-responsive"))

    def test_todo_campo_de_formulario_tem_rotulo_ou_aria_label(self):
        for arquivo in self.arquivos():
            texto = arquivo.read_text(encoding="utf-8")
            for campo in re.findall(r"<(?:input|select|textarea)\b[^>]*>", texto):
                if 'type="hidden"' in campo or 'type="checkbox"' in campo:
                    continue
                with self.subTest(arquivo=arquivo.name, campo=campo[:60]):
                    self.assertTrue(re.search(r'\bid="', campo) or "aria-label" in campo)


if __name__ == "__main__":
    unittest.main()
