from TescoAPI import TescoAPI
from DatabaseAPI import DatabaseAPI
import os
from dotenv import load_dotenv
import locale

load_dotenv()

def format_number_as_currency(number):
    locale.setlocale(locale.LC_ALL, '')
    currency_string = locale.format_string('%.2f', number, grouping=True)
    return currency_string

def notify_of_price_change(item_tpnb):
    item_name = DatabaseAPI().get_item_by_tpnb(item_tpnb)[0][1]
    item_prices = DatabaseAPI().get_prices_by_tpnb(item_tpnb)
    print(f"'{item_name}' is now £{format_number_as_currency(item_prices[0][2])}! "
          f"(was £{format_number_as_currency(item_prices[1][2])})")

def update_tesco_prices():
    items = DatabaseAPI().get_items()
    if items != -1:
        for item in items:
            item_tpnb = item[0]
            tesco_item_data = TescoAPI.get_item_details(item_tpnb)
            if tesco_item_data != -1:
                try:
                    tesco_item_price = tesco_item_data["data"]["product"]["price"]["price"]
                    stored_prices = DatabaseAPI().get_prices_by_tpnb(item_tpnb)
                    if len(stored_prices) != 0:
                        most_recent_price = stored_prices[0][2]
                        if most_recent_price != tesco_item_price:
                            DatabaseAPI().add_price(item_tpnb, tesco_item_price)
                            notify_of_price_change(item_tpnb)
                except Exception as e:
                    print(f"Error getting price for tesco item (tpnb: {item_tpnb}): {e}")


if __name__ == '__main__':
    update_tesco_prices()
