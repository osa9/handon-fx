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

    def _update_trade(self, broker, account_id: str, exit_cash: float):
        updated_trades = list(
            map(
                lambda trade: trade.to_model(account_id=account_id),
                broker.trades,
            )
        )

        updated_trades += list(
            map(
                lambda trade: trade.to_model(
                    account_id=account_id, exit_cash=exit_cash
                ),
                broker.closed_trades,
            )
        )

        with TradeModel.batch_write() as batch:
            for trade in updated_trades:
                batch.save(trade)

    def buy(self, account_id: str, size: Optional[float] = None):
        return self.order(account_id, "buy", size)

    def sell(self, account_id: str, size: Optional[float] = None):
        return self.order(account_id, "sell", size)

    def order(self, account_id: str, side: str, size: Optional[float] = None):
        account = self.get_account_info(account_id)
        broker = self._create_broker(account.account_id, account.cash)
        strategy = HandonStrategy(data=self.data, broker=broker, params={})
        strategy.init()

        # print(broker.position)
        before_summary = broker.summary()

        # print("initial trade:")
        # for trade in broker.trades:
        #    print("\t", trade)

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

        # print("open trade:")
        # for trade in broker.trades:
        #    print("\t", trade)

        # print("closed trade:")
        # for trade in broker.closed_trades:
        #    print("\t", trade)

        after_summary = broker.summary()
        self._update_trade(broker, account_id, after_summary["cash"])
        account.update(actions=[AccountModel.cash.set(after_summary["cash"])])

        # print(before_summary)
        # print(after_summary)
        # print(updated_trades)
        # print(broker.position)

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
        self._update_trade(broker, account_id, after_summary["cash"])
        return {
            "price": self.data.Close[-1],
            "before_summary": before_summary,
            "after_summary": after_summary,
        }
