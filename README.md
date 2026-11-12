# 🏢 Sistema de Controle de Portaria

**Organização, segurança e rastreabilidade no controle de acessos.**

Projeto acadêmico desenvolvido para a disciplina de **Análise e Projeto de Sistemas**, com o objetivo de organizar e facilitar o controle de entrada e saída de pessoas e veículos.

<p align="center">
  <img src="https://img.shields.io/badge/Status-Em%20desenvolvimento-yellow" alt="Status: Em desenvolvimento">
  <img src="https://img.shields.io/badge/Documenta%C3%A7%C3%A3o-UML-blue" alt="Documentação UML">
  <img src="https://img.shields.io/badge/Projeto-Acad%C3%AAmico-purple" alt="Projeto acadêmico">
  <img src="https://img.shields.io/badge/Vers%C3%A3o-0.9.0-green" alt="Versão 0.9.0">
  <img src="https://img.shields.io/badge/Python-Flask-informational" alt="Python e Flask">
  <img src="https://img.shields.io/badge/Banco-SQLite-lightgrey" alt="SQLite">
</p>

---

## 📑 Índice

- [Sobre o projeto](#-sobre-o-projeto)
- [Objetivos](#-objetivos)
- [Funcionalidades](#-funcionalidades)
- [Diagramas UML](#-diagramas-uml)
- [Documentação](#-documentação)
- [Como executar](#-como-executar)
- [Demonstração do sistema](#-demonstração-do-sistema)
- [Requisitos não funcionais](#-requisitos-não-funcionais)
- [Regras de negócio](#-regras-de-negócio)
- [Andamento do projeto](#-andamento-do-projeto)
- [Estrutura do repositório](#-estrutura-do-repositório)
- [Sobre o projeto acadêmico](#-sobre-o-projeto-acadêmico)

---

## 📌 Sobre o projeto

O **Sistema de Controle de Portaria** tem como objetivo organizar o registro e o acompanhamento da entrada e saída de pessoas e veículos em um ambiente controlado.

A proposta é centralizar as informações da portaria, facilitar a identificação de visitantes, registrar movimentações e permitir consultas ao histórico de acessos.

Este repositório reúne a documentação, os diagramas UML e os demais materiais desenvolvidos durante o planejamento e a implementação do sistema.

> **Status atual:** versão **0.9.0**. Os requisitos funcionais RF-01 a RF-10 e o backup (RNF-05) estão implementados e cobertos por testes automatizados. A próxima versão é a entrega final, com prints, vídeo e PDF (1.0.0). Veja o [CHANGELOG](CHANGELOG.md).

## 🎯 Objetivos

- Melhorar o controle de acesso de pessoas e veículos.
- Registrar entradas, saídas e ocorrências.
- Organizar os dados de moradores, funcionários e visitantes.
- Permitir o registro de autorizações de visitantes.
- Facilitar a consulta ao histórico de acessos.
- Apoiar a geração de relatórios de movimentação.

## ⚙️ Funcionalidades

| Código | Funcionalidade | Situação | Onde fica no sistema |
|:---:|---|:---:|---|
| RF-01 | Cadastro de moradores e funcionários | ✅ Implementado e testado | Menu **Pessoas** |
| RF-02 | Cadastro de veículos | ✅ Implementado e testado | Menu **Veículos** |
| RF-03 | Entrada de pessoas | ✅ Implementado e testado | Menu **Entrada e saída** |
| RF-04 | Saída de pessoas | ✅ Implementado e testado | Menu **Entrada e saída** |
| RF-05 | Cadastro de visitantes | ✅ Implementado e testado | Menu **Visitantes** |
| RF-06 | Autorização de visitantes | ✅ Implementado e testado | Menu **Autorizações** |
| RF-07 | Entrada e saída de veículos | ✅ Implementado e testado | Menu **Entrada e saída** |
| RF-08 | Histórico de acessos | ✅ Implementado e testado | Menu **Histórico** |
| RF-09 | Registro de ocorrências | ✅ Implementado e testado | Menu **Ocorrências** |
| RF-10 | Relatórios de acessos | ✅ Implementado e testado | Menu **Relatórios** (tela, CSV e impressão) |

Além disso, a página inicial tem um **dashboard** com os números atuais da portaria, lidos do banco de dados.
O passo a passo de uso de cada tela está no [README do sistema](sistema/README.md).

## 📐 Diagramas UML

### Diagrama de Casos de Uso

Representa os atores envolvidos e suas interações com o Sistema de Controle de Portaria.

- 🖼️ [Visualizar diagrama de casos de uso (JPG)](diagramas/Diagrama_Casos_de_Uso_Portaria.jpg)
- ✏️ [Abrir arquivo editável (diagrams.net)](diagramas/Diagrama_Casos_de_Uso_Portaria.drawio)

### Diagrama de Classes

Representa as classes do sistema, seus atributos, métodos e relacionamentos.

- 🖼️ [Visualizar diagrama de classes (JPG)](diagramas/Diagrama_de_Classes_Portaria.jpg)
- ✏️ [Abrir arquivo editável (diagrams.net)](diagramas/Diagrama_de_Classes_Portaria.drawio)

Para editar os arquivos `.drawio`, utilize o [diagrams.net](https://app.diagrams.net/).

## 📚 Documentação

| Documento | Descrição | Acesso |
|---|---|---|
| Requisitos do sistema | Requisitos funcionais, não funcionais e regras de negócio. | [Abrir DOCX](documentacao/requisitos%20do%20sistema.docx) |
| Casos de uso textuais | UC01 Registrar entrada, UC02 Autorizar visitante e UC03 Consultar histórico. | [Abrir PDF](documentacao/Casos_de_Uso_Sistema_Controle_de_Portaria.pdf) |
| Manual do sistema | Como instalar, executar, testar e usar cada tela. | [README do sistema](sistema/README.md) |
| Histórico de versões | O que foi feito em cada versão. | [CHANGELOG](CHANGELOG.md) |
| Documentação completa em PDF | Documento consolidado com requisitos, modelagem e prints reais. | ⏳ Pendente (versão 1.0.0) |

## 🚀 Como executar

Requisito: Python 3.10 ou superior. No Windows:

```
cd sistema
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe criar_admin.py
venv\Scripts\python.exe run.py
```

Abra http://127.0.0.1:5000 e entre com o administrador criado. Para rodar os testes automatizados:

```
venv\Scripts\python.exe -m unittest discover tests -v
```

## 🎥 Demonstração do sistema

O vídeo terá **duração máxima de um minuto** e mostrará as principais funcionalidades funcionando.

⏳ **Pendente (versão 1.0.0).** Mais detalhes na [pasta do vídeo](video/README.md).

## 🛡️ Requisitos não funcionais

| Código | Requisito | Situação |
|:---:|---|---|
| RNF-01 | Tempo de resposta de até 2 segundos | Consultas com índices no banco, limite de 200 linhas no histórico e relatórios de no máximo 366 dias. |
| RNF-02 | Autenticação por usuário e senha | Todas as telas exigem login; senhas guardadas com hash; formulários protegidos. |
| RNF-03 | Disponibilidade durante o funcionamento da portaria | Sistema leve (Flask + SQLite) que roda em um único computador, sem depender de internet. |
| RNF-04 | Acesso conforme o perfil | Permissões centralizadas em `sistema/app/permissoes.py`; páginas proibidas respondem com erro 403 e o menu mostra só o permitido. |
| RNF-05 | Backup a cada 24 horas | Script `sistema/backup.py` e tela **Backup** (administrador); o painel avisa quando o último backup passa de 24 horas. O agendamento diário é feito no Agendador de Tarefas do Windows (veja o [README do sistema](sistema/README.md)). |

## 📏 Regras de negócio

| Código | Regra | Como foi atendida |
|:---:|---|---|
| RN-01 | Cadastro obrigatório | Só pessoas cadastradas e ativas podem ter a entrada registrada. |
| RN-02 | Registro de entrada com data e hora | Data e hora são gravadas automaticamente pelo sistema. |
| RN-03 | Visitante autorizado | A entrada do visitante só é liberada com autorização válida para o dia. |
| RN-04 | Registro de saída | Quem está dentro aparece em **Dentro agora** até a saída ser registrada. |
| RN-05 | Acesso restrito para alterar ou excluir | Só o administrador edita ou exclui acessos e ocorrências. |
| RN-06 | CPF único | Verificado na validação e garantido no banco (`UNIQUE`). |
| RN-07 | Placa única | Verificado na validação e garantido no banco (`UNIQUE`). |
| RN-08 | Histórico preservado | Exclusão lógica: o registro continua guardado e visível ao administrador. |
| RN-09 | Visitante sem autorização aguarda | Toda solicitação começa "aguardando autorização" e é bloqueada na portaria até a decisão. |
| RN-10 | Ocorrência com data, hora e descrição | Campos obrigatórios na tela e no banco. |

## 📈 Andamento do projeto

- [x] 0.1.0 — Estrutura inicial
- [x] 0.2.0 — Banco de dados
- [x] 0.3.0 — Autenticação e usuários
- [x] 0.4.0 — Pessoas e veículos
- [x] 0.5.0 — Visitantes e autorizações
- [x] 0.6.0 — Entrada e saída
- [x] 0.7.0 — Histórico e ocorrências
- [x] 0.8.0 — Dashboard e relatórios
- [x] 0.9.0 — Interface e melhorias
- [ ] 1.0.0 — Primeira versão estável (prints, vídeo e PDF final)

O detalhe de cada versão está no [CHANGELOG](CHANGELOG.md) e nos commits do repositório.

## 🗂️ Estrutura do repositório

```
Projeto_Portaria/
├── README.md              ← este arquivo
├── CHANGELOG.md           ← histórico de versões
├── .gitignore             ← impede o envio do banco e da chave secreta
├── diagramas/             ← diagramas UML (JPG e .drawio)
├── documentacao/          ← requisitos e casos de uso
├── video/                 ← vídeo de demonstração
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
    └── run.py
```

## 🎓 Sobre o projeto acadêmico

Projeto desenvolvido em dupla para a disciplina de **Análise e Projeto de Sistemas**, percorrendo as etapas de levantamento de requisitos, modelagem UML, implementação e testes, com a evolução de cada versão registrada no GitHub.
