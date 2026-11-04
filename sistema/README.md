# Código-fonte — Sistema de Controle de Portaria

## Como executar (Windows)

Requisito: Python 3.10 ou superior.

```
cd sistema
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Abra http://127.0.0.1:5000 no navegador.

## Estrutura

- `app/routes/`: telas e ações de cada módulo
- `app/services/`: regras de negócio e validações
- `app/templates/`: páginas HTML
- `app/static/`: CSS e JavaScript
- `run.py`: inicia o sistema

## Banco de dados

O banco é um arquivo SQLite (`instance/portaria.db`), criado a partir de `banco/schema.sql`.
Na primeira execução do sistema ele é criado automaticamente. Também é possível criar manualmente:

```
venv\Scripts\python.exe criar_banco.py             (cria, sem apagar dados)
venv\Scripts\python.exe criar_banco.py --recriar   (APAGA tudo e cria de novo)
```

Tabelas: `perfil`, `pessoa`, `usuario`, `veiculo`, `visitante`, `autorizacao`,
`registro_acesso`, `ocorrencia`, `ocorrencia_pessoa`.

## Testes

```
venv\Scripts\python.exe -m unittest discover tests -v
```

## Primeiro acesso (login)

O sistema exige login. Antes de entrar pela primeira vez, crie o administrador:

```
venv\Scripts\python.exe criar_admin.py
```

O script pergunta o login e a senha (mínimo de 6 caracteres). Depois rode
`venv\Scripts\python.exe run.py` e entre em http://127.0.0.1:5000.

O administrador cadastra os demais usuários no menu **Usuários**.

## Cadastro de pessoas e veículos

No menu lateral, **Pessoas** e **Veículos** (administrador e porteiro):

- Cadastre primeiro a pessoa e depois o veículo, escolhendo o proprietário.
- O CPF e a placa não podem se repetir. O CPF pode ser digitado com ou sem pontos e traço;
  a placa aceita `ABC-1234` e `ABC1D23` (maiúsculas ou minúsculas).
- Use a caixa de busca para achar pessoas (nome ou CPF) e veículos (placa, modelo ou proprietário).
- Cadastros não são apagados: use **Desativar**, para que o histórico de acessos seja preservado.

## Visitantes e autorizações

- **Porteiro:** menu **Visitantes** > *Novo visitante*. A solicitação fica "aguardando autorização".
- **Aprovador (gerente):** menu **Autorizações** > *Analisar*. Escolha **Autorizar** (com a data inicial
  e, se quiser, a data final) ou **Negar**. A decisão fica registrada e não pode ser desfeita.
- Se o visitante voltar outro dia, o porteiro usa **Nova solicitação** na lista de visitantes.
- A autorização é conferida na hora da entrada (veja a seção abaixo).

## Entrada e saída

No menu **Entrada e saída** (porteiro e administrador):

- Escolha a pessoa, o visitante ou o veículo e clique em **Registrar entrada**. A data e a hora são gravadas automaticamente.
- **Visitante:** só entra com autorização válida para hoje. Se estiver aguardando, negada, ainda sem data
  de início ou vencida, o sistema bloqueia e explica o motivo.
- Quem já está dentro aparece na tabela **Dentro agora**; use **Registrar saída** quando sair.
- Os registros nunca são apagados, a saída só completa o horário.

## Perfis e permissões

| Perfil | O que pode fazer (nesta versão e nas próximas) |
|---|---|
| Administrador | Tudo: usuários, cadastros, acessos, autorizações, ocorrências, relatórios |
| Porteiro | Cadastros, visitantes, entradas e saídas, histórico e ocorrências |
| Aprovador (Gerente) | Autorizar/negar visitantes e consultar o histórico |
| Funcionário | Apenas entra no sistema (sem operações) |

As regras ficam em `app/permissoes.py`.
