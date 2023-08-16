import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os
from dotenv import load_dotenv
import asyncio
from web3 import Web3, WebsocketProvider, HTTPProvider
from datetime import datetime
import requests
import psycopg2
import json
import time
import sys

load_dotenv()

DATABASE_TOKEN = os.getenv('DATABASE_TOKEN')
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
ALCHEMY_MAINNET_API_KEY = os.getenv('ALCHEMY_MAINNET_API_KEY')
RESERVOIR_API_KEY = os.getenv('RESERVOIR_API_KEY')
OPENSEA_API_KEY = os.getenv('OPENSEA_API_KEY')
prohibitionContract = "0x47A91457a3a1f700097199Fd63c039c4784384aB"

# Set up the bot with the proper intents to read message content and reactions
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

class MyView(discord.ui.View):  # Create a class called MyView that subclasses discord.ui.View
    def __init__(self):
        super().__init__(timeout=None)  # timeout of the view must be set to None

    @discord.ui.button(label="Artist", style=discord.ButtonStyle.primary)  # Create a button with the label "Artist" with color Blurple
    async def artist_button_callback(self, button, interaction):
        role = discord.utils.get(interaction.guild.roles, id=1107785958746771538)
        await self.toggle_role(interaction, role)

    @discord.ui.button(label="Coder", style=discord.ButtonStyle.primary)  # Create a button with the label "Coder" with color Blurple
    async def coder_button_callback(self, button, interaction):
        role = discord.utils.get(interaction.guild.roles, id=1107786089932013709)
        await self.toggle_role(interaction, role)

    @discord.ui.button(label="Collector", style=discord.ButtonStyle.primary)  # Create a button with the label "Collector" with color Blurple
    async def collector_button_callback(self, button, interaction):
        role = discord.utils.get(interaction.guild.roles, id=1107786213575893012)
        await self.toggle_role(interaction, role)

    @staticmethod
    async def toggle_role(interaction, role):
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"I have successfully removed your {role.name} role.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"I have successfully given you the {role.name} role.", ephemeral=True)

@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, id=1101580614945222708)
    channel = discord.utils.get(guild.channels, id=1129038551066103959)
    message_id = 1129129885928005874
    message = await channel.fetch_message(message_id)
    await message.edit(content="Tap the below buttons to add/remove the corresponding role:", view=MyView())
    while True:
        await track()
        await asyncio.sleep(60)

async def getUser(address):
    headers = {
        "accept": "*/*"
    }
    url = "https://prohibition.art/api/u/"+address
    response = requests.get(url, headers=headers)
    data = json.loads(response.text)
    if data == '{"code":"NOT_FOUND","error":"Profile not found"}':
        owner_profile = "https://opensea.io/"+address
        w3 = Web3(HTTPProvider('https://eth-mainnet.g.alchemy.com/v2/'+ALCHEMY_MAINNET_API_KEY))
        owner_handle = w3.ens.name(address)
        if owner_handle == None:
            owner_handle = address
    else:
        owner_handle = data['handle']
        owner_profile = "https://prohibition.art/u/"+owner_handle
    if owner_handle == address:
        owner_handle = owner_handle[:5] + "..." + owner_handle[len(owner_handle)-5:]

    return owner_handle, owner_profile



