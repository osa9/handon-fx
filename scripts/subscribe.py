import base64
import json
from mastodon import Mastodon
from dotenv import load_dotenv
import sys
import os

load_dotenv()


def set_endpoint(access_token, instance, endpoint):
    mastodon = Mastodon(access_token=access_token, api_base_url=instance)

    pub_key = json.load(open("keys/pubkey"))
    pub_key["pubkey"] = base64.b64decode(pub_key["pubkey"])
    pub_key["auth"] = base64.b64decode(pub_key["auth"])
    print(pub_key)
    res = mastodon.push_subscription_set(endpoint, pub_key, mention_events=True)
    print(res)


set_endpoint(os.getenv("ACCESS_TOKEN"), os.getenv("MASTODON_SERVER"), sys.argv[1])
