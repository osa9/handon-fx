from chat_bot import parse_text
from handon_fx import HandonFxAPI
from handon_fx.models import TradeModel, AccountModel


def main2():
    if not TradeModel.exists():
        TradeModel.create_table(wait=True, billing_mode="PAY_PER_REQUEST")
    if not AccountModel.exists():
        AccountModel.create_table(wait=True, billing_mode="PAY_PER_REQUEST")

    fx = HandonFxAPI()
    fx.start()
    fx.order("osa9@handon.club", 10000)


def main():
    while True:
        text = input("> ")
        if text == "":
            break
        ops = parse_text(text)
        print(ops)
        if ops["operation"] == "buy":
            unit = ops["size"]
            if unit >= 1:
                unit *= 10000
            print("buy " + str(unit))
            fx = HandonFxAPI()
            fx.start()
            fx.order("osa9@handon.club", unit)
        if ops["operation"] == "sell":
            unit = ops["size"]
            if unit >= 1:
                unit *= 10000
            print("sell " + str(unit))
            fx = HandonFxAPI()
            fx.start()
            fx.order("osa9@handon.club", -unit)


if __name__ == "__main__":
    main()
