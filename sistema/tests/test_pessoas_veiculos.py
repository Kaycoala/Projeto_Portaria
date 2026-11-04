"""Testes do cadastro de pessoas e veículos (V0.4.0).
Execute com: python -m unittest discover tests -v
"""
import unittest

from app.db import conectar
from app.services import pessoa_service, veiculo_service
from app.services.erros import ErroNegocio
from tests.test_autenticacao import BaseTeste

CPF_1 = "11144477735"
CPF_2 = "52998224725"


def dados_pessoa(**mudancas):
    dados = {"nome": "Maria da Silva", "cpf": "111.444.777-35", "telefone": "(11) 91234-5678",
             "email": "Maria@Exemplo.com", "endereco_setor": "Bloco A, apto 12", "tipo": "morador"}
    dados.update(mudancas)
    return dados


class BasePessoasVeiculos(BaseTeste):
    def criar_pessoa(self, **mudancas):
        db = conectar(self.caminho)
        try:
            return pessoa_service.criar_pessoa(db, **dados_pessoa(**mudancas))
        finally:
            db.close()

    def criar_veiculo(self, pessoa_id, placa="ABC-1234", modelo="Gol", cor="Prata"):
        db = conectar(self.caminho)
        try:
            return veiculo_service.criar_veiculo(db, placa, modelo, cor, pessoa_id)
        finally:
            db.close()


class TestePessoaServico(BasePessoasVeiculos):
    def test_cria_pessoa_e_normaliza_os_dados(self):
        pessoa_id = self.criar_pessoa()
        linha = self.consultar("SELECT * FROM pessoa WHERE id=?", (pessoa_id,))[0]
        self.assertEqual(linha["cpf"], CPF_1)                  # só números
        self.assertEqual(linha["telefone"], "11912345678")
        self.assertEqual(linha["email"], "maria@exemplo.com")  # minúsculas
        self.assertEqual(linha["ativo"], 1)

    def test_campos_opcionais_podem_ficar_vazios(self):
        pessoa_id = self.criar_pessoa(telefone="", email="", endereco_setor="")
        linha = self.consultar("SELECT * FROM pessoa WHERE id=?", (pessoa_id,))[0]
        self.assertIsNone(linha["telefone"])
        self.assertIsNone(linha["email"])
        self.assertIsNone(linha["endereco_setor"])

    def test_cpf_duplicado_e_recusado(self):
        self.criar_pessoa()
        db = conectar(self.caminho)
        with self.assertRaisesRegex(ErroNegocio, "Já existe uma pessoa com este CPF"):
            pessoa_service.criar_pessoa(db, **dados_pessoa(nome="Outra Pessoa", cpf=CPF_1))
        db.close()

    def test_cpf_duplicado_com_formatacao_diferente_tambem_e_recusado(self):
        self.criar_pessoa(cpf="111.444.777-35")
        db = conectar(self.caminho)
        with self.assertRaisesRegex(ErroNegocio, "Já existe uma pessoa com este CPF"):
            pessoa_service.criar_pessoa(db, **dados_pessoa(cpf="11144477735"))
        db.close()

    def test_dados_invalidos_sao_recusados(self):
        db = conectar(self.caminho)
        casos = [
            ({"nome": "Jo"}, "nome completo"),
            ({"cpf": "123"}, "11 números"),
            ({"cpf": ""}, "11 números"),
            ({"telefone": "123"}, "telefone"),
            ({"email": "sem-arroba"}, "e-mail"),
            ({"tipo": "visitante"}, "tipo"),
            ({"tipo": ""}, "tipo"),
        ]
        for mudanca, trecho in casos:
            with self.subTest(mudanca=mudanca):
                with self.assertRaisesRegex(ErroNegocio, trecho):
                    pessoa_service.criar_pessoa(db, **dados_pessoa(**mudanca))
        db.close()
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM pessoa")[0]["n"], 0)

    def test_atualizar_pessoa(self):
        pessoa_id = self.criar_pessoa()
        db = conectar(self.caminho)
        pessoa_service.atualizar_pessoa(db, pessoa_id, **dados_pessoa(nome="Maria Souza", tipo="funcionario"))
        db.close()
        linha = self.consultar("SELECT * FROM pessoa WHERE id=?", (pessoa_id,))[0]
        self.assertEqual(linha["nome"], "Maria Souza")
        self.assertEqual(linha["tipo"], "funcionario")

    def test_atualizar_mantendo_o_proprio_cpf_funciona(self):
        pessoa_id = self.criar_pessoa()
        db = conectar(self.caminho)
        pessoa_service.atualizar_pessoa(db, pessoa_id, **dados_pessoa(telefone=""))   # mesmo CPF
        db.close()

    def test_atualizar_para_cpf_de_outra_pessoa_e_recusado(self):
        self.criar_pessoa()
        outra = self.criar_pessoa(nome="João Pereira", cpf=CPF_2)
        db = conectar(self.caminho)
        with self.assertRaisesRegex(ErroNegocio, "Já existe uma pessoa com este CPF"):
            pessoa_service.atualizar_pessoa(db, outra, **dados_pessoa(nome="João Pereira", cpf=CPF_1))
        db.close()

    def test_atualizar_pessoa_inexistente(self):
        db = conectar(self.caminho)
        with self.assertRaisesRegex(ErroNegocio, "não encontrada"):
            pessoa_service.atualizar_pessoa(db, 999, **dados_pessoa())
        db.close()

    def test_alternar_ativo_nao_apaga_a_pessoa(self):
        pessoa_id = self.criar_pessoa()
        db = conectar(self.caminho)
        self.assertFalse(pessoa_service.alternar_ativo(db, pessoa_id))
        self.assertTrue(pessoa_service.alternar_ativo(db, pessoa_id))
        db.close()
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM pessoa")[0]["n"], 1)

    def test_busca_por_nome_e_cpf(self):
        self.criar_pessoa()
        self.criar_pessoa(nome="João Pereira", cpf=CPF_2)
        db = conectar(self.caminho)
        nomes = lambda busca: [p["nome"] for p in pessoa_service.listar_pessoas(db, busca)]
        self.assertEqual(nomes("")[0], "João Pereira")          # ordem alfabética
        self.assertEqual(len(nomes("")), 2)
        self.assertEqual(nomes("maria"), ["Maria da Silva"])
        self.assertEqual(nomes("529.982"), ["João Pereira"])    # CPF com pontuação
        self.assertEqual(nomes("52998224725"), ["João Pereira"])
        self.assertEqual(nomes("inexistente"), [])
        db.close()

    def test_formatar_cpf(self):
        self.assertEqual(pessoa_service.formatar_cpf("11144477735"), "111.444.777-35")
        self.assertEqual(pessoa_service.formatar_cpf("123"), "123")
        self.assertEqual(pessoa_service.formatar_cpf(None), "")


