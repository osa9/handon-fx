import json
import traceback
import base64

from handon_fx.chat.mastodon_api import handle_push_notification


def push_notification(event, _context):
    try:
        handle_push_notification(
            base64.b64decode(event["body"]),
            event["headers"].get("encryption"),
            event["headers"].get("crypto-key"),
        )
        response = {"statusCode": 200, "body": json.dumps({"ok": True})}
        return response
    except Exception as ex:
        print("Unknown error")
        print(ex)
        print(traceback.format_exc())
        response = {"statusCode": 200, "body": json.dumps({"ok": False})}
        return response


def test(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps({"event": "test"}),
    }
