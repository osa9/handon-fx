from .utils import (
    _find,
    BUY_TEXTS,
    SELL_TEXTS,
    UNPOSITION_TEXTS,
    HELP_TEXTS,
    SUMMARY_TEXTS,
    RANKING_TEXTS,
    _find_n,
    _find_obj,
    RATE_TEXTS,
    yen,
    DEBT_TEXT,
    CLEAR_DEBT_TEXTS,
    _find_yen,
    WORST_RANKING_TEXTS,
)
from handon_fx.fx import HandonFxAPI
from ..fx.exceptions import NotEnoughCash


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
        ranking = _find(RANKING_TEXTS, text)
        debt = _find(DEBT_TEXT, text)
        clear_debt = _find(CLEAR_DEBT_TEXTS, text)

        ops = sum(
            [buy, sell, unposition, help, summary, rate, debt, clear_debt, ranking]
        )
        if ops != 1:
            n = _find_n(text)
            o = _find_obj(text)
            print({"obj": o, "len": len(o) })
            if ops == 0 and len(n) == 1 and len(o) == 0:
                return {"operation": "buy", "size": n[0]}
            elif ops == 2 and len(n) == 1 and len(o) == 1:
                return { "operation": "buy", "size": n[0], "pair": o[0], }
            else:
                print({"ops": ops, "n": n, "obj": o, "len": len(o) })
                return {"operation": "unknown"}

        if debt:
            debt_sizes = _find_yen(text)
            if len(debt_sizes) != 1:
                return {
                    "operation": "notion",
                    "message": "借りたい金額を1つだけ円で指定してください。(例: 100万円借りるなら「100万円借して下さいお願いします」)",
                }
            return {"operation": "debt", "size": debt_sizes[0]}
        elif clear_debt:
            debt_sizes = _find_yen(text)
            if len(debt_sizes) > 1:
                return {
                    "operation": "notion",
                    "message": "返済額を1つだけ円で指定してください。指定なしの場合は現金から返せるだけ返します。(例: 100万円返済するなら「100万円返します」)",
                }
            return {
                "operation": "clear_debt",
                "size": debt_sizes[0] if len(debt_sizes) == 1 else None,
            }
        if buy or sell:
            n = _find_n(text)
            o = _find_obj(text)
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
                if len(o) == 0:
                    return {"operation": "buy", "size": n[0]}
                elif len(o) == 1:
                    return { "operation": "buy", "size": n[0], "pair": o[0], }
                else:
                    return { "operation": "unknown" }
            else:
                if len(o) == 0:
                    return {"operation": "sell", "size": n[0]}
                elif len(o) == 1:
                    return { "operation": "sell", "size": n[0], "pair": o[0], }
                else:
                    return { "operation": "unknown" }

        elif unposition:
            return {"operation": "unposition"}
        elif help:
            return {"operation": "help"}
        elif summary:
            return {"operation": "summary"}
        elif ranking:
            worst = _find(WORST_RANKING_TEXTS, text)
            return {"operation": "ranking", "worst": worst}
        elif rate:
            return {"operation": "rate"}

    def _summary_message(self, summary):
        message = "現在のポジションは以下の通りです。\n"

        position_text = "なし"
        avg_price = "{:.3f}".format(summary["position_avg_price"])
        if summary["position_size"] > 0:
            position_text = (
                f"買い {summary['position_size']//10000}ロット (平均建玉価格{avg_price}円)"
            )
        elif summary["position_size"] < 0:
            position_text = (
                f"売り {-summary['position_size']//10000}ロット (平均建玉価格{avg_price}円)"
            )

        message += f"評価額: {yen(summary['equity'])}"
        if summary["debt"] > 0:
            message += f" (借金: {yen(summary['debt'])})"
        message += f"\n"
        message += f"余力: {yen(summary['margin_available'])}"
        message += f"({int(summary['lots_avaitable'])}ロット)\n"
        message += (
            f"損益: {'+' if int(summary['profit'])>=0 else ''}{yen(summary['profit'])}\n"
        )
        message += f"ポジション: {position_text}\n"
        message += f"現在のレート: {summary['rate']}円\n"
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
        if ops["operation"] == "help":
            return "自分で考えろ"
        if ops["operation"] == "summary":
            fx = HandonFxAPI()
            fx.start()
            summary = fx.summary(account_id)
            return self._summary_message(summary)
        if ops["operation"] == "rate":
            fx = HandonFxAPI()
            fx.start()
            rate = fx.rate()
            return f"1ドル{rate}円です。\nhttps://finance.yahoo.co.jp/quote/USDJPY=FX"
        if ops["operation"] == "ranking":
            return self.ranking(ops["worst"])
        if ops["operation"] == "debt":
            return self.debt(account_id, ops["size"])
        if ops["operation"] == "clear_debt":
            return self.pay_debt(account_id, ops["size"])

    def ranking(self, worst=False):
        fx = HandonFxAPI()
        fx.start()
        ranking = fx.ranking()

        if worst:
            message = "現在の資産額ワーストランキングは以下の通りです。\n"
            ranking = ranking[::-1]
        else:
            message = "現在の資産額ランキングは以下の通りです。\n"

        for i, r in enumerate(ranking[:10]):
            message += f"{i+1}位: {r['account_id']} {int(r['equity'])}円\n"
        return message

    def debt(self, account_id: str, size):
        fx = HandonFxAPI()
        fx.start()
        try:
            if size == 0:
                return "0円は借りられません。"
            res = fx.request_debt(account_id, size)
            return (
                f"どんどん金融をご利用頂きありがとうございます。{res['size']}円の融資について承りました。利率は1日1%です。ご利用は計画的に。"
            )
        except NotEnoughCash as e:
            return e.message

    def pay_debt(self, account_id: str, size):
        fx = HandonFxAPI()
        fx.start()
        try:
            if size == 0:
                return "0円は返済できません。"
            res = fx.pay_debt(account_id, size)
            if res["size"] == 0:
                return "返済できませんでした。"
            return (
                f"どんどん金融をご利用頂きありがとうございます。{res['size']}円の返済について承りました。またのご利用をお待ちしております。"
            )
        except NotEnoughCash as e:
            return e.message