class TesteVeiculoServico(BasePessoasVeiculos):
    def setUp(self):
        super().setUp()
        self.dono = self.criar_pessoa()

    def test_cria_veiculo_e_normaliza_a_placa(self):
        veiculo_id = self.criar_veiculo(self.dono, placa=" abc-1234 ")
        linha = self.consultar("SELECT * FROM veiculo WHERE id=?", (veiculo_id,))[0]
        self.assertEqual(linha["placa"], "ABC1234")
        self.assertEqual(linha["pessoa_id"], self.dono)
        self.assertEqual(linha["ativo"], 1)

    def test_aceita_placa_mercosul(self):
        self.criar_veiculo(self.dono, placa="abc1d23")
        self.assertEqual(self.consultar("SELECT placa FROM veiculo")[0]["placa"], "ABC1D23")

    def test_placa_duplicada_e_recusada(self):
        self.criar_veiculo(self.dono, placa="ABC-1234")
        db = conectar(self.caminho)
        for repetida in ("abc1234", "ABC 1234", "ABC-1234"):
            with self.subTest(placa=repetida):
                with self.assertRaisesRegex(ErroNegocio, "Já existe um veículo com esta placa"):
                    veiculo_service.criar_veiculo(db, repetida, "Uno", "Preto", self.dono)
        db.close()

    def test_dados_invalidos_sao_recusados(self):
        db = conectar(self.caminho)
        casos = [
            (("12", "Gol", "Prata", self.dono), "Placa inválida"),
            (("ABCD123", "Gol", "Prata", self.dono), "Placa inválida"),
            (("", "Gol", "Prata", self.dono), "Placa inválida"),
            (("ABC1234", "", "Prata", self.dono), "modelo"),
            (("ABC1234", "Gol", "", self.dono), "cor"),
            (("ABC1234", "Gol", "Prata", ""), "proprietário"),
            (("ABC1234", "Gol", "Prata", "abc"), "proprietário"),
        ]
        for argumentos, trecho in casos:
            with self.subTest(argumentos=argumentos):
                with self.assertRaisesRegex(ErroNegocio, trecho):
                    veiculo_service.criar_veiculo(db, *argumentos)
        db.close()
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM veiculo")[0]["n"], 0)

    def test_proprietario_inexistente_e_recusado(self):
        db = conectar(self.caminho)
        with self.assertRaisesRegex(ErroNegocio, "Proprietário não encontrado"):
            veiculo_service.criar_veiculo(db, "ABC1234", "Gol", "Prata", 999)
        db.close()

    def test_proprietario_inativo_e_recusado(self):
        db = conectar(self.caminho)
        pessoa_service.alternar_ativo(db, self.dono)
        with self.assertRaisesRegex(ErroNegocio, "inativo"):
            veiculo_service.criar_veiculo(db, "ABC1234", "Gol", "Prata", self.dono)
        db.close()

    def test_atualizar_veiculo(self):
        outro = self.criar_pessoa(nome="João Pereira", cpf=CPF_2)
        veiculo_id = self.criar_veiculo(self.dono)
        db = conectar(self.caminho)
        veiculo_service.atualizar_veiculo(db, veiculo_id, "ABC-1234", "Gol G5", "Azul", outro)
        db.close()
        linha = self.consultar("SELECT * FROM veiculo WHERE id=?", (veiculo_id,))[0]
        self.assertEqual((linha["modelo"], linha["cor"], linha["pessoa_id"]), ("Gol G5", "Azul", outro))

    def test_atualizar_para_placa_de_outro_veiculo_e_recusado(self):
        self.criar_veiculo(self.dono, placa="AAA1111")
        segundo = self.criar_veiculo(self.dono, placa="BBB2222")
        db = conectar(self.caminho)
        with self.assertRaisesRegex(ErroNegocio, "Já existe um veículo com esta placa"):
            veiculo_service.atualizar_veiculo(db, segundo, "AAA-1111", "Gol", "Prata", self.dono)
        db.close()

    def test_veiculo_de_dono_inativo_continua_editavel_sem_trocar_o_dono(self):
        veiculo_id = self.criar_veiculo(self.dono)
        db = conectar(self.caminho)
        pessoa_service.alternar_ativo(db, self.dono)
        veiculo_service.atualizar_veiculo(db, veiculo_id, "ABC1234", "Gol", "Preto", self.dono)
        db.close()

    def test_nao_ativa_veiculo_de_proprietario_inativo(self):
        veiculo_id = self.criar_veiculo(self.dono)
        db = conectar(self.caminho)
        veiculo_service.alternar_ativo(db, veiculo_id)       # desativa
        pessoa_service.alternar_ativo(db, self.dono)         # dono fica inativo
        with self.assertRaisesRegex(ErroNegocio, "proprietário está inativo"):
            veiculo_service.alternar_ativo(db, veiculo_id)
        db.close()

    def test_alternar_ativo_nao_apaga_o_veiculo(self):
        veiculo_id = self.criar_veiculo(self.dono)
        db = conectar(self.caminho)
        self.assertFalse(veiculo_service.alternar_ativo(db, veiculo_id))
        self.assertTrue(veiculo_service.alternar_ativo(db, veiculo_id))
        db.close()
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM veiculo")[0]["n"], 1)

    def test_busca_por_placa_modelo_e_proprietario(self):
        outro = self.criar_pessoa(nome="João Pereira", cpf=CPF_2)
        self.criar_veiculo(self.dono, placa="ABC-1234", modelo="Gol")
        self.criar_veiculo(outro, placa="XYZ1D23", modelo="Onix")
        db = conectar(self.caminho)
        placas = lambda busca: [v["placa"] for v in veiculo_service.listar_veiculos(db, busca)]
        self.assertEqual(placas(""), ["ABC1234", "XYZ1D23"])
        self.assertEqual(placas("abc-12"), ["ABC1234"])
        self.assertEqual(placas("onix"), ["XYZ1D23"])
        self.assertEqual(placas("joão"), ["XYZ1D23"])
        self.assertEqual(placas("nada"), [])
        db.close()

    def test_formatar_placa(self):
        self.assertEqual(veiculo_service.formatar_placa("abc1234"), "ABC-1234")
        self.assertEqual(veiculo_service.formatar_placa("ABC1D23"), "ABC-1D23")


