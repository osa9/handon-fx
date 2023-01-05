from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.indexes import AllProjection
from pynamodb.models import Model, GlobalSecondaryIndex
import os


class OrderModel(Model):
    pass


class AccountTradeIndex(GlobalSecondaryIndex):
    class Meta:
        projection = AllProjection()
        index_name = os.getenv("TRADE_TABLE_ACCOUNT_STATE_INDEX")

    account_id = UnicodeAttribute(hash_key=True)
    state = UnicodeAttribute(range_key=True)


class TradeModel(Model):
    class Meta:
        table_name = os.getenv("TRADE_TABLE")
        host = os.getenv("DYNAMODB_HOST")
        region = os.getenv("REGION")

    trade_id = UnicodeAttribute(hash_key=True)

    account_id = UnicodeAttribute()
    state = UnicodeAttribute()  # open, done, canceled

    instrument = UnicodeAttribute()  # JPY/USD
    size = NumberAttribute()  # マイナスなら買い
    entry_price = NumberAttribute()  # エントリ時の価格
    entry_time = UTCDateTimeAttribute()  # エントリ時間
    exit_price = NumberAttribute(null=True)  # ポジションの約定価格の価格
    exit_time = UTCDateTimeAttribute(null=True)  # ポジションの約定時間
    exit_cash = NumberAttribute(null=True)  # ポジションの約定時の残金

    account_state_index = AccountTradeIndex()


class AccountModel(Model):
    class Meta:
        table_name = os.getenv("ACCOUNT_TABLE")
        host = os.getenv("DYNAMODB_HOST")
        region = os.getenv("REGION")

    account_id = UnicodeAttribute(hash_key=True)  # user@handon.club
    cash = NumberAttribute()  # 現金
