import time
from TescoAPI import TescoAPI
from DatabaseAPI import DatabaseAPI
import os
import urllib.parse
from dotenv import load_dotenv
import locale
from discordwebhook import Discord as discordwebhook
import discord
from discord.ext import commands
import time
import asyncio
from datetime import datetime
from utils import logger
import numpy as np

load_dotenv()
discord_webhook_url=os.getenv("discord_webhook_url")
discord_token=os.getenv("discord_token")
price_check_rate=os.getenv("price_check_rate")

intents = discord.Intents.all()
client = discord.Client(command_prefix=',', intents=intents)

discord_webhook = discordwebhook(url=discord_webhook_url)

def format_number_as_currency(number):
    locale.setlocale(locale.LC_ALL, '')
    currency_string = locale.format_string('%.2f', number, grouping=True)
    return currency_string

def send_discord_message(message):
    discord_webhook.post(content=message, 
                         username="Tesco", 
                         avatar_url="https://www.cantechonline.com/wp-content/uploads/Tesco-Logo.jpg")
    logger("Successfully sent discord message.")

def get_item_price_update_message(item_tpnb):
    message = -1
    item_name = DatabaseAPI().get_item_by_tpnb(item_tpnb)[0][1]
    item_prices = DatabaseAPI().get_prices_by_tpnb(item_tpnb)
    message = f"### {item_name} \n "
    if len(item_prices) > 0:
        message += f"- now £{item_prices[0][2]}! \n - clubcard offer: {item_prices[0][3]}"
    if len(item_prices) >= 2:
        message += f" \n - was previously priced at £{item_prices[1][2]}"
    return message

def notify_of_price_change(item_tpnb):
    item_name = DatabaseAPI().get_item_by_tpnb(item_tpnb)[0][1]
    item_prices = DatabaseAPI().get_prices_by_tpnb(item_tpnb)
    prior_item_price = -1
    new_item_price = -1
    if len(item_prices) >= 2:
        prior_item_price = item_prices[1][2]
        new_item_price = item_prices[0][2]
    elif len(item_prices) > 0:
        new_item_price = item_prices[0][2]
    if prior_item_price == -1 and new_item_price == -1:
        logger("There was an error notifying the user of the price change.")
    elif prior_item_price != -1 and new_item_price != -1:
        send_discord_message(message=f"'{item_name}' is now £{format_number_as_currency(new_item_price)}! Clubcard deal: {item_prices[0][3]}")

def update_tesco_price(item_tpnb):
    logger(f"Checking price for tesco item (tpnb: {item_tpnb})")
    tesco_item_data = TescoAPI.get_item_details(item_tpnb)
    if tesco_item_data != -1:
        try:
            clubcard_deal_json = TescoAPI.get_item_clubcard_details(tesco_item_data)
            tesco_item_price = tesco_item_data["data"]["product"]["price"]["price"]
            if clubcard_deal_json["promotional_price"] != None and clubcard_deal_json["promotional_price"] < tesco_item_price:
                tesco_item_price = clubcard_deal_json["promotional_price"]
            stored_prices = DatabaseAPI().get_prices_by_tpnb(item_tpnb)
            if not stored_prices:
                most_recent_price = -1
            else:
                most_recent_price = stored_prices[0][2]
            if most_recent_price != tesco_item_price:
                DatabaseAPI().add_price(item_tpnb, tesco_item_price, f"{clubcard_deal_json['promotion_deal_text']}")
                logger(f"Successfully updated price for tesco item (tpnb: {item_tpnb})" +
                        f"to £{format_number_as_currency(tesco_item_price)}.")
                return True
            else:
                logger(f"Price for tesco item (tpnb: {item_tpnb}) has not changed. Finished checking price.")
                return False
        except Exception as e:
            logger(f"Error getting price for tesco item (tpnb: {item_tpnb}): {e}")
            return -1

def update_all_item_prices():
    items = DatabaseAPI().get_items()
    if items != -1:
        updated_tpnbs = []
        for item in items:
            item_tpnb = item[0]
            update_status = update_tesco_price(item_tpnb)
            updated_tpnbs.append((item_tpnb, update_status))
        return updated_tpnbs
    return -1

def format_subscriber_update_message(subscriber, updated_items):
    message = f"# {subscriber.name} price updates\n"
    message += f"Hello {subscriber.mention}, here are the price updates for your items (only showing updated prices):\n"
    item_added_to_message = False
    for item in updated_items:
        item_tpnb = item[0]
        price_update_status = item[1]
        if price_update_status == True:
            item_added_to_message = True
            message += f"{get_item_price_update_message(item_tpnb)} \n"
    if not item_added_to_message:
        message += "- *No items found :neutral_face:*" 
    return message

def update_subscribers_item_prices(subscriber):
    subscribers_items = DatabaseAPI().get_items_by_subscriber(subscriber)
    if subscribers_items == -1:
        return "there was an error getting your items."
    updated_items = []
    for item in subscribers_items:
        item_tpnb = item
        price_update_status = update_tesco_price(item_tpnb)
        updated_items.append([item_tpnb, price_update_status])
    return format_subscriber_update_message(subscriber, updated_items)

def send_updates_to_subscribers(updated_tpnbs):
    subscribers = DatabaseAPI().get_subscribers()
    if subscribers != -1:
        for subscriber in subscribers:
            subscriber = client.get_user(subscriber)
            if subscriber != None:
                subscribers_items = DatabaseAPI().get_items_by_subscriber(subscriber) 
                if subscribers_items != -1:
                    subscribers_updated_tpnbs = np.array([item for item in updated_tpnbs if item[0] in subscribers_items])
                    send_discord_message(format_subscriber_update_message(subscriber, subscribers_updated_tpnbs))
        

@client.event
async def on_ready():
    logger(f"{client.user} has connected to Discord!")
    client.loop.create_task(price_periodic_checker())

async def price_periodic_checker():
    logger(f"price checker started.")
    while True:
        logger(f"Checking tesco prices...")
        updated_tpnbs = update_all_item_prices()
        if updated_tpnbs != -1:
            send_updates_to_subscribers(updated_tpnbs)
        logger(f"Finished checking tesco prices.")
        await asyncio.sleep(int(price_check_rate))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if "www.tesco.com" in message.content:
        response = ""
        added_item_response = add_item_by_link(link=message.content, sender=message.author)
        if added_item_response != -1:
            response = f"{message.author.mention}, '{added_item_response}' added to the watchlist successfully!"
        else:
            response = f"{message.author.mention}, there was an error adding that item to the watchlist."
        await message.channel.send(response)
    if "check" in message.content:
        response = update_subscribers_item_prices(message.author)
        await message.channel.send(response)

def add_item_by_link(link, sender):
    try:
        parsed_url = urllib.parse.urlparse(link)
        if parsed_url.netloc == "www.tesco.com":
            item_tpnb = TescoAPI.find_tpnb_from_product_page(link)
            tesco_item_data = TescoAPI.get_item_details(item_tpnb)
            if tesco_item_data != -1:
                item_name = tesco_item_data["data"]["product"]["title"]
                DatabaseAPI().add_item(item_name, item_tpnb, sender)
                update_tesco_price(item_tpnb=item_tpnb)
                return item_name
    except Exception as e:
        logger(f"Error adding item by link: {e}")
        return -1
    return -1

if __name__ == '__main__':
    DatabaseAPI().create_database()
    client.run(discord_token)