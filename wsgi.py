import os
from dotenv import load_dotenv
from flask import Flask

from routes.main import main_blueprint
from routes.admin import admin_blueprint
from routes.api import api_blueprint

load_dotenv()

FLASK_DEBUG = os.getenv("FLASK_DEBUG")
NODE_ENV = os.getenv("NODE_ENV")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads/")
PORT = int (
            os.getenv("PORT", "5000")
        )
MAX_CONTENT_LENGTH = 64 * 1024 * 1024

app = Flask(__name__, static_folder="static")

app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_DIR, exist_ok=True)

app.register_blueprint(main_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(api_blueprint)

if __name__ == "__main__":
    print(f"Flask running on {NODE_ENV} with DEBUG: {FLASK_DEBUG}")
    if NODE_ENV == "test":
        app.config["TEMPLATES_AUTO_RELOAD"] = True
        app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

        from livereload import Server

        server = Server(app.wsgi_app)

        server.watch("static/*.css")
        server.watch("static/*.js")
        server.watch("templates/*.html")

        server.serve(port=PORT, debug=True)
    elif NODE_ENV == "production":
        app.run(host="0.0.0.0", port=PORT)
