from .utils import (
    _find,
    BUY_TEXTS,
    SELL_TEXTS,
    UNPOSITION_TEXTS,
    HELP_TEXTS,
    SUMMARY_TEXTS,
    _find_n,
    RATE_TEXTS,
    yen,
)
from handon_fx.fx import HandonFxAPI


class ChatBot:
    def __init__(self, fxApi: HandonFxAPI):
        self.fx = fxApi

    def _parse_text(self, text: str):
        buy = _find(BUY_TEXTS, text)
        sell = _find(SELL_TEXTS, text)
        unposition = _find(UNPOSITION_TEXTS, text)
        help = _find(HELP_TEXTS, text)
        summary = _find(SUMMARY_TEXTS, text)
        rate = _find(RATE_TEXTS, text)

        ops = sum([buy, sell, unposition, help, summary, rate])
        if ops != 1:
            n = _find_n(text)
            if ops == 0 and len(n) == 1:
                return {"operation": "buy", "size": n[0]}
            return {"operation": "unknown"}

        if buy or sell:
            n = _find_n(text)
            if len(n) > 1:
                return {
                    "operation": "notion",
                    "message": "数値は最大で1つのみ含むようにします。利用可能な数値は0.3, 30%, 30等です。\n1未満の小数またはパーセンテージが指定された場合は余力からその割合を購入します。数値がなければ余力から買えるだけ書います。",
                }
            if len(n) == 0:
                n = [None]
            if n[0] is not None and n[0] < 0:
                buy = not buy
                sell = not sell
                n[0] = -n[0]

            if buy:
                return {"operation": "buy", "size": n[0]}
            else:
                return {"operation": "sell", "size": n[0]}
        elif unposition:
            return {"operation": "unposition"}
        elif help:
            return {"operation": "help"}
        elif summary:
            return {"operation": "summary"}
        elif rate:
            return {"operation": "rate"}

    def _summary_message(self, summary):
        message = "現在のポジションは以下の通りです。\n"
        # {'cash': 1000000, 'equity': 1000000.0, 'profit': 0.0, 'lots_avaitable': 0, 'position_size': 150000, 'position_avg_price': 132.122}
        position_text = "なし"
        if summary["position_size"] > 0:
            position_text = f"買い {summary['position_size']//10000}ロット (平均建玉価格{summary['position_avg_price']}円)"
        elif summary["position_size"] < 0:
            position_text = f"売り {summary['position_size']//10000}ロット (平均建玉価格{summary['position_avg_price']}円)"

        message += f"評価額: {yen(summary['equity'])}\n"
        message += f"現金: {yen(summary['cash'])}"
        message += f"(余力 {int(summary['lots_avaitable'])}ロット)\n"
        message += (
            f"損益: {'+' if int(summary['profit'])>=0 else ''}{yen(summary['profit'])}\n"
        )
        message += f"ポジション: {position_text}\n"
        return message

    def _operation_message(self, side, res):
        before = res["before_summary"]
        after = res["after_summary"]
        price = res["price"]

        size = (after["position_size"] - before["position_size"]) // 10000
        message = f"{price}円で、"
        if size > 0:
            message += f"買い{size}ロットを執行しました。\n"
        elif size < 0:
            message += f"売り{-size}ロットを執行しました。\n"
        else:
            return "余力不足です。\n"
        return message + "\n" + self._summary_message(after)

    def action(self, account_id, text):
        ops = self._parse_text(text)

        if ops["operation"] == "notion":
            return ops["message"]
        if ops["operation"] == "buy":
            fx = HandonFxAPI()
            fx.start()

            unit = ops["size"]
            if unit is None:
                summary = fx.summary(account_id)
                if summary["position_size"] < 0:
                    res = fx.close_position(account_id)
                    return self._operation_message("buy", res)
            if unit == 0:
                return "0ロットは取引できません。"
            if unit and unit >= 1:
                unit *= 10000

            res = fx.buy(account_id, unit)
            return self._operation_message("buy", res)
        if ops["operation"] == "sell":
            fx = HandonFxAPI()
            fx.start()

            unit = ops["size"]
            if unit is None:
                summary = fx.summary(account_id)
                if summary["position_size"] > 0:
                    res = fx.close_position(account_id)
                    return self._operation_message("sell", res)
            if unit == 0:
                return "0ロットは取引できません。"
            if unit and unit >= 1:
                unit *= 10000

            res = fx.sell(account_id, unit)
            return self._operation_message("sell", res)
        if ops["operation"] == "unposition":
            fx = HandonFxAPI()
            fx.start()
            res = fx.close_position(account_id)
            return self._operation_message("unposition", res)
            pass
        if ops["operation"] == "help":
            return "自分で考えろ"
        if ops["operation"] == "summary":
            fx = HandonFxAPI()
            fx.start()
            summaru = fx.summary(account_id)
            return self._summary_message(summaru)
        if ops["operation"] == "rate":
            fx = HandonFxAPI()
            fx.start()
            rate = fx.rate()
            return f"1ドル{rate}円です。\nhttps://finance.yahoo.co.jp/quote/USDJPY=FX"
