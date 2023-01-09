from typing import Optional

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

    def summary(self, account_id: str):
        account = self.get_account_info(account_id)
        broker = self._create_broker(account.account_id, account.cash)
        return broker.summary()

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

        before_summary = broker.summary()

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

        after_summary = broker.summary()
        self._update_trade(broker, account, after_summary["cash"])

        return {
            "price": self.data.Close[-1],
            "before_summary": before_summary,
            "after_summary": after_summary,
        }

    def close_position(self, account_id: str):
        account = self.get_account_info(account_id)
        broker = self._create_broker(account.account_id, account.cash)
        before_summary = broker.summary()
        broker.close_trades(self.data.Close[-1])
        after_summary = broker.summary()
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
                    "equity": broker.equity,
                }
            )

        return sorted(ranking, key=lambda x: x["equity"], reverse=True)
