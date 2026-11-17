# 🏢 Sistema de Controle de Portaria

**Organização, segurança e rastreabilidade no controle de acessos.**

Projeto acadêmico desenvolvido para a disciplina de **Análise e Projeto de Sistemas** (Ciência da Computação), com o objetivo de organizar e facilitar o controle de entrada e saída de pessoas e veículos em uma portaria.

<p align="center">
  <img src="https://img.shields.io/badge/Status-Est%C3%A1vel-brightgreen" alt="Status: Estável">
  <img src="https://img.shields.io/badge/Vers%C3%A3o-1.0.0-green" alt="Versão 1.0.0">
  <img src="https://img.shields.io/badge/Testes-262%20aprovados-brightgreen" alt="262 testes aprovados">
  <img src="https://img.shields.io/badge/Python-Flask-informational" alt="Python e Flask">
  <img src="https://img.shields.io/badge/Banco-SQLite-lightgrey" alt="SQLite">
  <img src="https://img.shields.io/badge/Documenta%C3%A7%C3%A3o-UML-blue" alt="Documentação UML">
</p>

**Integrantes:** Kayque da Silva Cremonini · Felipe Rafael Dias Delfante

---

## 📑 Índice

- [Sobre o projeto](#-sobre-o-projeto)
- [Objetivos](#-objetivos)
- [Funcionalidades](#-funcionalidades)
- [Perfis de usuário](#-perfis-de-usuário)
- [Diagramas UML](#-diagramas-uml)
- [Documentação](#-documentação)
- [Demonstração do sistema](#-demonstração-do-sistema)
- [Como executar](#-como-executar)
- [Requisitos não funcionais](#-requisitos-não-funcionais)
- [Regras de negócio](#-regras-de-negócio)
- [Limitações conhecidas](#-limitações-conhecidas)
- [Andamento do projeto](#-andamento-do-projeto)
- [Estrutura do repositório](#-estrutura-do-repositório)
- [Sobre o projeto acadêmico](#-sobre-o-projeto-acadêmico)

---

## 📌 Sobre o projeto

O **Sistema de Controle de Portaria** organiza o registro e o acompanhamento da entrada e saída de pessoas e veículos em um ambiente controlado, como um condomínio ou uma empresa.

É uma aplicação web usada pelo navegador, escrita em **Python com Flask**, que guarda os dados em um banco **SQLite**. Ela centraliza o cadastro de pessoas e veículos, a solicitação e a decisão de autorização de visitantes, o registro de entradas e saídas, as ocorrências, o histórico de acessos e os relatórios. Cada usuário enxerga apenas o que o seu perfil permite.

> **Status atual:** versão **1.0.0** (primeira versão estável). Os requisitos funcionais RF-01 a RF-10 estão implementados (o RF-06 com uma ressalva e o RF-07 de forma parcial, descritas em [Limitações conhecidas](#-limitações-conhecidas)) e o sistema é coberto por **262 testes automatizados**. Veja o [CHANGELOG](CHANGELOG.md).

## 🎯 Objetivos

- Melhorar o controle de acesso de pessoas e veículos.
- Registrar entradas, saídas e ocorrências, com data e hora automáticas.
- Organizar os dados de moradores, funcionários, prestadores e visitantes.
- Registrar a autorização de visitantes (autorizar com período ou negar) e impedir a entrada sem autorização válida.
- Facilitar a consulta ao histórico de acessos.
- Gerar relatórios de movimentação por período, com exportação em CSV.

## ⚙️ Funcionalidades

| Código | Funcionalidade | Situação | Onde fica no sistema |
|:---:|---|:---:|---|
| RF-01 | Cadastro de moradores, funcionários e prestadores | ✅ Implementado | Menu **Pessoas** |
| RF-02 | Cadastro de veículos | ✅ Implementado | Menu **Veículos** |
| RF-03 | Entrada de pessoas, visitantes e veículos | ✅ Implementado | Menu **Entrada e saída** |
| RF-04 | Saída | ✅ Implementado | Menu **Entrada e saída** |
| RF-05 | Cadastro de visitantes (já abre a solicitação de autorização) | ✅ Implementado | Menu **Visitantes** |
| RF-06 | Autorização de visitantes | ⚠️ Implementado com ressalva | Menu **Autorizações** |
| RF-07 | Entrada e saída de veículos | ⚠️ Parcial (só veículos de pessoas cadastradas) | Menu **Entrada e saída** |
| RF-08 | Histórico de acessos | ✅ Implementado | Menu **Histórico** |
| RF-09 | Registro de ocorrências | ✅ Implementado | Menu **Ocorrências** |
| RF-10 | Relatórios de acessos | ✅ Implementado | Menu **Relatórios** (tela, CSV e impressão) |

Além disso, a página inicial tem um **painel (dashboard)** com os números atuais da portaria, lidos do banco de dados.
O passo a passo de uso de cada tela está no [README do sistema](sistema/README.md).

## 👥 Perfis de usuário

| Perfil | O que pode fazer |
|---|---|
| **Administrador** | Tudo: gerencia usuários, gera relatórios, faz backup e é o único que corrige a observação de um acesso e exclui (logicamente) acessos e ocorrências. |
| **Porteiro** | Cadastra pessoas, veículos e visitantes, registra entradas, saídas e ocorrências, consulta o histórico e vê o painel. |
| **Aprovador (Gerente)** | Autoriza (com período) ou nega visitantes, consulta o histórico e vê o painel. |
| **Funcionário** | Consegue entrar no sistema, mas não tem operações. |

O **visitante** não é usuário do sistema: é um cadastro feito pelo porteiro, sem login.

## 📐 Diagramas UML

Os diagramas foram revisados para refletir o sistema como ele foi implementado.

### Diagrama de Casos de Uso

Mostra a fronteira do sistema, os atores (Funcionário, Porteiro, Aprovador e Administrador), os relacionamentos *include* e *extend* e a generalização do Administrador, que herda o que o Porteiro e o Aprovador fazem.

- 🖼️ [Visualizar diagrama de casos de uso (JPG)](diagramas/Diagrama_Casos_de_Uso_Portaria.jpg)

### Diagrama de Classes

Está em nível de projeto: atributos privados com tipo, operações públicas com parâmetros e retorno, multiplicidade em todas as associações e enumerações (`TipoPessoa`, `StatusAutorizacao` e `TipoAcesso`).

- 🖼️ [Visualizar diagrama de classes (JPG)](diagramas/Diagrama_de_Classes_Portaria.jpg)
- ✏️ [Código-fonte do diagrama (Graphviz)](diagramas/Diagrama_de_Classes_Portaria.dot)

A ligação entre cada classe e as tabelas do banco está em [Correspondência com a modelagem](documentacao/Correspondencia_Modelagem.md).

## 📚 Documentação

| Documento | Descrição | Acesso |
|---|---|---|
| **Documentação completa (PDF)** | Descrição do sistema, requisitos, casos de uso (com fluxos principal, alternativos e de exceção), diagrama de classes, repositório e verificação. | [Abrir PDF](documentacao/Documentacao_Sistema_Controle_de_Portaria.pdf) |
| Requisitos do sistema | Requisitos funcionais, não funcionais e regras de negócio (texto original). | [Abrir DOCX](documentacao/requisitos%20do%20sistema.docx) |
| Casos de uso textuais | UC01 Registrar entrada, UC02 Autorizar visitante e UC03 Consultar histórico. | [Abrir PDF](documentacao/Casos_de_Uso_Sistema_Controle_de_Portaria.pdf) |
| Correspondência com a modelagem | Como cada classe do diagrama virou tabela no banco de dados. | [Abrir](documentacao/Correspondencia_Modelagem.md) |
| Manual do sistema | Como instalar, executar, testar e usar cada tela. | [README do sistema](sistema/README.md) |
| Histórico de versões | O que foi feito em cada versão. | [CHANGELOG](CHANGELOG.md) |

## 🎥 Demonstração do sistema

O vídeo tem menos de um minuto e mostra o sistema funcionando: painel, cadastros, visitantes e autorizações, entrada e saída, histórico e relatórios.

▶️ [**Assistir ao vídeo de demonstração (MP4)**](video/demonstracao.mp4)

O roteiro de gravação está em [video/ROTEIRO.md](video/ROTEIRO.md).

## 🚀 Como executar

Requisito: Python 3.10 ou superior. No Windows:

```
cd sistema
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe criar_admin.py
venv\Scripts\python.exe run.py
```

Abra http://127.0.0.1:5000 e entre com o administrador criado. Para conhecer o sistema com dados fictícios (porteiro, gerente, pessoas, veículos, visitantes e movimentações), rode também `venv\Scripts\python.exe popular_demo.py` antes do `run.py`.

Para rodar os testes automatizados (262 testes):

```
venv\Scripts\python.exe -m unittest discover tests -v
```

## 🛡️ Requisitos não funcionais

| Código | Requisito | Situação |
|:---:|---|---|
| RNF-01 | Consultas e registros respondem em até 2 segundos | ✅ Medido com 30.000 acessos no banco: maior tempo de 0,56 s (relatório de 366 dias). Índices no banco, limite de 200 linhas no histórico e relatórios de no máximo 366 dias. |
| RNF-02 | Autenticação por usuário e senha | ✅ Todas as telas, exceto o login, exigem sessão; senhas guardadas com hash (pbkdf2:sha256); formulários protegidos contra CSRF. |
| RNF-03 | Disponibilidade durante o funcionamento da portaria | ⚠️ Não comprovável pelo código: depende do computador onde o sistema roda. O sistema é leve (Flask + SQLite), roda em um único computador e não depende de servidor de banco externo. |
| RNF-04 | Acesso conforme o perfil | ✅ Permissões centralizadas em `sistema/app/permissoes.py`; páginas proibidas respondem com erro 403 e o menu mostra só o permitido. |
| RNF-05 | Backup a cada 24 horas | ⚠️ Parcial: script `sistema/backup.py` e tela **Backup** (administrador); o painel avisa quando o último backup passa de 24 horas. O agendamento diário é feito no Agendador de Tarefas do Windows (veja o [README do sistema](sistema/README.md)). |

## 📏 Regras de negócio

| Código | Regra | Como foi atendida |
|:---:|---|---|
| RN-01 | Cadastro obrigatório | Só pessoas cadastradas e ativas podem ter a entrada registrada. |
| RN-02 | Registro de entrada com data e hora | Data e hora são gravadas automaticamente pelo sistema. |
| RN-03 | Visitante autorizado | A entrada do visitante só é liberada com autorização aprovada e vigente na data. O porteiro não libera por conta própria. |
| RN-04 | Registro de saída | Quem está dentro aparece em **Dentro agora** até a saída ser registrada (o sistema não alerta sobre saída esquecida). |
| RN-05 | Acesso restrito para alterar ou excluir | Só o administrador corrige a observação de acessos e exclui acessos e ocorrências. |
| RN-06 | CPF único | Verificado na validação e garantido no banco (`UNIQUE`). O CPF de visitante não é único. |
| RN-07 | Placa única | Verificado na validação e garantido no banco (`UNIQUE`). |
| RN-08 | Histórico preservado | Exclusão lógica: o registro continua guardado e visível ao administrador. |
| RN-09 | Visitante sem autorização aguarda | Toda solicitação começa "aguardando autorização" e é bloqueada na portaria até a decisão. |
| RN-10 | Ocorrência com data, hora e descrição | Campos obrigatórios na tela e no banco. |

## ⚠️ Limitações conhecidas

- **RF-06 / RN-03:** quem decide a autorização é o Aprovador (ou o Administrador); não há vínculo entre a pessoa visitada e quem decide, e o porteiro não pode liberar um visitante sozinho.
- **RF-07:** não há veículo de visitante; todo veículo precisa de uma pessoa cadastrada como proprietária.
- **RN-06:** o CPF exige 11 números, mas os dígitos verificadores não são conferidos.
- **RNF-03 e RNF-05:** dependem do ambiente de uso (execução contínua e agendamento do backup).
- O visitante não acessa o sistema, e não há troca de senha pelo próprio usuário (o administrador redefine a senha).

## 📈 Andamento do projeto

- [x] 0.1.0 — Estrutura inicial
- [x] 0.2.0 — Banco de dados
- [x] 0.3.0 — Autenticação e usuários
- [x] 0.4.0 — Pessoas e veículos
- [x] 0.5.0 — Visitantes e autorizações
- [x] 0.6.0 — Entrada e saída
- [x] 0.7.0 — Histórico e ocorrências
- [x] 0.8.0 — Dashboard e relatórios
- [x] 0.9.0 — Backup e interface
- [x] 1.0.0 — Primeira versão estável (testes gerais, correções finais e documentação)
  - [x] Entrega: PDF final e vídeo de demonstração
  - [ ] Prints reais do sistema (opcional; roteiro em [documentacao/prints](documentacao/prints/README.md))

O detalhe de cada versão está no [CHANGELOG](CHANGELOG.md) e nos commits do repositório.

## 🗂️ Estrutura do repositório

```
Projeto_Portaria/
├── README.md              ← este arquivo
├── CHANGELOG.md           ← histórico de versões
├── .gitignore             ← impede o envio do banco e da chave secreta
├── diagramas/             ← diagramas UML (JPG) e código-fonte do diagrama de classes
├── documentacao/          ← PDF final, requisitos, casos de uso e correspondência com a modelagem
├── video/                 ← vídeo de demonstração (MP4) e roteiro
└── sistema/               ← código-fonte
    ├── app/
    │   ├── routes/        ← telas e ações de cada módulo
    │   ├── services/      ← regras de negócio e validações
    │   ├── templates/     ← páginas HTML
    │   ├── static/        ← CSS e JavaScript
    │   ├── auth.py        ← login e proteção das páginas
    │   └── permissoes.py  ← o que cada perfil pode fazer
    ├── banco/             ← schema.sql e dados iniciais
    ├── tests/             ← testes automatizados (unittest)
    ├── backup.py          ← cópia de segurança do banco
    ├── criar_admin.py
    ├── criar_banco.py
    ├── popular_demo.py    ← dados fictícios para demonstração
    └── run.py
```

## 🎓 Sobre o projeto acadêmico

Projeto desenvolvido em dupla para a disciplina de **Análise e Projeto de Sistemas**, percorrendo as etapas de levantamento de requisitos, modelagem UML, implementação e testes, com a evolução de cada versão registrada no GitHub.
