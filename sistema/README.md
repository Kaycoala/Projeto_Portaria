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
