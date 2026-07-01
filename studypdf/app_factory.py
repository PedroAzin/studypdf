import os
import secrets

from flask import Flask, render_template
from flask_wtf import CSRFProtect
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

from studypdf.db import check_database_connection, close_db, describe_database_target, init_db, validate_database_config
from studypdf.routes.books import books_bp
from studypdf.routes.main import main_bp
from studypdf.routes.notes import notes_bp
from studypdf.services.processing import start_processing_worker

ERROR_TEMPLATE = "error.html"
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.secret_key = os.environ.get("STUDYPDF_SIGNING_KEY") or secrets.token_hex(32)
    app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
    app.config["PROPAGATE_EXCEPTIONS"] = False

    csrf.init_app(app)
    validate_startup_config(app)
    register_lifecycle(app)
    register_routes(app)
    register_template_filters(app)
    register_error_handlers(app)
    start_processing_worker(app)
    return app


def validate_startup_config(app):
    validate_database_config()
    app.logger.info(
        "Verificando conexao com banco de dados: %s (timeout=%ss)",
        describe_database_target(),
        os.environ.get("STUDYPDF_DATABASE_CONNECT_TIMEOUT_SECONDS", "10"),
    )
    check_database_connection()
    app.logger.info("Conexao com banco de dados verificada.")


def register_lifecycle(app):
    app.teardown_appcontext(close_db)

    @app.before_request
    def ensure_db():
        init_db()


def register_routes(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(notes_bp)


def register_template_filters(app):
    @app.template_filter("json_tags")
    def json_tags(value):
        if not value:
            return "[]"
        return [tag.strip() for tag in value.split(",") if tag.strip()]


def register_error_handlers(app):
    @app.errorhandler(RequestEntityTooLarge)
    def handle_too_large(error):
        return render_template(
            ERROR_TEMPLATE,
            title="Arquivo muito grande",
            message="O PDF ultrapassa o limite de 100 MB.",
        ), 413

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return render_template(
            ERROR_TEMPLATE,
            title=f"Erro {error.code}",
            message=error.description,
        ), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.exception("Erro inesperado")
        return render_template(
            ERROR_TEMPLATE,
            title="Erro inesperado",
            message="Nao foi possivel concluir a operacao agora.",
        ), 500
