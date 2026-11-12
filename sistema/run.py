import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Modo de desenvolvimento (recarrega sozinho e mostra detalhes técnicos dos erros) só se pedido:
    #   Windows (PowerShell):  $env:PORTARIA_DEBUG = "1"
    # Por padrão fica desligado: na demonstração o usuário vê a página de erro amigável.
    app.run(debug=os.environ.get("PORTARIA_DEBUG") == "1")
