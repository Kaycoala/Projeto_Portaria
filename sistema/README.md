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
