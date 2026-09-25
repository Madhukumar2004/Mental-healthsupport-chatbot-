import uuid
from flask import Flask, render_template, request, jsonify
from chatbot import get_chatbot_response, detect_mood
import database

app = Flask(__name__)

# Initialize database schema and tables on application startup
database.init_db()


@app.route("/", methods=["GET"])
def index():
    """
    GET /
    Opens the main MindCare chatbot page.
    """
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
@app.route("/api/chat", methods=["POST"])
def chat():
    """
    POST /chat (and POST /api/chat)
    - Receives user's message.
    - Validates for empty messages or invalid request formats.
    - Sends message to chatbot logic.
    - Detects the mood.
    - Saves conversation turn (user_message, bot_response, mood) to SQLite database.
    - Returns bot response and mood as JSON.
    """
    # 1. Validate request format
    if not request.is_json and not request.form:
        return jsonify({
            "error": "Invalid request format. Request body must be JSON."
        }), 400

    data = request.get_json(silent=True)
    if data is None and not request.form:
        return jsonify({
            "error": "Invalid or malformed JSON payload."
        }), 400

    payload = data if isinstance(data, dict) else request.form

    # 2. Extract and validate user message
    user_message = (
        payload.get("message")
        or payload.get("user_message")
        or payload.get("text")
        or ""
    )

    if not isinstance(user_message, str) or not user_message.strip():
        return jsonify({
            "error": "Message cannot be empty."
        }), 400

    clean_message = user_message.strip()
    session_id = payload.get("session_id") or str(uuid.uuid4())

    # 3. Send to chatbot logic & detect mood
    bot_result = get_chatbot_response(clean_message)
    detected_mood = bot_result.get("mood") or detect_mood(clean_message)
    response_text = bot_result["response"]

    # 4. Save conversation turn to SQLite chat_history table
    database.save_chat(
        user_message=clean_message,
        bot_response=response_text,
        mood=detected_mood
    )

    # Also persist to session message store for multi-turn web session support
    database.save_message(
        session_id=session_id,
        sender="user",
        message=clean_message
    )
    database.save_message(
        session_id=session_id,
        sender="bot",
        message=response_text,
        intent=bot_result.get("intent"),
        is_crisis=bot_result.get("is_crisis", False)
    )

    # 5. Return bot response and mood as JSON
    return jsonify({
        "response": response_text,
        "bot_response": response_text,
        "mood": detected_mood,
        "intent": bot_result.get("intent", "unknown"),
        "is_crisis": bot_result.get("is_crisis", False),
        "suggested_actions": bot_result.get("suggested_actions", []),
        "session_id": session_id,
    }), 200


@app.route("/history", methods=["GET"])
def get_chat_history():
    """
    GET /history
    Returns previous chat history from the SQLite database.
    Supports ?limit=<int> and ?format=dict query parameters.
    """
    limit = request.args.get("limit", default=100, type=int)
    history_records = database.retrieve_chat_history(limit=limit)
    # Support dictionary wrapper if explicitly requested via query parameter
    if request.args.get("format") == "dict":
        return jsonify({
            "status": "success",
            "count": len(history_records),
            "history": history_records
        }), 200
    return jsonify(history_records), 200


@app.route("/api/history", methods=["GET"])
@app.route("/api/history/<session_id>", methods=["GET"])
def api_session_history(session_id=None):
    """Returns conversation history for web UI."""
    limit = request.args.get("limit", default=100, type=int)
    if session_id:
        chat_history = database.get_chat_history(session_id, limit=limit)
        return jsonify({
            "session_id": session_id,
            "history": chat_history
        }), 200
    history_records = database.retrieve_chat_history(limit=limit)
    return jsonify({
        "status": "success",
        "count": len(history_records),
        "history": history_records
    }), 200


@app.route("/clear", methods=["DELETE", "POST"])
@app.route("/api/clear", methods=["DELETE", "POST"])
def clear_all_history():
    """
    DELETE /clear (also supports POST for browser forms)
    Deletes all chat history from SQLite.
    """
    deleted_count = database.clear_chat_history()

    # Clear session store and mood logs
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    if session_id:
        database.clear_history(session_id)
    else:
        database.clear_history()

    return jsonify({
        "status": "success",
        "message": "All chat history deleted successfully.",
        "deleted_count": deleted_count
    }), 200


@app.route("/api/mood", methods=["POST"])
def record_mood():
    """Logs the user's current mood check-in."""
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id") or str(uuid.uuid4())
    mood = data.get("mood", "").strip()
    note = data.get("note", "").strip() or None

    if not mood:
        return jsonify({"error": "Mood must be specified."}), 400

    database.save_mood(session_id, mood, note)
    return jsonify({
        "status": "success",
        "message": f"Recorded mood: {mood}"
    }), 200


@app.route("/api/mood/<session_id>", methods=["GET"])
def get_moods(session_id):
    """Returns recent mood history for the session."""
    moods = database.get_mood_logs(session_id)
    return jsonify({
        "session_id": session_id,
        "moods": moods
    }), 200


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "MindCare Mental Health Support Chatbot"
    }), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
