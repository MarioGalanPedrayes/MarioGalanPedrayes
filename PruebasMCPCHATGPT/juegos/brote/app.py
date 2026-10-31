"""Servidor web de BROTE."""
import os
from flask import Flask, jsonify, render_template, request, session
from game import new_game, perform_action, snapshot

app = Flask(__name__)
app.secret_key = os.environ.get("BROTE_SECRET_KEY", "brote-local-dev-key-change-me")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


def current_game():
    if "game" not in session:
        session["game"] = new_game()
    return session["game"]


@app.get("/")
def index():
    current_game()
    return render_template("index.html")


@app.get("/api/state")
def state():
    return jsonify(snapshot(current_game()))


@app.post("/api/action")
def action():
    payload = request.get_json(silent=True) or {}
    game = current_game()
    try:
        updated = perform_action(game, payload.get("action", ""), payload.get("data", {}))
        session["game"] = updated
        session.modified = True
        return jsonify({"ok": True, "state": updated})
    except (ValueError, TypeError) as exc:
        return jsonify({"ok": False, "error": str(exc), "state": snapshot(game)}), 400


@app.post("/api/reset")
def reset():
    session["game"] = new_game()
    session.modified = True
    return jsonify({"ok": True, "state": snapshot(session["game"])})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
