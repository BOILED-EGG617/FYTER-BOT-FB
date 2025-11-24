# fb_group_bot.py
# Simple, safe Facebook Group helper template
# Credit: Script edited by RAVI KING
# IMPORTANT: This is a template. Read README.md before using. Do NOT use for spam/abuse.

import os
import time
import logging
from dotenv import load_dotenv
from flask import Flask, request, jsonify, abort
import requests

# Load .env
load_dotenv()

# Config
GRAPH_API_BASE = os.getenv("GRAPH_API_BASE", "https://graph.facebook.com/v17.0")
GROUP_ID = os.getenv("FB_GROUP_ID")
ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
ADMIN_FACEBOOK_ID = os.getenv("ADMIN_FACEBOOK_ID")
FB_VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN")
ADMIN_COMMAND_SECRET = os.getenv("ADMIN_COMMAND_SECRET", "change-me")
CREDIT_LINE = "Script edited by RAVI KING"

# Basic validation of required config
if not all([GROUP_ID, ACCESS_TOKEN, ADMIN_FACEBOOK_ID, FB_VERIFY_TOKEN]):
    logging.warning("One or more required environment variables are not set. See .env.example")

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


def is_admin(sender_id: str) -> bool:
    return str(sender_id) == str(ADMIN_FACEBOOK_ID)


def post_message_to_group(message: str) -> dict:
    """
    Post a message to the group using Graph API.
    Requires proper token and permissions. May fail if permissions are not granted.
    """
    url = f"{GRAPH_API_BASE}/{GROUP_ID}/feed"
    params = {
        "message": f"{message}\n\n{CREDIT_LINE}",
        "access_token": ACCESS_TOKEN
    }
    resp = requests.post(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """
    Verification endpoint for FB webhook setup.
    When adding webhook in FB App dashboard, FB will call this with hub.verify_token and hub.challenge.
    """
    verify_token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    mode = request.args.get("hub.mode")
    if verify_token == FB_VERIFY_TOKEN and mode == "subscribe":
        return challenge, 200
    return "Verification token mismatch", 403


@app.route("/webhook", methods=["POST"])
def handle_webhook():
    """
    Basic webhook handler: logs events and shows how to detect mentions.
    Customize parsing to your subscription type. This handler WILL NOT auto-run admin commands:
    it only posts to group when the triggering user is the configured admin (per your requirement).
    """
    data = request.get_json(silent=True)
    logging.info("Webhook payload received: %s", data)

    if not data:
        return jsonify({"status": "no payload"}), 400

    # The actual structure depends on what webhook fields you subscribed to.
    # Inspect your webhook payloads in your app dashboard and adapt parsing.
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                # Example fields — you must adapt according to actual payload
                sender = value.get("from", {})
                sender_id = sender.get("id")
                message_text = value.get("message", "") or value.get("text", "")

                # If someone mentions the ADMIN_FACEBOOK_ID in a message:
                if sender_id and message_text and str(ADMIN_FACEBOOK_ID) in message_text:
                    logging.info("Detected mention of admin by %s", sender_id)
                    # Only respond automatically if the mention came from the admin themself
                    if is_admin(sender_id):
                        reply = f"Auto-reply triggered by admin. {CREDIT_LINE}"
                        try:
                            result = post_message_to_group(reply)
                            logging.info("Posted reply: %s", result)
                        except Exception as e:
                            logging.exception("Failed to post reply: %s", e)
                    else:
                        logging.info("Mention detected, but sender is not admin — no auto-action taken.")
    except Exception as exc:
        logging.exception("Error processing webhook payload: %s", exc)
        return jsonify({"status": "error", "detail": str(exc)}), 500

    return jsonify({"status": "ok"}), 200


@app.route("/command", methods=["POST"])
def command_endpoint():
    """
    Admin-only endpoint to issue commands to the bot.
    Protect this with ADMIN_COMMAND_SECRET and check admin id in payload.
    Expected JSON:
      {
        "admin_id": "<your_facebook_id>",
        "secret": "<ADMIN_COMMAND_SECRET>",
        "command": "post",
        "args": "Hello group"
      }
    Only the configured ADMIN_FACEBOOK_ID and the secret can perform actions.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "invalid json"}), 400

    # Basic secret check
    if data.get("secret") != ADMIN_COMMAND_SECRET:
        return jsonify({"error": "invalid secret"}), 403

    sender_id = data.get("admin_id")
    if not is_admin(sender_id):
        return jsonify({"error": "unauthorized admin id"}), 403

    command = (data.get("command") or "").strip().lower()
    args = data.get("args", "")

    if command == "post":
        if not args:
            return jsonify({"error": "no message provided"}), 400
        try:
            res = post_message_to_group(args)
            return jsonify({"status": "posted", "result": res}), 200
        except Exception as e:
            logging.exception("Failed to post message: %s", e)
            return jsonify({"error": "post_failed", "detail": str(e)}), 500
    elif command == "ping":
        return jsonify({"status": "pong", "credit": CREDIT_LINE}), 200
    else:
        return jsonify({"error": "unknown_command"}), 400


if __name__ == "__main__":
    # Development server. For production use gunicorn or a proper WSGI server.
    host = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_RUN_PORT", 5000))
    app.run(host=host, port=port, debug=(os.getenv("FLASK_ENV") != "production"))
