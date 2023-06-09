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

def get_what_price_part_changed(item_prices):
    # [standard_price_change, clubcard_price_change, clubcard_msg_change]
    changes = {"spc": False, "cpc": False, "cmc": False}
    if len(item_prices) == 0:
        return []
    elif len(item_prices) == 1:
        return {"spc": True, "cpc": True, "cmc": True}
    elif len(item_prices) >= 2:
        most_recent_price = item_prices[0]
        second_most_recent_price = item_prices[1]
        if most_recent_price[4] is not None and second_most_recent_price[4] is not None:
            if float(most_recent_price[4]) != float(second_most_recent_price[4]):
                changes["cpc"] = True
        if most_recent_price[3] is not None and second_most_recent_price[3] is not None:
            if most_recent_price[3] != second_most_recent_price[3]:
                changes["cmc"] = True
        if float(most_recent_price[2]) != float(second_most_recent_price[2]):
            changes["spc"] = True
    return changes

def get_update_status_message(item_price_status):
    if(item_price_status):
        return "(`changed`) "
    else:
        return ""

def get_item_price_update_message(item_tpnb):
    message = -1
    item_name = DatabaseAPI().get_item_by_tpnb(item_tpnb)[0][1]
    item_prices = DatabaseAPI().get_prices_by_tpnb(item_tpnb)
    price_change_status = get_what_price_part_changed(item_prices)
    message = f"### {item_name} \n "
    if len(item_prices) > 0:
        clubcard_is_best_price = False
        clubcard_price = item_prices[0][4]
        if clubcard_price != None:
            clubcard_price = float(clubcard_price)
            if clubcard_price < float(item_prices[0][2]):
                clubcard_is_best_price = True
        if clubcard_is_best_price:
            message += f"- {get_update_status_message(price_change_status['cpc'])}best price £{clubcard_price}! (*Clubcard Price*) \n "
            message += f"- {get_update_status_message(price_change_status['spc'])}price normally £{item_prices[0][2]} \n "
        else:
            message += f"- {get_update_status_message(price_change_status['spc'])}best price £{item_prices[0][2]}! (*Standard*) \n "
            if clubcard_price != None:
                message += f"- {get_update_status_message(price_change_status['cpc'])}clubcard price is £{clubcard_price} \n " 
        message += f"- {get_update_status_message(price_change_status['cmc'])}clubcard offer: {item_prices[0][3]}"
    return message

def update_tesco_price(item_tpnb):
    logger(f"Checking price for tesco item (tpnb: {item_tpnb})")
    tesco_item_data = TescoAPI.get_item_details(item_tpnb)
    if tesco_item_data != -1:
        try:
            clubcard_deal_json = TescoAPI.get_item_clubcard_details(tesco_item_data)
            tesco_item_price = tesco_item_data["data"]["product"]["price"]["price"]
            tesco_clubcard_price = clubcard_deal_json["promotional_price"]
            tesco_clubcard_message = str(clubcard_deal_json['promotion_deal_text'])
            stored_prices = DatabaseAPI().get_prices_by_tpnb(item_tpnb)
            if not stored_prices:
                most_recent_price = -1
            else:
                most_recent_price = stored_prices[0][2]
                most_recent_clubcard_price = stored_prices[0][4]
                most_recent_clubcard_message = stored_prices[0][3]
            if most_recent_price != tesco_item_price or most_recent_clubcard_price != tesco_clubcard_price or most_recent_clubcard_message != tesco_clubcard_message:
                DatabaseAPI().add_price(item_tpnb, tesco_item_price, f"{clubcard_deal_json['promotion_deal_text']}", tesco_clubcard_price)
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

def format_subscriber_update_message(subscriber):
    message = f"# {subscriber.name} item updates\n"
    message += f"Hello {subscriber.mention}, here are the price updates for your items (only showing updated items):\n"
    item_added_to_message = False
    for item_tpnb in DatabaseAPI().get_unviewed_item_changes(subscriber):
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
    formatted_message = format_subscriber_update_message(subscriber)
    DatabaseAPI().update_subscribers_last_viewed(subscriber)
    return formatted_message

