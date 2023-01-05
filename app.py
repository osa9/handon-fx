from fastapi import FastAPI, Body, Header, Request
import dotenv
import os

# 手抜き
dotenv.load_dotenv()
os.environ["DYNAMODB_HOST"] = "http://localhost:4567"
os.environ["CHAT_TABLE"] = "Chat"
os.environ["TRADE_TABLE"] = "Trade"
os.environ["ACCOUNT_TABLE"] = "Account"
os.environ["TRADE_TABLE_ACCOUNT_STATE_INDEX"] = "Trade-account_state_index"

from handon_fx.chat.mastodon_api import handle_push_notification
from handon_fx.chat.models import ChatModel
from handon_fx.fx.models import TradeModel, AccountModel

if not ChatModel().exists():
    ChatModel.create_table(billing_mode="PAY_PER_REQUEST")
if not TradeModel().exists():
    TradeModel.create_table(billing_mode="PAY_PER_REQUEST")
if not AccountModel().exists():
    AccountModel.create_table(billing_mode="PAY_PER_REQUEST")

app = FastAPI()


@app.get("/")
def index():
    return {"message": "Hello World"}


@app.post("/push")
async def post_push(request: Request):
    try:
        body = await request.body()
        encryption = request.headers["encryption"]
        crypto_key = request.headers["crypto-key"]
        handle_push_notification(body, encryption, crypto_key)
    finally:
        return {"message": "Hello World"}
