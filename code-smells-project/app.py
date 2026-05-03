import logging
from flask import Flask
from flask_cors import CORS
from src.config.settings import SECRET_KEY, FLASK_DEBUG, PORT
from src.config.database import get_db
from src.views.routes import bp
from src.middlewares.error_handler import register_error_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
CORS(app)

app.register_blueprint(bp)
register_error_handlers(app)

if __name__ == "__main__":
    get_db()
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print(f"Rodando em http://localhost:{PORT}")
    print("=" * 50)
    app.run(host="0.0.0.0", port=PORT, debug=FLASK_DEBUG)