async def send_updates_to_subscribers():
    subscribers = DatabaseAPI().get_subscribers()
    if subscribers != -1:
        for subscriber in subscribers:
            subscriber = await client.fetch_user(subscriber)
            if subscriber != None:
                subscribers_items = DatabaseAPI().get_items_by_subscriber(subscriber) 
                if subscribers_items != -1:
                    formatted_message = format_subscriber_update_message(subscriber)
                    DatabaseAPI().update_subscribers_last_viewed(subscriber)
                    send_discord_message(formatted_message)

def send_subscribed_item_list(subscriber):
    message = f"# {subscriber.name} subscribed items"
    items = DatabaseAPI().get_items_by_subscriber(subscriber)
    if items != -1:
        message += f" \n{subscriber.mention}, here are your subscribed items:"
        for tpnb in items:
            item = DatabaseAPI().get_item_by_tpnb(tpnb)
            if item != -1 and len(item) > 0:
                message += f" \n- {item[0][1]}"
                prices = DatabaseAPI().get_prices_by_tpnb(tpnb)
                if prices != -1 and len(prices) > 0:
                    message += f" \n - price: £{prices[0][2]}"
                    if prices[0][4] is not None:
                        message += f" \n - clubcard price: £{prices[0][4]}"
                    else:
                        message += f" \n - clubcard price: {prices[0][4]}"
                    message += f" \n - clubcard deal: {prices[0][3]}"
        if items == []:
            message += f" \n- *No items found :neutral_face:*"
    else:
        message += f" \n{subscriber.mention}, failed to get your subscribed items."
    return message

def get_subscribers_items_as_options(subscriber):
    options = []
    tpnbs = DatabaseAPI().get_items_by_subscriber(subscriber)
    if tpnbs != -1:
        for tpnb in tpnbs:
            item = DatabaseAPI().get_item_by_tpnb(tpnb)
            if item != -1 and len(item) > 0:
                item = item[0][1]
                options.append(discord.SelectOption(label=str(item), value=str(tpnb)))
    return options
        
class Dropdown(discord.ui.Select):
    def __init__(self, placeholder, options):
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if DatabaseAPI().remove_item_from_subscription(self.values[0], interaction.user) != -1:
            await interaction.response.send_message(f'The item has been removed from your subscription list. This dropdown will now be disabled.')
            self.view.stop()
            self.disabled = True
        else:
            await interaction.response.send_message(f'Failed to remove the item from your subscription list.')

class DropdownView(discord.ui.View):
    def __init__(self, placeholder, options):
        super().__init__()
        self.add_item(Dropdown(placeholder, options))

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
            await send_updates_to_subscribers()
        logger(f"Finished checking tesco prices.")
        await asyncio.sleep(int(price_check_rate))

@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot == True:
        return
    if "check" in message.content:
        response = update_subscribers_item_prices(message.author)
        await message.channel.send(response)
    elif "www.tesco.com" in message.content:
        response = ""
        added_item_response = add_item_by_link(link=message.content, sender=message.author)
        if added_item_response != -1:
            response = f"{message.author.mention}, '{added_item_response}' added to the watchlist successfully!"
        else:
            response = f"{message.author.mention}, there was an error adding that item to the watchlist."
        await message.channel.send(response)
    elif "list" in message.content:
        response = send_subscribed_item_list(message.author)
        await message.channel.send(response)
    elif "remove" in message.content:
        placeholder='Choose an item to remove...'
        options=get_subscribers_items_as_options(message.author)
        if options != []:
            view = DropdownView(placeholder, options)
            response = f"{message.author.mention}, here are your subscribed items:"
            await message.channel.send(response, view=view)
        else:
            await message.channel.send("You have no subscribed items.")
    

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