from typing import Optional
import datetime
import pytz

from .exceptions import NotEnoughCash
from .rate import get_current_rate
from backtesting._util import _Data as Data
from .broker import HandonBroker
from .models import TradeModel, AccountModel
from .strategy import HandonStrategy
from .trade import HandonTrade


class HandonFxAPI:
    def __init__(self):
        self.data = None

    def start(self):
        self.data = Data(get_current_rate())

    def get_accounts(self):
        accounts = []
        for account in AccountModel.scan():
            accounts.append(account)
        return accounts

    def get_account_info(self, account_id: str, create_account: bool = True):
        try:
            account = AccountModel.get(account_id)
        except AccountModel.DoesNotExist:
            if create_account:
                account = AccountModel(account_id=account_id, cash=100_0000)
                account.save()
            else:
                raise AccountModel.DoesNotExist
        return account

    def get_open_trades(self, account_id: str):
        return TradeModel.account_state_index.query(
            account_id, TradeModel.state == "open"
        )

    def _create_broker(self, account_id, cash):
        broker = HandonBroker(
            data=self.data,
            cash=cash,
            commission=0,
            margin=1.0 / 20.0,
            trade_on_close=False,
            hedging=False,
            exclusive_orders=False,
            index=self.data.index,
            lot_unit=10000,
        )

        trades = map(
            lambda trade: HandonTrade.from_model(broker, trade),
            self.get_open_trades(account_id),
        )
        broker.trades = list(trades)

        return broker

    def rate(self):
        return self.data.Close[-1]

    def _get_summary(self, account: AccountModel, broker: HandonBroker):
        summary = broker.summary()
        summary["debt"] = account.current_debt
        return summary

    def summary(self, account_id: str):
        account = self.get_account_info(account_id)
        broker = self._create_broker(account.account_id, account.cash)
        return self._get_summary(account, broker)

    def _update_trade(self, broker, account: AccountModel, exit_cash: float):
        updated_trades = list(
            map(
                lambda trade: trade.to_model(account_id=account.account_id),
                broker.trades,
            )
        )

        updated_trades += list(
            map(
                lambda trade: trade.to_model(
                    account_id=account.account_id, exit_cash=exit_cash
                ),
                broker.closed_trades,
            )
        )

        with TradeModel.batch_write() as batch:
            for trade in updated_trades:
                batch.save(trade)
        account.update(actions=[AccountModel.cash.set(exit_cash)])

    def buy(self, account_id: str, size: Optional[float] = None):
        return self.order(account_id, "buy", size)

    def sell(self, account_id: str, size: Optional[float] = None):
        return self.order(account_id, "sell", size)

    def order(self, account_id: str, side: str, size: Optional[float] = None):
        account = self.get_account_info(account_id)
        broker = self._create_broker(account.account_id, account.cash)
        strategy = HandonStrategy(data=self.data, broker=broker, params={})
        strategy.init()

        before_summary = self._get_summary(account, broker)

        if side == "buy":
            if size is None:
                strategy.buy()
            else:
                strategy.buy(size=size)
        else:
            if size is None:
                strategy.sell()
            else:
                strategy.sell(size=size)
        broker.next()

        after_summary = self._get_summary(account, broker)
        self._update_trade(broker, account, after_summary["cash"])

        return {
            "price": self.data.Close[-1],
            "before_summary": before_summary,
            "after_summary": after_summary,
        }

    def close_position(self, account_id: str):
        account = self.get_account_info(account_id)
        broker = self._create_broker(account.account_id, account.cash)
        before_summary = self._get_summary(account, broker)
        broker.close_trades(self.data.Close[-1])
        after_summary = self._get_summary(account, broker)
        self._update_trade(broker, account, after_summary["cash"])

        return {
            "price": self.data.Close[-1],
            "before_summary": before_summary,
            "after_summary": after_summary,
        }

    def get_equity(self, account: AccountModel):
        broker = self._create_broker(account.account_id, account.cash)
        return broker.equity

    def ranking(self):
        """
        評価額ランキングを取得する
        :return: 評価額ランキング
        """
        accounts = self.get_accounts()

        ranking = []
        for account in accounts:
            broker = self._create_broker(account.account_id, account.cash)
            ranking.append(
                {
                    "account_id": account.account_id,
                    "equity": broker.equity - account.current_debt,
                }
            )

        return sorted(ranking, key=lambda x: x["equity"], reverse=True)

    def request_debt(self, account_id: str, size: int):
        account = self.get_account_info(account_id)

        if size > account.debt_limit:
            raise NotEnoughCash(f"今月の借り入れ金額はあと{account.debt_limit}円までです")

        # 複利計算
        new_cash = account.cash + size
        new_debt_size = account.current_debt + size
        new_month_debt = account.this_month_debt + size

        account.update(
            actions=[
                AccountModel.cash.set(new_cash),
                AccountModel.debt.set(new_debt_size),
                AccountModel.month_debt.set(new_month_debt),
                AccountModel.debt_date.set(datetime.datetime.utcnow()),
            ]
        )

        return {
            "cash": new_cash,
            "debt": new_debt_size,
            "size": size,
            "month_limit": account.debt_limit,
        }

    def pay_debt(self, account_id: str, size: Optional[int] = None):
        account = self.get_account_info(account_id)
        broker = self._create_broker(account.account_id, account.cash)

        if size is None or size > account.current_debt:
            size = account.current_debt

        if size > broker.margin_available:
            raise NotEnoughCash(f"余力が{size - account.cash}円足りません")
        if size > account.cash:
            raise NotEnoughCash(f"現金が{size - account.cash}円足りません。ポジションを決済してください")

        new_cash = account.cash - size
        new_debt_size = account.current_debt - size
        new_month_debt = max(account.this_month_debt - size, 0)
        # for debug
        if new_debt_size == 0:
            new_month_debt = 0

        account.update(
            actions=[
                AccountModel.cash.set(new_cash),
                AccountModel.debt.set(new_debt_size),
                AccountModel.month_debt.set(new_month_debt),
                AccountModel.debt_date.set(datetime.datetime.utcnow()),
            ]
        )

        return {
            "cash": new_cash,
            "debt": new_debt_size,
            "size": size,
            "month_limit": account.debt_limit,
        }
