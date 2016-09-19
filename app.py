import os
import json
import requests

from dotenv import load_dotenv, find_dotenv
from flask import Flask, request

app = Flask(__name__)

load_dotenv(find_dotenv())


@app.route("/", methods=['GET'])
def verify():
    """
    Echo 'hub.challenge" so we can register app as webhook
    """
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Token mismatch", 403
        return request.args["hub.challenge"], 200
    return "Hello!", 200


@app.route("/", methods=['POST'])
def hook():
    """
    Receives all messages from Facebook bot
    """
    data = request.get_json()
    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                handle_messaging_event(messaging_event)


def handle_messaging_event(messaging_event):
    """
    Handle all events from bot (messages, delivery, optins, postbacks)
    :param messaging_event: event object
    """
    if messaging_event.get("postback"):
        # Here we handling payload which we setup by sending this request
        # curl - X POST - H "Content-Type: application/json" - d '{
        #     "setting_type":"call_to_actions",
        #     "thread_state":"new_thread",
        #     "call_to_actions":[
        #         {
        #             "payload": "GET_STARTED"
        #         }
        #     ]
        # }'
        if messaging_event["postback"]["payload"] == 'GET_STARTED':
            sender_id = messaging_event["sender"]["id"]
            profile = get_profile(sender_id)
            send_message(sender_id, "{}, what would you like to do tonight?".format(profile["first_name"]))


def get_profile(user_id):
    """
    Get profile of user by id
    :param user_id: user id
    """
    params = {
        'access_token': os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        'Content-type': 'application/json'
    }
    r = requests.get("https://graph.facebook.com/v2.7/{}".format(user_id), params=params, headers=headers)
    if r.status_code == 200:
        return json.loads(r.text)


def send_message(recipient_id, message):
    """
    Handle message sending
    :param recipient_id: who should receive message
    :param message: message text
    """
    params = {
        'access_token': os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        'Content-type': 'application/json'
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id,
        },
        "message": {
            "text": message,
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        raise Exception(r.text)


if __name__ == "__main__":
    app.run()
