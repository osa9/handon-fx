import base64
import json
from mastodon import Mastodon
import os
from dotenv import load_dotenv


load_dotenv()


def generate_key(access_token, instance):
    mastodon = Mastodon(access_token=access_token, api_base_url=instance)

    privkey, pubkey = mastodon.push_subscription_generate_keys()
    pubkey_b64 = {
        "pubkey": base64.b64encode(pubkey["pubkey"]).decode("utf-8"),
        "auth": base64.b64encode(pubkey["auth"]).decode("utf-8"),
    }

    privkey_b64 = {
        "privkey": privkey["privkey"],
        "auth": base64.b64encode(privkey["auth"]).decode("utf-8"),
    }

    json.dump(pubkey_b64, open("keys/pubkey", "w"))
    json.dump(privkey_b64, open("keys/privkey", "w"))
    print("Generated keys/pubkey and keys/privkey")


generate_key(os.getenv("ACCESS_TOKEN"), os.getenv("MASTODON_SERVER"))