async def track():
    try:
        #Get our discord server and channels
        guild = discord.utils.get(bot.guilds, id=1101580614945222708)
        mint_channel = discord.utils.get(guild.channels, id=1126976550508712106)
        sales_channel = discord.utils.get(guild.channels, id=1126976977199435786)
        listings_channel = discord.utils.get(guild.channels, id=1126977037765189752)

        #Get the last events we already posted
        conn = psycopg2.connect(DATABASE_TOKEN, sslmode='require')
        cur = conn.cursor()
        command = "select * from globalvariables where name = 'prohibition_latest_mint_hash'"
        cur.execute(command)
        results = cur.fetchall()
        latest_mint_hash = results[0][1]
        command = "select * from globalvariables where name = 'prohibition_latest_sale_hash'"
        cur.execute(command)
        results = cur.fetchall()
        latest_sale_hash = results[0][1]
        command = "select * from globalvariables where name = 'prohibition_latest_offer_id'"
        cur.execute(command)
        results = cur.fetchall()
        latest_offer_id = results[0][1]
        command = "select * from globalvariables where name = 'prohibition_latest_listing_id'"
        cur.execute(command)
        results = cur.fetchall()
        latest_listing_id = results[0][1]
        cur.close()
        conn.commit()
        conn.close()

        mints = []
        sales = []
        offers = []
        listings = []

        headers = {
            "accept": "*/*",
            "x-api-key": RESERVOIR_API_KEY
        }

        OSheaders = {
            "accept": "application/json",
            "X-API-KEY": OPENSEA_API_KEY
        }

        exit_flag = False
        continuation = ''

        #'Continuation' refers to pagination within the API responses
        while continuation != None and not exit_flag:
            #If it's our first time through the loop, we leave off the continuation param
            if continuation == '':
                url = "https://api-arbitrum.reservoir.tools/transfers/v3?contract=0x47A91457a3a1f700097199Fd63c039c4784384aB&limit=100"
            else:
                url = "https://api-arbitrum.reservoir.tools/transfers/v3?contract=0x47A91457a3a1f700097199Fd63c039c4784384aB&limit=100&continuation="+continuation
            response = requests.get(url, headers=headers)
            data = json.loads(response.text)

            #Go through all the transfers on the contract looking for ones coming from the 0x0 address (mint events)
            for i in data['transfers']:
                if i['price'] == None and i['from'] == '0x0000000000000000000000000000000000000000':
                    mint_hash = i['txHash']
                    #Once we reach the last one we posted, we can stop calling the API and stop adding the events to our list
                    if mint_hash == latest_mint_hash:
                        exit_flag = True
                        break
                    else:
                        mints.append(i)

            continuation = data['continuation']

            #We'll pause for a second so we don't get rate limited
            await asyncio.sleep(1)

        exit_flag = False
        continuation = ''

        #'Continuation' refers to pagination within the API responses
        while continuation != None and not exit_flag:
            #If it's our first time through the loop, we leave off the continuation param
            if continuation == '':
                url = "https://api-arbitrum.reservoir.tools/transfers/v3?contract=0x47A91457a3a1f700097199Fd63c039c4784384aB&limit=100"
            else:
                url = "https://api-arbitrum.reservoir.tools/transfers/v3?contract=0x47A91457a3a1f700097199Fd63c039c4784384aB&limit=100&continuation="+continuation
            response = requests.get(url, headers=headers)
            data = json.loads(response.text)

            #Go through all the transfers on the contract looking for ones that have a price associated with them (sale events)
            for i in data['transfers']:
                if i['price'] != None:
                    sale_hash = i['txHash']
                    #Once we reach the last one we posted, we can stop calling the API and stop adding the events to our list
                    if sale_hash == latest_sale_hash:
                        exit_flag = True
                        break
                    else:
                        sales.append(i)

            continuation = data['continuation']
            await asyncio.sleep(1)
            #We'll pause for a second so we don't get rate limited

        exit_flag = False
        continuation = ''

        #'Continuation' refers to pagination within the API responses
        while continuation != None and not exit_flag:
            #If it's our first time through the loop, we leave off the continuation param
            if continuation == '':
                url = "https://api-arbitrum.reservoir.tools/orders/bids/v6?contracts=0x47A91457a3a1f700097199Fd63c039c4784384aB"
            else:
                url = "https://api-arbitrum.reservoir.tools/orders/bids/v6?contracts=0x47A91457a3a1f700097199Fd63c039c4784384aB&continuation="+continuation
            response = requests.get(url, headers=headers)
            data = json.loads(response.text)

            #Go through all the transfers on the contract looking for ones that have a price associated with them (sale events)
            for i in data['orders']:
                offer_id = i['id']
                #Once we reach the last one we posted, we can stop calling the API and stop adding the events to our list
                if offer_id == latest_offer_id:
                    exit_flag = True
                    break
                else:
                    #If we come across a canceled or fulfilled offer, we don't want to post that
                    if i['status'] == "active":
                        offers.append(i)

            continuation = data['continuation']
            await asyncio.sleep(1)
            #We'll pause for a second so we don't get rate limited

        exit_flag = False
        continuation = ''

        #'Continuation' refers to pagination within the API responses
        while continuation != None and not exit_flag:
            #If it's our first time through the loop, we leave off the continuation param
            if continuation == '':
                url = "https://api-arbitrum.reservoir.tools/orders/asks/v5?contracts=0x47a91457a3a1f700097199fd63c039c4784384ab"
            else:
                url = "https://api-arbitrum.reservoir.tools/orders/asks/v5?contracts=0x47a91457a3a1f700097199fd63c039c4784384ab&continuation="+continuation
            response = requests.get(url, headers=headers)
            data = json.loads(response.text)

            #Go through all the transfers on the contract looking for ones that have a price associated with them (sale events)
            for i in data['orders']:
                listing_id = i['id']
                #Once we reach the last one we posted, we can stop calling the API and stop adding the events to our list
                if listing_id == latest_listing_id:
                    exit_flag = True
                    break
                else:
                    #If we come across a canceled or fulfilled listing, we don't want to post that
                    if i['status'] == "active":
                        listings.append(i)

            continuation = data['continuation']
            await asyncio.sleep(1)
            #We'll pause for a second so we don't get rate limited

        conn = psycopg2.connect(DATABASE_TOKEN, sslmode='require')
        cur = conn.cursor()

        #Go through our list in reverse order so that we post the oldest events first
        for i in reversed(mints):
            token_id = i['token']['tokenId']
            collection_name = i['token']['collection']['name']
            token_name, token_artist = collection_name.rsplit(" by ", 1)
            if token_id[-6:].lstrip('0') == "":
                token_name = token_name + " #0"
            else:
                token_name = token_name + " #"+ token_id[-6:].lstrip('0')
            image_url = "https://prohibition-arbitrum.s3.amazonaws.com/" + token_id + ".png"
            response_code = 404
            wait_time = 60
            while response_code != 200 and wait_time > 0:
                response = requests.get(image_url, headers=headers)
                response_code = response.status_code
                await asyncio.sleep(60)
                wait_time -= 1
            timestamp = i['timestamp']
            owner = i['to']
            owner_handle, owner_profile = await getUser(owner)
            latest_mint_hash = i['txHash']

            embed = discord.Embed(title=f"{token_name} by {token_artist}", description=f"{token_name} was minted by [{owner_handle}]({owner_profile}) at <t:{timestamp}:f>.\n\nhttps://prohibition.art/token/{token_id}")
            embed.set_image(url=image_url)
            await mint_channel.send(embed=embed)
            #Update our latest event so we know where we left off for next time
            command = "update globalvariables set value = '{0}' where name = 'prohibition_latest_mint_hash'".format(latest_mint_hash)
            cur.execute(command)
            conn.commit()
            #Call the OpenSea refresh metadata endpoint and get the newly rendered image updated
            url = "https://api.opensea.io/v2/chain/arbitrum/contract/0x47A91457a3a1f700097199Fd63c039c4784384aB/nfts/" + token_id + "/refresh"
            response = requests.post(url, headers=OSheaders)
            await asyncio.sleep(1)
            #We'll pause for a second so we don't get rate limited

        #Go through our list in reverse order so that we post the oldest events first
        for i in reversed(sales):
            owner = i['to']
            owner_handle, owner_profile = await getUser(owner)
            seller = i['from']
            seller_handle, seller_profile = await getUser(seller)
            token_id = i['token']['tokenId']
            collection_name = i['token']['collection']['name']
            token_name, token_artist = collection_name.rsplit(" by ", 1)
            if token_id[-6:].lstrip('0') == "":
                token_name = token_name + " #0"
            else:
                token_name = token_name + " #"+ token_id[-6:].lstrip('0')
            image_url = "https://prohibition-arbitrum.s3.amazonaws.com/" + token_id + ".png"
            response_code = 404
            wait_time = 60
            while response_code != 200 and wait_time > 0:
                response = requests.get(image_url, headers=headers)
                response_code = response.status_code
                await asyncio.sleep(60)
                wait_time -= 1
            timestamp = i['timestamp']
            price_symbol = i['price']['currency']['symbol']
            price_amount = i['price']['amount']['decimal']
            latest_sale_hash = i['txHash']
            embed = discord.Embed(title=f"{token_name} by {token_artist}", description=f"{token_name} sold for {price_amount} {price_symbol} at <t:{timestamp}:f>.\n\n**Buyer:**\n[{owner_handle}]({owner_profile})\n\n**Seller:**\n[{seller_handle}]({seller_profile})\n\nhttps://prohibition.art/token/{token_id}")
            embed.set_image(url=image_url)
            await sales_channel.send(embed=embed)
            #Update our latest event so we know where we left off for next time
            command = "update globalvariables set value = '{0}' where name = 'prohibition_latest_sale_hash'".format(latest_sale_hash)
            cur.execute(command)
            conn.commit()
            await asyncio.sleep(1)
            #We'll pause for a second so we don't get rate limited

        #Go through our list in reverse order so that we post the oldest events first
        for i in reversed(offers):
            #Get information on the maker of the offer
            maker = i['maker']
            maker_handle, maker_profile = await getUser(maker)
            #Get info on the offer
            offer_price = i['price']['amount']['decimal']
            offer_symbol = i['price']['currency']['symbol']
            latest_offer_id = i['id']
            timestamp_str = i['createdAt']
            timestamp_dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            timestamp = int(timestamp_dt.timestamp())
            #if this is a collection offer
            if i['criteria']['kind'] == "collection":
                collection_id_base = i['criteria']['data']['collection']['id'].split(":")[1]
                collection_id = str(int(collection_id_base)/1000000)
                offer_quantity = i['quantityRemaining']
                url = "https://prohibition.art/api/project/0x47A91457a3a1f700097199Fd63c039c4784384aB-"+collection_id
                response = requests.get(url, headers=headers)
                data = json.loads(response.text)
                collection_name = data['name']
                collection_artist = data['artistName']
                project_slug = data['slug']
                image_url = "https://prohibition-arbitrum.s3.amazonaws.com/" + collection_id_base + ".png"
                embed = discord.Embed(title=f"{collection_name} by {collection_artist}", description=f"{collection_name} received {offer_quantity} collection offer(s) of {offer_price} {offer_symbol} offer at <t:{timestamp}:f>.\n\n**Offer Maker:**\n[{maker_handle}]({maker_profile})\n\nhttps://prohibition.art/project/{project_slug}")
                embed.set_image(url=image_url)
                await listings_channel.send(embed=embed)
            else:
                token_id = i['criteria']['data']['token']['tokenId']
                #Get info on the token
                url = "https://api-arbitrum.reservoir.tools/tokens/v6?tokens=0x47a91457a3a1f700097199fd63c039c4784384ab%3A"+token_id
                response = requests.get(url, headers=headers)
                data = json.loads(response.text)
                collection_name = data['tokens'][0]['token']['collection']['name']
                token_name, token_artist = collection_name.rsplit(" by ", 1)
                if token_id[-6:].lstrip('0') == "":
                    token_name = token_name + " #0"
                else:
                    token_name = token_name + " #"+ token_id[-6:].lstrip('0')
                image_url = "https://prohibition-arbitrum.s3.amazonaws.com/" + token_id + ".png"
                response_code = 404
                wait_time = 60
                while response_code != 200 and wait_time > 0:
                    response = requests.get(image_url, headers=headers)
                    response_code = response.status_code
                    await asyncio.sleep(60)
                    wait_time -= 1
                owner_address = data['tokens'][0]['token']['owner']
                #Get info on the current owner
                owner_handle, owner_profile = await getUser(owner_address)
                embed = discord.Embed(title=f"{token_name} by {token_artist}", description=f"{token_name} received a {offer_price} {offer_symbol} offer at <t:{timestamp}:f>.\n\n**Offer Maker:**\n[{maker_handle}]({maker_profile})\n\n**Current Owner:**\n[{owner_handle}]({owner_profile})\n\nhttps://prohibition.art/token/{token_id}")
                embed.set_image(url=image_url)
                await listings_channel.send(embed=embed)
            #Update our latest event so we know where we left off for next time
            command = "update globalvariables set value = '{0}' where name = 'prohibition_latest_offer_id'".format(latest_offer_id)
            cur.execute(command)
            conn.commit()
            await asyncio.sleep(1)
            #We'll pause for a second so we don't get rate limited

        #Go through our list in reverse order so that we post the oldest events first
        for i in reversed(listings):
            token_id = i['criteria']['data']['token']['tokenId']
            #Get info on the current owner
            maker = i['maker']
            maker_handle, maker_profile = await getUser(maker)
            #Get info on the listing
            listing_price = i['price']['amount']['decimal']
            listing_symbol = i['price']['currency']['symbol']
            latest_listing_id = i['id']
            timestamp_str = i['createdAt']
            timestamp_dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            timestamp = int(timestamp_dt.timestamp())
            #Get info on the token
            url = "https://api-arbitrum.reservoir.tools/tokens/v6?tokens=0x47a91457a3a1f700097199fd63c039c4784384ab%3A"+token_id
            response = requests.get(url, headers=headers)
            data = json.loads(response.text)
            if data['tokens'] == []:
                continue
            collection_name = data['tokens'][0]['token']['collection']['name']
            token_name, token_artist = collection_name.rsplit(" by ", 1)
            if token_id[-6:].lstrip('0') == "":
                token_name = token_name + " #0"
            else:
                token_name = token_name + " #"+ token_id[-6:].lstrip('0')
            image_url = "https://prohibition-arbitrum.s3.amazonaws.com/" + token_id + ".png"
            response_code = 404
            wait_time = 60
            while response_code != 200 and wait_time > 0:
                response = requests.get(image_url, headers=headers)
                response_code = response.status_code
                await asyncio.sleep(60)
                wait_time -= 1
            owner_address = data['tokens'][0]['token']['owner']
            #Get info on the current owner
            owner_handle, owner_profile = await getUser(owner_address)
            embed = discord.Embed(title=f"{token_name} by {token_artist}", description=f"{token_name} was listed for sale at <t:{timestamp}:f>.\n\n**Price:**\n{listing_price} {listing_symbol}\n\n**Owner:**\n[{owner_handle}]({owner_profile})\n\nhttps://prohibition.art/token/{token_id}")
            embed.set_image(url=image_url)
            await listings_channel.send(embed=embed)
            #Update our latest event so we know where we left off for next time
            command = "update globalvariables set value = '{0}' where name = 'prohibition_latest_listing_id'".format(latest_listing_id)
            cur.execute(command)
            conn.commit()
            await asyncio.sleep(1)
            #We'll pause for a second so we don't get rate limited

        cur.close()
        conn.commit()
        conn.close()

    #If an error occurs, we're gonna log it and pause for a minute, then try again
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        print(f"An error occurred: {e} at line {line_number}")
        await asyncio.sleep(60)

bot.run(BOT_TOKEN)