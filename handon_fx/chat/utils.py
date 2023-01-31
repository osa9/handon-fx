import re

BUY_TEXTS = ["買", "ロング", "long", "Long", "L", "buy", "Buy"]
SELL_TEXTS = ["売", "ショート", "short", "Short", "S", "sell", "Sell"]
UNPOSITION_TEXTS = ["解消", "利確", "損切"]
HELP_TEXTS = ["ヘルプ", "help"]
SUMMARY_TEXTS = [
    "サマリ",
    "summary",
    "Summary",
    "ポジション",
    "Position",
    "position",
    "残高",
    "余力",
]
RATE_TEXTS  = ["レート", "Rate", "rate", "価格", "ドル", "為替"]
PAIRS_TEXTS = {
        "USDJPY": ["USDJPY", "USD/JPY", "USD-JPY", "ドル円", "どるえん", "ドル", "どる", ],
        "EURJPY": ["EURJPY", "EUR/JPY", "EUR-JPY", "ユロ円", "ユロ", "ユーロ", ],
        "AUDJPY": ["AUDJPY", "AUD/JPY", "AUD-JPY", "オジ円", "オジ", "オージー", ],
        "BGPJPY": ["BGPJPY", "BGP/JPY", "BGP-JPY", "ポン円", "ポン", ],
        "EURUSD": ["EURUSD", "EUR/USD", "EUR-USD", "EURUSD", ],
        "AUDUSD": ["AUDUSD", "AUD/USD", "AUD-USD", "AUDUSD", ],
        "BGPUSD": ["BGPUSD", "BGP/USD", "BGP-USD", "BGPUSD", ],
        "BTCUSD": ["BTCUSD", "BTC/USD", "BTC-USD", "ビットコイン", "ビットコ", "ビット子", ],
}
RANKING_TEXTS = ["ランキング", "ranking", "Ranking", "Rank", "rank"]
WORST_RANKING_TEXTS = ["逆", "ワースト"]
DEBT_TEXT = ["貸し", "借し"]
CLEAR_DEBT_TEXTS = ["返済", "返し", "返す"]


def _find(keywords, text):
    for t in keywords:
        if t in text:
            return True
    return False


def _find_yen(text):
    numbers = re.findall(r"\d+(?:,\d+)*(?:万|万円|円)", text)
    res = []
    for number_text in numbers:
        number = int(number_text.replace(",", "").replace("万", "0000").replace("円", ""))
        res += [number]
    return res


def _find_n(text):
    numbers = re.findall(r"[-+]?\d+(?:,\d+)*(?:\.\d+)?%?", text)

    res = []
    for number_text in numbers:
        number = float(number_text.rstrip("%"))
        if "%" in number_text:
            if number > 100:
                number = 0.999998
            elif number < -100:
                number = -0.999998
            elif abs(abs(number) - 100) < 0.0001:
                number = 0.999998
            else:
                number /= 100
        if "-" in number_text:
            number = -number
        if number > 1:
            number = int(number)
        res += [number]

    return res



def _find_obj(text):
    """Find the target object in the text.

    Args:
    text -- user-posted string.

    Returns:
    - [] when there is no target object.
    - [elems] when there are target objects.

    See Also:
    - ``._find``
    - ``._find_yen``
    - ``._find_n``
    """

    res = []
    for k_pr in PAIRS_TEXTS.keys():
        if _find(PAIRS_TEXTS[k_pr], text):
            print({"matched": k_pr , "text": text})
            res.append(k_pr)
    return res


def remove_html_tags(text):
    """Remove html tags from a string"""
    clean_a = re.compile("<a.*?>(.*?)</a>")
    clean_tag = re.compile("<.*?>")
    clean_emoji = re.compile(r":[^:\s]*:")
    text = re.sub(clean_a, "", text)
    text = re.sub(clean_tag, "", text)
    text = re.sub(clean_emoji, "", text)
    return text


def yen(n):
    n = int(n)
    if n < 10000:
        return str(n) + "円"
    else:
        return f"{n // 10000}万{n % 10000}円"
