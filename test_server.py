# Script de teste na porta 8090
from app import create_app
import logging

# Configurar logging para debug
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

# Configurar loggers específicos
auth_logger = logging.getLogger('auth_debug')
auth_logger.setLevel(logging.DEBUG)

app_logger = logging.getLogger('blog_app_init')
app_logger.setLevel(logging.DEBUG)

print("=== INICIANDO SERVIDOR DE TESTE SSL COM LOGGING DETALHADO ===")
app = create_app()

if __name__ == "__main__":
    print("Iniciando servidor de teste na porta 8090...")
    app.run(debug=True, port=8090, use_reloader=False) 