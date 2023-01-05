from datetime import datetime
from math import copysign
from typing import Optional

from backtesting.backtesting import _Broker, Trade
import numpy as np
import warnings

from .trade import HandonTrade


class HandonBroker(_Broker):
    def __init__(
        self,
        *,
        data,
        cash,
        commission,
        margin,
        trade_on_close,
        hedging,
        exclusive_orders,
        index,
        lot_unit=100000,
    ):
        super().__init__(
            data=data,
            cash=cash,
            commission=commission,
            margin=margin,
            trade_on_close=trade_on_close,
            hedging=hedging,
            exclusive_orders=exclusive_orders,
            index=index,
        )
        self.lot_unit = lot_unit

    def _process_orders(self):
        data = self._data
        open, high, low = data.Open[-1], data.High[-1], data.Low[-1]
        prev_close = data.Close[-2]
        reprocess_orders = False

        # Process orders
        for order in list(self.orders):  # type: Order

            # Related SL/TP order was already removed
            if order not in self.orders:
                continue

            # Check if stop condition was hit
            stop_price = order.stop
            if stop_price:
                is_stop_hit = (
                    (high > stop_price) if order.is_long else (low < stop_price)
                )
                if not is_stop_hit:
                    continue

                # > When the stop price is reached, a stop order becomes a market/limit order.
                # https://www.sec.gov/fast-answers/answersstopordhtm.html
                order._replace(stop_price=None)

            # Determine purchase price.
            # Check if limit order can be filled.
            if order.limit:
                is_limit_hit = (
                    low < order.limit if order.is_long else high > order.limit
                )
                # When stop and limit are hit within the same bar, we pessimistically
                # assume limit was hit before the stop (i.e. "before it counts")
                is_limit_hit_before_stop = is_limit_hit and (
                    order.limit < (stop_price or -np.inf)
                    if order.is_long
                    else order.limit > (stop_price or np.inf)
                )
                if not is_limit_hit or is_limit_hit_before_stop:
                    continue

                # stop_price, if set, was hit within this bar
                price = (
                    min(stop_price or open, order.limit)
                    if order.is_long
                    else max(stop_price or open, order.limit)
                )
            else:
                # Market-if-touched / market order
                price = prev_close if self._trade_on_close else open
                price = (
                    max(price, stop_price or -np.inf)
                    if order.is_long
                    else min(price, stop_price or np.inf)
                )

            # Determine entry/exit bar index
            is_market_order = not order.limit and not stop_price
            time_index = (
                (self._i - 1) if is_market_order and self._trade_on_close else self._i
            )

            # If order is a SL/TP order, it should close an existing trade it was contingent upon
            if order.parent_trade:
                trade = order.parent_trade
                _prev_size = trade.size
                # If order.size is "greater" than trade.size, this order is a trade.close()
                # order and part of the trade was already closed beforehand
                size = copysign(min(abs(_prev_size), abs(order.size)), order.size)
                # If this trade isn't already closed (e.g. on multiple `trade.close(.5)` calls)
                if trade in self.trades:
                    self._reduce_trade(trade, price, size, time_index)
                    assert order.size != -_prev_size or trade not in self.trades
                if order in (trade._sl_order, trade._tp_order):
                    assert order.size == -trade.size
                    assert order not in self.orders  # Removed when trade was closed
                else:
                    # It's a trade.close() order, now done
                    assert abs(_prev_size) >= abs(size) >= 1
                    self.orders.remove(order)
                continue

            # Else this is a stand-alone trade

            # Adjust price to include commission (or bid-ask spread).
            # In long positions, the adjusted price is a fraction higher, and vice versa.
            adjusted_price = self._adjusted_price(order.size, price)

            # If order size was specified proportionally,
            # precompute true size in units, accounting for margin and spread/commissions
            size = order.size
            if -1 < size < 1:
                size = copysign(
                    int(
                        (self.margin_available * self._leverage * abs(size))
                        // adjusted_price
                    ),
                    size,
                )
                size = (size // self.lot_unit) * self.lot_unit
                # Not enough cash/margin even for a single unit
                if not size:
                    self.orders.remove(order)
                    continue
            assert size == round(size)
            need_size = int(size)

            if not self._hedging:
                # Fill position by FIFO closing/reducing existing opposite-facing trades.
                # Existing trades are closed at unadjusted price, because the adjustment
                # was already made when buying.
                for trade in list(self.trades):
                    if trade.is_long == order.is_long:
                        continue
                    assert trade.size * order.size < 0

                    # Order size greater than this opposite-directed existing trade,
                    # so it will be closed completely
                    if abs(need_size) >= abs(trade.size):
                        self._close_trade(trade, price, time_index)
                        need_size += trade.size
                    else:
                        # The existing trade is larger than the new order,
                        # so it will only be closed partially
                        self._reduce_trade(trade, price, need_size, time_index)
                        need_size = 0

                    if not need_size:
                        break

            # If we don't have enough liquidity to cover for the order, cancel it
            if abs(need_size) * adjusted_price > self.margin_available * self._leverage:
                self.orders.remove(order)
                continue

            # Open a new trade
            if need_size:
                self._open_trade(
                    adjusted_price, need_size, order.sl, order.tp, time_index, order.tag
                )

                # We need to reprocess the SL/TP orders newly added to the queue.
                # This allows e.g. SL hitting in the same bar the order was open.
                # See https://github.com/kernc/backtesting.py/issues/119
                if order.sl or order.tp:
                    if is_market_order:
                        reprocess_orders = True
                    elif (
                        low <= (order.sl or -np.inf) <= high
                        or low <= (order.tp or -np.inf) <= high
                    ):
                        warnings.warn(
                            f"({data.index[-1]}) A contingent SL/TP order would execute in the "
                            "same bar its parent stop/limit order was turned into a trade. "
                            "Since we can't assert the precise intra-candle "
                            "price movement, the affected SL/TP order will instead be executed on "
                            "the next (matching) price/bar, making the result (of this trade) "
                            "somewhat dubious. "
                            "See https://github.com/kernc/backtesting.py/issues/119",
                            UserWarning,
                        )

            # Order processed
            self.orders.remove(order)

        if reprocess_orders:
            self._process_orders()

    def close_trades(self, price, _time_index=0):
        for trade in list(self.trades):
            self._close_trade(trade, price, _time_index)

    def _close_trade(self, trade: Trade, price: float, _time_index: int):
        super()._close_trade(trade, price, int(datetime.now().timestamp()))

    def _open_trade(
        self,
        price: float,
        size: int,
        sl: Optional[float],
        tp: Optional[float],
        time_index: int,
        tag,
    ):
        trade = HandonTrade(self, size, price, int(datetime.now().timestamp()), tag)
        self.trades.append(trade)
        if tp:
            trade.tp = tp
        if sl:
            trade.sl = sl

    def summary(self):
        return {
            "cash": self._cash,
            "equity": self.equity,
            "profit": self.equity - self._cash,
            "lots_avaitable": int(
                self.margin_available
                * self._leverage
                // self._data.Close[-1]
                // self.lot_unit
            ),
            "position_size": self.position.size,
            "position_avg_price": sum(
                trade.entry_price * trade.size for trade in self.trades
            )
            / self.position.size
            if self.position.size
            else 0,
        }
