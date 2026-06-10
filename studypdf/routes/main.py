from flask import Blueprint, render_template, request

from studypdf.db import get_db

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    recent_books = get_db().execute(
        "SELECT * FROM books ORDER BY created_at DESC LIMIT 6"
    ).fetchall()
    return render_template("index.html", recent_books=recent_books)


@main_bp.route("/search")
def search():
    return render_template("search.html", query=request.args.get("q", "").strip())