class TesteTelasPermissoes(BasePessoasVeiculos):
    URLS = ("/pessoas/", "/pessoas/nova", "/veiculos/", "/veiculos/novo")

    def test_sem_login_redireciona_para_o_login(self):
        for url in self.URLS:
            with self.subTest(url=url):
                resposta = self.app.test_client().get(url)
                self.assertEqual(resposta.status_code, 302)
                self.assertIn("/login", resposta.headers["Location"])

    def test_admin_e_porteiro_acessam(self):
        for login in ("admin", "porteiro1"):
            cliente, _ = self.entrar(login)
            for url in self.URLS:
                with self.subTest(login=login, url=url):
                    self.assertEqual(cliente.get(url).status_code, 200)

    def test_aprovador_e_funcionario_recebem_403(self):
        pessoa_id = self.criar_pessoa()
        veiculo_id = self.criar_veiculo(pessoa_id)
        for login in ("gerente1", "func1"):
            cliente, _ = self.entrar(login)
            for url in self.URLS + (f"/pessoas/{pessoa_id}/editar", f"/veiculos/{veiculo_id}/editar"):
                with self.subTest(login=login, url=url):
                    self.assertEqual(cliente.get(url).status_code, 403)
            for url in (f"/pessoas/{pessoa_id}/alternar", f"/veiculos/{veiculo_id}/alternar"):
                with self.subTest(login=login, url=url):
                    self.assertEqual(self.enviar(cliente, url).status_code, 403)
            resposta = self.enviar(cliente, "/pessoas/nova", dados_pessoa(cpf=CPF_2))
            self.assertEqual(resposta.status_code, 403)
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM pessoa")[0]["n"], 1)
        self.assertEqual(self.consultar("SELECT ativo FROM pessoa")[0]["ativo"], 1)

    def test_menu_mostra_pessoas_e_veiculos_so_para_quem_pode(self):
        cliente, _ = self.entrar("porteiro1")
        html = cliente.get("/").get_data(as_text=True)
        self.assertIn('href="/pessoas/"', html)
        self.assertIn('href="/veiculos/"', html)
        cliente, _ = self.entrar("gerente1")
        html = cliente.get("/").get_data(as_text=True)
        self.assertNotIn('href="/pessoas/"', html)
        self.assertNotIn('href="/veiculos/"', html)

    def test_cadastro_pela_tela_cria_a_pessoa(self):
        cliente, _ = self.entrar("porteiro1")
        resposta = self.enviar(cliente, "/pessoas/nova", dados_pessoa())
        self.assertEqual(resposta.status_code, 302)
        html = cliente.get("/pessoas/").get_data(as_text=True)
        self.assertIn("Pessoa cadastrada com sucesso", html)
        self.assertIn("Maria da Silva", html)
        self.assertIn("111.444.777-35", html)

    def test_cpf_duplicado_pela_tela_mostra_erro_e_mantem_o_formulario(self):
        self.criar_pessoa()
        cliente, _ = self.entrar("porteiro1")
        resposta = self.enviar(cliente, "/pessoas/nova", dados_pessoa(nome="Carlos Duplicado"))
        self.assertEqual(resposta.status_code, 200)
        html = resposta.get_data(as_text=True)
        self.assertIn("Já existe uma pessoa com este CPF", html)
        self.assertIn("Carlos Duplicado", html)                  # mantém o que foi digitado
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM pessoa")[0]["n"], 1)

    def test_editar_pessoa_pela_tela(self):
        pessoa_id = self.criar_pessoa()
        cliente, _ = self.entrar("admin")
        html = cliente.get(f"/pessoas/{pessoa_id}/editar").get_data(as_text=True)
        self.assertIn("Maria da Silva", html)
        resposta = self.enviar(cliente, f"/pessoas/{pessoa_id}/editar",
                               dados_pessoa(nome="Maria Souza"))
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(self.consultar("SELECT nome FROM pessoa")[0]["nome"], "Maria Souza")

    def test_pessoa_inexistente_da_404(self):
        cliente, _ = self.entrar("admin")
        self.assertEqual(cliente.get("/pessoas/999/editar").status_code, 404)
        self.assertEqual(cliente.get("/veiculos/999/editar").status_code, 404)

    def test_desativar_pessoa_pela_tela(self):
        pessoa_id = self.criar_pessoa()
        cliente, _ = self.entrar("porteiro1")
        self.enviar(cliente, f"/pessoas/{pessoa_id}/alternar")
        self.assertEqual(self.consultar("SELECT ativo FROM pessoa")[0]["ativo"], 0)
        self.enviar(cliente, f"/pessoas/{pessoa_id}/alternar")
        self.assertEqual(self.consultar("SELECT ativo FROM pessoa")[0]["ativo"], 1)

    def test_busca_pela_tela(self):
        self.criar_pessoa()
        self.criar_pessoa(nome="João Pereira", cpf=CPF_2)
        cliente, _ = self.entrar("porteiro1")
        html = cliente.get("/pessoas/?busca=jo%C3%A3o").get_data(as_text=True)
        self.assertIn("João Pereira", html)
        self.assertNotIn("Maria da Silva", html)
        html = cliente.get("/pessoas/?busca=zzzz").get_data(as_text=True)
        self.assertIn("Nenhuma pessoa encontrada", html)

    def test_cadastro_de_veiculo_pela_tela(self):
        dono = self.criar_pessoa()
        cliente, _ = self.entrar("porteiro1")
        form = cliente.get("/veiculos/novo").get_data(as_text=True)
        self.assertIn("Maria da Silva", form)                    # proprietário aparece na lista
        dados = {"placa": "abc-1234", "modelo": "Gol", "cor": "Prata", "pessoa_id": str(dono)}
        self.assertEqual(self.enviar(cliente, "/veiculos/novo", dados).status_code, 302)
        html = cliente.get("/veiculos/").get_data(as_text=True)
        self.assertIn("Veículo cadastrado com sucesso", html)
        self.assertIn("ABC-1234", html)
        resposta = self.enviar(cliente, "/veiculos/novo", dict(dados, placa="ABC1234"))
        self.assertIn("Já existe um veículo com esta placa", resposta.get_data(as_text=True))
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM veiculo")[0]["n"], 1)

    def test_veiculo_com_proprietario_inexistente_pela_tela(self):
        cliente, _ = self.entrar("porteiro1")
        dados = {"placa": "ABC1234", "modelo": "Gol", "cor": "Prata", "pessoa_id": "999"}
        resposta = self.enviar(cliente, "/veiculos/novo", dados)
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Proprietário não encontrado", resposta.get_data(as_text=True))

    def test_editar_e_desativar_veiculo_pela_tela(self):
        dono = self.criar_pessoa()
        veiculo_id = self.criar_veiculo(dono)
        cliente, _ = self.entrar("admin")
        html = cliente.get(f"/veiculos/{veiculo_id}/editar").get_data(as_text=True)
        self.assertIn("ABC-1234", html)
        dados = {"placa": "ABC-1234", "modelo": "Gol G5", "cor": "Azul", "pessoa_id": str(dono)}
        self.assertEqual(self.enviar(cliente, f"/veiculos/{veiculo_id}/editar", dados).status_code, 302)
        self.assertEqual(self.consultar("SELECT modelo FROM veiculo")[0]["modelo"], "Gol G5")
        self.enviar(cliente, f"/veiculos/{veiculo_id}/alternar")
        self.assertEqual(self.consultar("SELECT ativo FROM veiculo")[0]["ativo"], 0)

    def test_post_sem_token_csrf_e_recusado(self):
        cliente, _ = self.entrar("porteiro1")
        resposta = cliente.post("/pessoas/nova", data=dados_pessoa())
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.consultar("SELECT COUNT(*) AS n FROM pessoa")[0]["n"], 0)

    def test_pessoa_cadastrada_aparece_na_lista_de_vinculo_de_usuario(self):
        self.criar_pessoa()
        cliente, _ = self.entrar("admin")
        html = cliente.get("/usuarios/novo").get_data(as_text=True)
        self.assertIn("Maria da Silva", html)


if __name__ == "__main__":
    unittest.main()
