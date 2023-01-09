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
RATE_TEXTS = ["レート", "Rate", "rate", "価格", "ドル", "為替"]
RANKING_TEXTS = ["ランキング", "ranking", "Ranking", "Rank", "rank"]


def _find(keywords, text):
    for t in keywords:
        if t in text:
            return True
    return False


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
