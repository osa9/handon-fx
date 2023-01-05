from typing import Tuple

from backtesting import Strategy
from .trade import HandonTrade


class HandonStrategy(Strategy):
    def init(self):
        pass

    def next(self):
        pass

    @property
    def trades(self) -> Tuple[HandonTrade, ...]:
        """List of active trades (see `Trade`)."""
        return tuple(self._broker.trades)
