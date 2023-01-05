from typing import Optional, Union

import pandas as pd
from uuid6 import uuid7

from backtesting.backtesting import Trade, _Broker, Order
import datetime

from .models import TradeModel


class HandonTrade(Trade):
    """
    When an `Order` is filled, it results in an active `Trade`.
    Find active trades in `Strategy.trades` and closed, settled trades in `Strategy.closed_trades`.
    """

    def __init__(
        self, broker: _Broker, size: int, entry_price: float, entry_bar, trade_id
    ):
        super().__init__(broker, size, entry_price, entry_bar, trade_id)

    def _get(self, k):
        return getattr(self, f"_Trade{k}")

    def _replace(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, f"_Trade__{k}", v)
        return self

    def _copy(self, **kwargs):
        copied = super()._copy(**kwargs)
        copied._replace(tag=str(uuid7()))  # DBのIDを新規にする

        return copied

    def __repr__(self):
        entry_bar = datetime.datetime.fromtimestamp(
            self._get("__entry_bar")
        ).isoformat()
        exit_bar = (
            datetime.datetime.fromtimestamp(self._get("__exit_bar")).isoformat()
            if self._get("__exit_bar") is not None
            else ""
        )
        return (
            f'<Trade size={self._get("__size")} time={entry_bar}-{exit_bar or ""} '
            f'price={self._get("__entry_price")}-{self._get("__exit_price") or ""} pl={self.pl:.0f}'
            f'{" tag="+str(self._get("__tag")) if self._get("__tag") is not None else ""}>'
        )

    @property
    def entry_time(self) -> Union[pd.Timestamp, int]:
        """Datetime of when the trade was entered."""
        return datetime.datetime.fromtimestamp(self._get("__entry_bar"))

    @property
    def exit_time(self) -> Optional[Union[pd.Timestamp, int]]:
        """Datetime of when the trade was exited."""
        if self.__exit_bar is None:
            return None
        return datetime.datetime.fromtimestamp(self._get("__exit_bar"))

    def to_model(
        self,
        account_id: str,
        instrument: str = "JPY/USD",
        exit_cash: Optional[float] = None,
    ):
        state = "open" if self._get("__exit_price") is None else "done"
        exit_price = self._get("__exit_price")
        exit_bar = self._get("__exit_bar")
        if exit_bar is not None:
            exit_bar = datetime.datetime.fromtimestamp(exit_bar)

        return TradeModel(
            trade_id=self._get("__tag") or str(uuid7()),
            account_id=account_id,
            state=state,
            instrument=instrument,
            size=self._get("__size"),
            entry_price=self._get("__entry_price"),
            entry_time=datetime.datetime.fromtimestamp(self._get("__entry_bar")),
            exit_price=exit_price,
            exit_time=exit_bar,
            exit_cash=exit_cash,
        )

    @staticmethod
    def from_model(broker, model: TradeModel):
        entry_time = int(model.entry_time.timestamp())
        exit_time = model.exit_price
        if exit_time is not None:
            exit_time = int(exit_time.timestamp())
        trade = HandonTrade(
            broker=broker,
            size=model.size,
            entry_price=model.entry_price,
            entry_bar=entry_time,
            trade_id=model.trade_id,
        )
        trade._replace(
            exit_bar=exit_time,
            exit_price=model.exit_price,
        )
        return trade
