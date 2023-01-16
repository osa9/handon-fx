import datetime

import pytz
from pynamodb.attributes import (
    UnicodeAttribute,
    NumberAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.indexes import AllProjection
from pynamodb.models import Model, GlobalSecondaryIndex
import os

from handon_fx.fx.utils import jst_same_month, jst_delta_days


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
        print(os.getenv("TRADE_TABLE"))
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
    debt = NumberAttribute(default=0)  # 借金
    month_debt = NumberAttribute(default=0)  # 今月の借金額(上限100万)
    debt_date = UTCDateTimeAttribute(null=True)  # 最後に借金した日時

    @property
    def this_month_debt(self):
        if self.debt_date is None:
            return 0
        if jst_same_month(self.debt_date):
            return self.month_debt
        return 0

    @property
    def debt_limit(self):
        if self.account_id == "hiroakichan@handon.club":
            max_debt = 1300_0000
        else:
            max_debt = 100_0000
        return max_debt - self.this_month_debt

    @property
    def current_debt(self):
        """
        現在の借金を取得する
        :param account: アカウント
        :return: 借金
        """
        if not self.debt_date:
            return int(self.debt)
        else:
            return int(self.debt * (1.01 ** jst_delta_days(self.debt_date)))
