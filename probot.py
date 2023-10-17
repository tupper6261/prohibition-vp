import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Select
from discord.commands import Option, OptionChoice
import os
from dotenv import load_dotenv
import asyncio
from web3 import Web3, HTTPProvider
from datetime import datetime, timedelta
import requests
import psycopg2
import json
import time
import sys
import base64
import random
from PIL import Image
from io import BytesIO

load_dotenv()

DATABASE_TOKEN = os.getenv('DATABASE_TOKEN')
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
ALCHEMY_MAINNET_API_KEY = os.getenv('ALCHEMY_MAINNET_API_KEY')
RESERVOIR_API_KEY = os.getenv('RESERVOIR_API_KEY')
VP_RESERVOIR_API_KEY = os.getenv('VP_RESERVOIR_API_KEY')
OPENSEA_API_KEY = os.getenv('OPENSEA_API_KEY')
ARBISCAN_API_KEY = os.environ.get('ARBISCAN_API_KEY')

prohibitionContract = "0x47A91457a3a1f700097199Fd63c039c4784384aB"

PROHIBITION_GUILD_ID = 1101580614945222708
ARTIST_VERIFICATION_CATEGORY_ID = 1151907551529664593
VERIFIED_ARTIST_ROLE_ID = 1151597107225043036
VERIFIED_ROLE_ID = 1101595354085990560
PROHIBITION_TEAM_ROLE_ID = 1101586848213651556

#Setting contants for verification voting here so they can be easily updated in the future
'''
Acceptance Criteria

- A simple majority determines if a vote passes or fails
    - More than 50% in favor passes the motion
    - More than 50% in opposition denies the motion
- The motion fails if less than 10% of verified artists vote
- The maximum duration is 1 week
- The minimum duration is 48 hours
- The vote fails if there is a tie
'''
VERIFICATION_ACCEPTANCE_CRITERIA = "**Acceptance Criteria:**\n- A simple majority determines if a vote passes or fails\n - More than 50% in favor passes the motion\n - More than 50% in opposition denies the motion\n- The motion fails if less than 10% of verified artists vote\n- The maximum duration is 1 week\n- The minimum duration is 48 hours\n- The vote fails if there is a tie"
VERIFICATION_MAJORITY = .5
VERIFICATION_MAJORITY_STRING = "50%"
VERIFICATION_QUORUM = .1
VERIFICATION_QUORUM_STRING = "10%"
VERIFICATION_MINIMUM_VOTE_DURATION_STRING = "48 hours"
VERIFICATION_MINIMUM_VOTE_DURATION = 172800 #48 hours --> 172800 seconds
VERIFICATION_MAXIMUM_VOTE_DURATION_STRING = "1 week"
VERIFICATION_MAXIMUM_VOTE_DURATION = 604800 #1 week --> 604800 seconds

DELETE_LINKS = False

UPDATE_LOOP = True

response = requests.get(requests.get("https://api.arbiscan.io/api?module=contract&action=getabi&address=" + prohibitionContract + "&apikey=" + ARBISCAN_API_KEY))
PROHIBITION_CONTRACT_ABI = response.text

PROHIBITION_PROJECT_NAMES = ["testing1", "testing2"]
PROHIBITION_ARTISTS = []


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

class VoteView(discord.ui.View):  # Create a class called MyView that subclasses discord.ui.View
    def __init__(self):
        super().__init__(timeout=None)  # timeout of the view must be set to None

    @discord.ui.button(label="Vote For", style=discord.ButtonStyle.primary)  # Create a button with the label "Vote For" with color Blurple
    async def vote_for_button_callback(self, button, interaction):
        verified_artist_role = discord.utils.get(interaction.guild.roles, id=VERIFIED_ARTIST_ROLE_ID)
        verified_artist_role_members = [member for member in interaction.guild.members if verified_artist_role in member.roles]
        verified_artist_role_member_count = len(verified_artist_role_members)
        if verified_artist_role in interaction.user.roles:
            message_id = interaction.message.id  # Get the message ID

            conn = psycopg2.connect(DATABASE_TOKEN, sslmode='require')
            cur = conn.cursor()
            cur.execute("select * from prohibition_verification_voting_channels where message_id = {0}".format(message_id))
            results = cur.fetchall()
            vote_id = results[0][0]
            #add the vote to the vote log
            cur.execute("insert into prohibition_verification_vote_log (vote_id, discord_user_id, approved, vote_timestamp) values ({0}, {1}, true, {2})".format(vote_id, interaction.user.id, int(time.time())))
            conn.commit()
            #either add the user to the vote_summary table or edit their response
            cur.execute("select * from prohibition_verification_vote_summary where vote_id = {0} and discord_user_id = {1}".format(vote_id, interaction.user.id))
            results = cur.fetchall()
            if results == []:
                cur.execute("insert into prohibition_verification_vote_summary (vote_id, discord_user_id, approved) values ({0}, {1}, true)".format(vote_id, interaction.user.id))
                conn.commit()
            else:
                cur.execute("update prohibition_verification_vote_summary set approved = true where vote_id = {0} and discord_user_id = {1}".format(vote_id, interaction.user.id))
                conn.commit()
            cur.close()
            conn.commit()
            conn.close()

            # Edit the original message
            message_content, is_vote_finished = await updateVoteMessage(vote_id, verified_artist_role_member_count)
            embed = discord.Embed(description=message_content)
            if is_vote_finished:
                await interaction.response.edit_message(view = None, embed = embed)
                await interaction.channel.send("<@&1101586848213651556>, this vote has ended.")
            else:
                await interaction.response.edit_message(embed = embed)
        else:
            await interaction.response.send_message("Only currently-verified artists are allowed to vote; this vote has not been recorded. If you feel you are receiving this message in error, please <#1101604838137143406> and we'll get back with you ASAP!", ephemeral=True)

    @discord.ui.button(label="Vote Against", style=discord.ButtonStyle.primary)  # Create a button with the label "Vote Against" with color Blurple
    async def vote_against_button_callback(self, button, interaction):
        verified_artist_role = discord.utils.get(interaction.guild.roles, id=VERIFIED_ARTIST_ROLE_ID)
        verified_artist_role_members = [member for member in interaction.guild.members if verified_artist_role in member.roles]
        verified_artist_role_member_count = len(verified_artist_role_members)
        if verified_artist_role in interaction.user.roles:
            message_id = interaction.message.id  # Get the message ID

            conn = psycopg2.connect(DATABASE_TOKEN, sslmode='require')
            cur = conn.cursor()
            cur.execute("select * from prohibition_verification_voting_channels where message_id = {0}".format(message_id))
            results = cur.fetchall()
            vote_id = results[0][0]
            #add the vote to the vote log
            cur.execute("insert into prohibition_verification_vote_log (vote_id, discord_user_id, approved, vote_timestamp) values ({0}, {1}, false, {2})".format(vote_id, interaction.user.id, int(time.time())))
            conn.commit()
            #either add the user to the vote_summary table or edit their response
            cur.execute("select * from prohibition_verification_vote_summary where vote_id = {0} and discord_user_id = {1}".format(vote_id, interaction.user.id))
            results = cur.fetchall()
            if results == []:
                cur.execute("insert into prohibition_verification_vote_summary (vote_id, discord_user_id, approved) values ({0}, {1}, false)".format(vote_id, interaction.user.id))
                conn.commit()
            else:
                cur.execute("update prohibition_verification_vote_summary set approved = false where vote_id = {0} and discord_user_id = {1}".format(vote_id, interaction.user.id))
                conn.commit()
            cur.close()
            conn.commit()
            conn.close()

            # Edit the original message
            message_content, is_vote_finished = await updateVoteMessage(vote_id, verified_artist_role_member_count)
            embed = discord.Embed(description=message_content)
            if is_vote_finished:
                await interaction.response.edit_message(view = None, embed = embed)
                await interaction.channel.send("<@&1101586848213651556>, this vote has ended.")
            else:
                await interaction.response.edit_message(embed = embed)
        else:
            await interaction.response.send_message("Only currently-verified artists are allowed to vote; this vote has not been recorded. If you feel you are receiving this message in error, please <#1101604838137143406> and we'll get back with you ASAP!", ephemeral=True)

@bot.event
async def on_ready():
    global UPDATE_LOOP
    if UPDATE_LOOP:
        UPDATE_LOOP = False
        await updateLoop()

async def updateLoop():
    await updateRoles()
    while True:
        await updateVotes()
        await updateProjects()
        await track()
        await updateCalendar()
        await asyncio.sleep(300)

async def updateRoles():
    guild = discord.utils.get(bot.guilds, id=PROHIBITION_GUILD_ID)
    channel = discord.utils.get(guild.channels, id=1129038551066103959)
    #Role message
    message_id = 1129129885928005874
    message = await channel.fetch_message(message_id)
    await message.edit(content="Tap the below buttons to add/remove the corresponding role:", view=MyView())

async def updateProjects():
    try:
        #Get the prohibition contract ABI
        global PROHIBITION_CONTRACT_ABI
        global PROHIBITION_ARTISTS
        global PROHIBITION_PROJECT_NAMES

        #Connect to alchemy
        w3 = Web3(HTTPProvider('https://arb-mainnet.g.alchemy.com/v2/'+ALCHEMY_MAINNET_API_KEY))

        #Load the prohibition contract
        contract = w3.eth.contract(address=prohibitionContract, abi=PROHIBITION_CONTRACT_ABI)

        #See how many projects currently exist
        nextProjectId = contract.functions.nextProjectId().call()

        #Connect to Postgres
        conn = psycopg2.connect(DATABASE_TOKEN, sslmode='require')
        cur = conn.cursor()

        PROHIBITION_ARTISTS = []
        PROHIBITION_PROJECT_NAMES = []

        #Go through all the existing projects
        for projectID in range(0,nextProjectId):
            #Grab some pertinent info from the projectStateData function
            result = contract.functions.projectStateData(projectID).call()
            #Extract the returned values
            invocations, maxInvocations, active, paused, completedTimestamp, locked = result
            #If the project isn't active, we don't need to worry about it
            if active:
                #Grab some more info from the projectDetails function
                result = contract.functions.projectDetails(projectID).call()
                #Extract the returned values
                projectName, artist, description, website, license = result
                #Get the prohibition minter contract address
                minterContractAddress = contract.functions.minterContract().call()
                #Get the minter contract ABI
                response = requests.get("https://api.arbiscan.io/api?module=contract&action=getabi&address=" + minterContractAddress + "&apikey=" + ARBISCAN_API_KEY)
                minterContractABI = json.loads(response.text)['result']
                #Load the minter contract
                minterContract = w3.eth.contract(address=minterContractAddress, abi=minterContractABI)
                #Now get this specific project's minter contract address
                projectMinterContractAddress = minterContract.functions.getMinterForProject(projectID).call()
                #Get the project's minter contract ABI
                response = requests.get("https://api.arbiscan.io/api?module=contract&action=getabi&address=" + projectMinterContractAddress + "&apikey=" + ARBISCAN_API_KEY)
                projectMinterContractABI = json.loads(response.text)['result']
                #Load the project's minter contract
                projectMinterContract = w3.eth.contract(address=projectMinterContractAddress, abi=projectMinterContractABI)
                #Get a few more pieces of info from the getPriceInfo function on the minter contract
                result = projectMinterContract.functions.getPriceInfo(projectID).call()
                #Extract the returned values
                isConfigured, tokenPriceInWei, currencySymbol, currencyAddress = result
                #Convert the token price into standard readable format
                readableTokenPrice = float(tokenPriceInWei)/1000000000000000000
                #Set the project url and image url
                projectImage = "https://prohibition-arbitrum.s3.amazonaws.com/" + str(projectID * 1000000) + ".png"
                url = "https://prohibition.art/api/project/0x47A91457a3a1f700097199Fd63c039c4784384aB-"+str(projectID)
                response = requests.get(url)
                #Make sure the project exists on the prohibition platform
                if response.text == '{"code":"NOT_FOUND","error":"Project not found"}':
                    continue
                data = json.loads(response.text)
                projectURL = "https://prohibition.art/project/" + data['slug']

                #See if there are still tokens available to mint
                stillMinting = True
                if invocations >= maxInvocations:
                    stillMinting = False
                #Upsert the SQL table
                cur.execute("""
                    INSERT INTO prohibition_projects (
                        project_ID, 
                        is_active, 
                        invocations, 
                        max_invocations, 
                        project_name, 
                        project_artist, 
                        minter_contract, 
                        project_price, 
                        project_image, 
                        project_url
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (project_ID) 
                    DO UPDATE SET 
                        is_active = EXCLUDED.is_active,
                        invocations = EXCLUDED.invocations,
                        max_invocations = EXCLUDED.max_invocations,
                        project_name = EXCLUDED.project_name,
                        project_artist = EXCLUDED.project_artist,
                        minter_contract = EXCLUDED.minter_contract,
                        project_price = EXCLUDED.project_price,
                        project_image = EXCLUDED.project_image,
                        project_url = EXCLUDED.project_url;
                """, (projectID, stillMinting, invocations, maxInvocations, projectName, artist, projectMinterContractAddress, readableTokenPrice, projectImage, projectURL))
                conn.commit()

                PROHIBITION_PROJECT_NAMES.append(projectName)
                PROHIBITION_ARTISTS.append(artist)
                
        cur.close()
        conn.commit()
        conn.close()   
    #If an error occurs, we're gonna log it and pause for a minute, then try again
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        print(f"An error occurred: {e} at line {line_number}")
        await asyncio.sleep(60)

async def updateVotes():
    #Get the current active votes
    conn = psycopg2.connect(DATABASE_TOKEN, sslmode='require')
    cur = conn.cursor()
    cur.execute("SELECT * FROM prohibition_verification_voting_channels WHERE active_vote = true")
    results = cur.fetchall()
    cur.close()
    conn.commit()
    conn.close()
    guild = discord.utils.get(bot.guilds, id=PROHIBITION_GUILD_ID)
    verified_artist_role = discord.utils.get(guild.roles, id=VERIFIED_ARTIST_ROLE_ID)
    verified_artist_role_members = [member for member in guild.members if verified_artist_role in member.roles]
    verified_artist_role_member_count = len(verified_artist_role_members)
    for vote in results:
        channel = discord.utils.get(guild.channels, id=vote[2])
        message = await channel.fetch_message(vote[3])
        message_content, is_vote_finished = await updateVoteMessage(vote[0], verified_artist_role_member_count)
        embed = discord.Embed(description=message_content)
        if is_vote_finished:
            await message.edit(view = None, embed = embed)
            await channel.send("<@&1101586848213651556>, this vote has ended.")
        else:
            await message.edit(view = VoteView(), embed = embed)

async def updateVoteMessage(vote_id, number_of_verified_artists):
    #Get the current vote stats
    conn = psycopg2.connect(DATABASE_TOKEN, sslmode='require')
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM prohibition_verification_vote_summary WHERE approved = true and vote_id = {0}".format(vote_id))
    votes_for = cur.fetchall()[0][0]
    cur.execute("SELECT COUNT(*) FROM prohibition_verification_vote_summary WHERE approved = false and vote_id = {0}".format(vote_id))
    votes_against = cur.fetchall()[0][0]
    cur.execute("SELECT * FROM prohibition_verification_voting_channels WHERE vote_id = {0}".format(vote_id))
    results = cur.fetchall()
    earliest_vote_end = results[0][4]
    latest_vote_end = results[0][5]
    cur.close()
    conn.commit()
    conn.close()

    #Get the current timestamp
    current_time = int(time.time())
    #See if the minimum vote time has passed
    if earliest_vote_end > current_time:
        minimum_duration_reached = False
    else:
        minimum_duration_reached = True
    #See if the maximum vote time has passed
    if latest_vote_end > current_time:
        maximum_duration_reached = False
    else:
        maximum_duration_reached =True
    #See if a quorum has been reached
    total_vote_percent = round(((float(votes_for) + float(votes_against))/float(number_of_verified_artists)), 4)
    if total_vote_percent < VERIFICATION_QUORUM:
        quorum_reached = False
    else:
        quorum_reached = True
    #See if a majority vote has been reached
    votes_for_percent = round((float(votes_for)/float(number_of_verified_artists)), 4)
    votes_against_percent = round((float(votes_against)/float(number_of_verified_artists)), 4)
    if votes_for_percent > VERIFICATION_MAJORITY or votes_against_percent > VERIFICATION_MAJORITY:
        majority_vote_reached = True
    else:
        majority_vote_reached = False

    #Different vote states get different messages
    if not minimum_duration_reached:
        is_vote_finished = False
        message_content = "\n\n**Current Vote Status:**"
        message_content += "\n{0} votes for".format(votes_for)
        message_content += "\n{0} votes against".format(votes_against)
        message_content += "\n{0}% of Verified Artists have voted - a quorum has ".format(str(round(total_vote_percent*100,2)))
        if not quorum_reached:
            message_content += "not "
        message_content += "been reached"
        message_content += "\nVote will close no earlier than <t:" + str(earliest_vote_end) + ":f>"
        message_content += "\nVote will continue until a " + VERIFICATION_MAJORITY_STRING + " majority has been reached or until <t:" + str(latest_vote_end) + ":f>, whichever is earlier"
    else:
        if majority_vote_reached:
            is_vote_finished = True
            message_content = "\n\n**Vote Results:**"
            conn = psycopg2.connect(DATABASE_TOKEN, sslmode='require')
            cur = conn.cursor()
            if votes_for > votes_against:
                message_content = "\n\nApplication for verification was approved by majority vote on <t:" + str(current_time) + ":f>."
                cur.execute("update prohibition_verification_voting_channels set active_vote = false and getting_verified = true where vote_id = {0}".format(vote_id))
            else:
                message_content = "\n\nApplication for verification was denied by majority vote on <t:" + str(current_time) + ":f>."
                cur.execute("update prohibition_verification_voting_channels set active_vote = false and getting_verified = false where vote_id = {0}".format(vote_id))
            conn.commit()
            cur.close()
            conn.close()
        else:
            if maximum_duration_reached:
                is_vote_finished = True
                message_content = "\n\n**Vote Results:**"
                conn = psycopg2.connect(DATABASE_TOKEN, sslmode='require')
                cur = conn.cursor()
                if quorum_reached:
                    if votes_for > votes_against:
                        message_content = "\n\nApplication for verification was approved by quorum majority vote after reaching maximum vote duration on <t:" + str(current_time) + ":f>."
                        cur.execute("update prohibition_verification_voting_channels set active_vote = false and getting_verified = true where vote_id = {0}".format(vote_id))
                    else:
                        message_content = "\n\nApplication for verification was denied by quorum majority vote after reaching maximum vote duration on <t:" + str(current_time) + ":f>."
                        cur.execute("update prohibition_verification_voting_channels set active_vote = false and getting_verified = false where vote_id = {0}".format(vote_id))
                else:
                    message_content = "\n\nApplication for verification was denied after reaching maximum vote duration on <t:" + str(current_time) + ":f> without meeting a quorum."
                    cur.execute("update prohibition_verification_voting_channels set active_vote = false and getting_verified = false where vote_id = {0}".format(vote_id))
                conn.commit()
                cur.close()
                conn.close()
            else:
                is_vote_finished = False
                message_content = "\n\n**Current Vote Status:**"
                message_content += "\n{0} votes for".format(votes_for)
                message_content += "\n{0} votes against".format(votes_against)
                message_content += "\n{0}% of Verified Artists have voted - a quorum has ".format(str(round(total_vote_percent*100,2)))
                if not quorum_reached:
                    message_content += "not "
                message_content += "been reached"
                message_content += "\n" + VERIFICATION_MINIMUM_VOTE_DURATION_STRING + " minimum vote time has elapsed."
                message_content += "\nVote will continue until a " + VERIFICATION_MAJORITY_STRING + " majority has been reached or until <t:" + str(latest_vote_end) + ":f>, whichever is earlier"
    
    return message_content, is_vote_finished

#Slash command to display an iteration from a specified project
@bot.slash_command(guild_ids=[PROHIBITION_GUILD_ID], description="Display an iteration of a minted project")
async def project(ctx, projectname: discord.Option(str, autocomplete = discord.utils.basic_autocomplete(PROHIBITION_PROJECT_NAMES))):
    await ctx.respond("This command isn't ready yet!\n\nBut you're working with " + projectname, ephemeral = True)
    return

#Slash command to discover a prohibition project
@bot.slash_command(guild_ids=[PROHIBITION_GUILD_ID], description="Discover a new project on the Prohibition platform")
async def discover(ctx, active: discord.Option(str, "Show a random iteration of an actively-minting project, or from any project?", choices = ["Only Active Projects", "Any Project"]) = "Any Project"):
    conn = psycopg2.connect(DATABASE_TOKEN, sslmode='require')
    cur = conn.cursor()
    if active == "Only Active Projects":
        cur.execute("select * from prohibition_projects where is_active = true")
    else:
        cur.execute("select * from prohibition_projects")
    projects = cur.fetchall()
    cur.close()
    conn.close()

    project = random.randint(0,len(projects))
    project = projects[project]
    projectID = project[0]
    projectInvocations = project[2]
    projectMaxInvocations = project[3]
    projectName =  project[4]
    projectArtist = project[5]
    projectMinterContract = project[6]
    projectPrice = project[7]
    projectImage = project[8]
    projectURL = project[9]

    invocation = random.randint(0,projectInvocations)
    tokenID = projectID * 1000000 + invocation
    invocationURL = projectURL + "/token/" + str(invocation)
    invocationImage = "https://prohibition-arbitrum.s3.amazonaws.com/" + str(tokenID) + ".png"
    print (invocationImage)

    #[Display](URL)
    embed = discord.Embed(title=f"{projectName} by {projectArtist}", description=f"\n**Project Price:** {projectPrice} ETH\n**Minted:** {projectInvocations} / {projectMaxInvocations}\n\n[Invocation #{str(invocation)}]({invocationURL})")
    embed.set_image(url=invocationImage)

    await ctx.respond(embed = embed)

    return

#Slash command to start a new artist verification vote
@bot.slash_command(guild_ids=[PROHIBITION_GUILD_ID], description="Start a new artist verification vote")
async def artistverificationvote(ctx, walletaddress: Option(str, "What is the applicant's wallet address?"), discordusername: Option(discord.Member, "What is the Discord account of the user applying for verification?")=None, xhandle: Option(str, "What is the X handle (without the @) of the user applying for verification?")=None, ighandle: Option(str, "What is the Instagram handle (without the @) of the user applying for verification?")=None, website: Option(str, "What is the applicant's website?")=None):
    guild = discord.utils.get(bot.guilds, id=PROHIBITION_GUILD_ID)
    forum_channel = guild.get_channel(1154132908714496070)
    bot_member = guild.me
    artist_prohibition_handle, artist_prohibition_profile = await getUser(walletaddress)

    vote_begin = int(time.time())
    earliest_vote_end = vote_begin + VERIFICATION_MINIMUM_VOTE_DURATION
    latest_vote_end = vote_begin + VERIFICATION_MAXIMUM_VOTE_DURATION
    
    # Get today's date in the format dateMonthYear
    todays_date = datetime.now().strftime('%d%b%Y')

    '''

    #Create discussion forum thread
    discussion_forum_name = artist_prohibition_handle + " verification discussion"
    discussion_forum_content = "Feel free to discuss the details of " + artist_prohibition_handle + "'s verification request"

    await forum_channel.create_thread(name = discussion_forum_name, content = discussion_forum_content)
    '''

    channel_name = "vote-" + artist_prohibition_handle + "-" + todays_date

    # Define the roles
    default_role = guild.default_role
    verified_role = discord.utils.get(guild.roles, id=VERIFIED_ROLE_ID)
    prohibition_team_role = discord.utils.get(guild.roles, id=PROHIBITION_TEAM_ROLE_ID)

    # Set the overwrites
    overwrites = {
        default_role: discord.PermissionOverwrite(read_messages=False),
        verified_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
        prohibition_team_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        bot_member: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
    }

    # Create the channel
    channel = await guild.create_text_channel(
        name=channel_name,
        category=guild.get_channel(ARTIST_VERIFICATION_CATEGORY_ID),
        overwrites=overwrites
    )

    message_title = artist_prohibition_handle + " Verification Vote"
    message_content = artist_prohibition_handle + " is applying to be a verified artist on the Prohibition platform. Please review their work, accounts, and wallet history below and submit your vote before the deadline.\n\n**Prohibition Profile:** " + artist_prohibition_profile
    message_content += "\n**Wallet Address: **" + walletaddress
    message_content += "\n**Arbiscan Transaction History: **[" + walletaddress[:5] + "..." + walletaddress[len(walletaddress)-5:] + "](https://arbiscan.io/address/" + walletaddress + ")"
    message_content += "\n**Etherscan Transaction History: **[" + walletaddress[:5] + "..." + walletaddress[len(walletaddress)-5:] + "](https://etherscan.io/address/" + walletaddress + ")"
    if discordusername:
        message_content += "\n**Discord Account: **" + discordusername.mention
    if xhandle:
        message_content += "\n**X Profile: **[" + xhandle + "](https://twitter.com/" + xhandle +")"
    if ighandle:
        message_content += "\n**Instagram Profile: **[" + ighandle + "](https://instagram.com/" + ighandle +")"
    if website:
        message_content += "\n**Personal Website: **" + website

    embed = discord.Embed(title=message_title, description=message_content)

    info_message = await channel.send(embed = embed)
    
    message_content = VERIFICATION_ACCEPTANCE_CRITERIA

    embed = discord.Embed(description=message_content)

    verification_acceptance_criteria_message = await channel.send(embed = embed)

    message_content = "\n\n**Current Vote Status:**"
    message_content += "\n0 votes for"
    message_content += "\n0 votes against"
    message_content += "\n0% of Verified Artists have voted"
    message_content += "\nVote will close no earlier than <t:" + str(earliest_vote_end) + ":f>"
    message_content += "\nVote will continue until a " + VERIFICATION_MAJORITY_STRING + " majority has been reached or until <t:" + str(latest_vote_end) + ":f>, whichever is earlier"

    embed = discord.Embed(description=message_content)

    voting_message = await channel.send(embed = embed, view = VoteView())

    ping_message = await channel.send("<@&" + str(VERIFIED_ARTIST_ROLE_ID) + ">, there is a new verified artist vote for your review :point_up_2:")

    conn = psycopg2.connect(DATABASE_TOKEN, sslmode='require')
    cur = conn.cursor()
    cur.execute("insert into prohibition_verification_voting_channels (vote_id, artist_wallet, channel_id, message_id, minimum_vote_time, maximum_vote_time) values ({0}, '{1}', {2}, {3}, {4}, {5})".format(vote_begin, walletaddress, channel.id, voting_message.id, earliest_vote_end, latest_vote_end))
    conn.commit()
    cur.close()
    conn.close()

    await ctx.respond("Vote for " + artist_prohibition_handle + " has been successfully created.", ephemeral = True)


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

async def updateCalendar():
    try:
        headers = {
            "accept": "*/*",
            "content-type": "application/json"
        }

        events = []
        projectID = 0
        response_code = 200
        response_404 = 0
        while response_404 < 5:
            url = "https://prohibition.art/api/project/0x47A91457a3a1f700097199Fd63c039c4784384aB-"+str(projectID)
            response = requests.get(url, headers=headers)
            data = json.loads(response.text)
            response_code = response.status_code
            if response_code != 404:
                response_404 = 0
                date = data['startTime']
                if date == None:
                    date = data['auctionStartTime']
                if date != None:
                    datetimeDate = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")
                    date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")
                    date = int(date.timestamp())
                    currentTime = int(time.time())
                    if date > currentTime:
                        events.append((data, projectID, datetimeDate, date))
            else:
                response_404 += 1
            projectID += 1

        for event in events:
            image_url = "https://prohibition-arbitrum.s3.amazonaws.com/" + str(event[1] * 1000000) + ".png"
            response_image = requests.get(image_url)
            image = Image.open(BytesIO(response_image.content))
            # Compress the image
            buffered = BytesIO()
            compression = 100
            image.save(buffered, format="PNG", optimize=True, quality=compression)  # You can adjust the quality as needed
            # Convert the compressed image to base64
            image_base64 = base64.b64encode(buffered.getvalue())
            image_size_kb = (len(image_base64) * 3 / 4) / 1024
            
            while image_size_kb > 10240 and compression > 0:
                compression -= 10
                buffered.seek(0)  # Reset the buffer position
                buffered.truncate()  # Clear the buffer content
                #remove the alpha channel and save as jpeg to make the image smaller 
                if image.mode == 'RGBA':
                    image = image.convert("RGB")
                image.save(buffered, format="JPEG", quality=compression)
                image_base64 = base64.b64encode(buffered.getvalue())
                image_size_kb = (len(image_base64) * 3 / 4) / 1024
                print(image_size_kb)

            projectName = event[0]['name']
            projectArtist = event[0]['artistName']
            projectDescription = event[0]['description']
            projectURL = "https://prohibition.art/project/" + event[0]['slug']
            conn = psycopg2.connect(DATABASE_TOKEN, sslmode='require')
            cur = conn.cursor()
            cur.execute("select * from prohibitionupcomingprojects where project_ID = {}".format(event[1]))
            results = cur.fetchall()
            if results == []:
                DISCORD_API_ENDPOINT = "https://discord.com/api/v10/guilds/1101580614945222708/scheduled-events"

                start_time = event[2].isoformat()
                end_time = (event[2] + timedelta(hours=1)).isoformat()

                payload = {
                    "name": projectName + " by " + projectArtist,
                    "entity_type": 3,  # External Event
                    "scheduled_start_time": start_time,
                    "scheduled_end_time": (event[2] + timedelta(hours=1)).isoformat(),
                    "entity_metadata": {"location": projectURL},
                    "privacy_level": 2, #Private to guild members
                    "image": "data:image/png;base64," + image_base64.decode('utf-8'),
                }

                headers = {
                    "Authorization": f"Bot {BOT_TOKEN}",
                    "Content-Type": "application/json"
                }
                response = requests.post(DISCORD_API_ENDPOINT, json=payload, headers=headers)
                data = json.loads(response.text)

                if response.status_code == 200:
                    cur.execute("insert into prohibitionupcomingprojects (project_ID, discord_event_id, release_timestamp) values ({0}, {1}, {2})".format(event[1], int(data['id']), event[3]))
                    conn.commit()
                else:
                    print(f"Failed to create event '{projectName}'. Reason: {response.text}")
                    
            else:
                if results[0][2] != event[2]:
                    cur.execute("update prohibitionupcomingprojects set release_timestamp = {0} where project_ID = {1}".format(event[3], event[1]))
                    conn.commit()
            cur.close()
            conn.commit()
            conn.close()
    #If an error occurs, we're gonna log it and pause for a minute, then try again
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        print(f"An error occurred: {e} at line {line_number}")
        await asyncio.sleep(60)

async def track():
    try:
        #Get our discord server and channels
        guild = discord.utils.get(bot.guilds, id=1101580614945222708)
        mint_channel = discord.utils.get(guild.channels, id=1126976550508712106)
        sales_channel = discord.utils.get(guild.channels, id=1126976977199435786)
        listings_channel = discord.utils.get(guild.channels, id=1126977037765189752)
        offers_channel = discord.utils.get(guild.channels, id=1145743548923265195)
        hc_mint_channel = discord.utils.get(guild.channels, id=1143961800690385016)
        hc_sales_channel = discord.utils.get(guild.channels, id=1145743594217537536)
        hc_listings_channel = discord.utils.get(guild.channels, id=1145743631580418119)
        hc_offers_channel = discord.utils.get(guild.channels, id=1145743668972630067)

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

        refreshHeaders = {
            "accept": "*/*",
            "content-type": "application/json",
            "x-api-key": RESERVOIR_API_KEY
        }

        OSheaders = {
            "accept": "application/json",
            "X-API-KEY": OPENSEA_API_KEY
        }

        mint_exit_flag = False
        sale_exit_flag = False
        continuation = ''

        #'Continuation' refers to pagination within the API responses
        while continuation != None and not (mint_exit_flag and sale_exit_flag):
            #Check if we've been rate limited, and if so, wait 5 seconds and try again
            while True:
                #If it's our first time through the loop, we leave off the continuation param
                if continuation == '':
                    url = "https://api-arbitrum.reservoir.tools/transfers/v3?contract=0x47A91457a3a1f700097199Fd63c039c4784384aB&limit=100"
                else:
                    url = "https://api-arbitrum.reservoir.tools/transfers/v3?contract=0x47A91457a3a1f700097199Fd63c039c4784384aB&limit=100&continuation="+continuation
                response = requests.get(url, headers=headers)
                await asyncio.sleep(1)
                data = json.loads(response.text)
                response_code = response.status_code
                if response_code == 429:
                    await asyncio.sleep(5)
                else:
                    break
            

            #Go through all the transfers on the contract looking for ones coming from the 0x0 address (mint events)
            for i in data['transfers']:
                if i['price'] == None and i['from'] == '0x0000000000000000000000000000000000000000':
                    mint_hash = i['txHash']
                    #Once we reach the last one we posted, we can stop calling the API and stop adding the events to our list
                    if mint_hash == latest_mint_hash:
                        mint_exit_flag = True
                    else:
                        if not mint_exit_flag:
                            mints.append(i)
                if i['price'] != None:
                    sale_hash = i['txHash']
                    #Once we reach the last one we posted, we can stop calling the API and stop adding the events to our list
                    if sale_hash == latest_sale_hash:
                        sale_exit_flag = True
                    else:
                        if not sale_exit_flag:
                            sales.append(i)

            continuation = data['continuation']

        exit_flag = False
        continuation = ''

        #'Continuation' refers to pagination within the API responses
        while continuation != None and not exit_flag:
            #Check if we've been rate limited, and if so, wait 5 seconds and try again
            while True:
                #If it's our first time through the loop, we leave off the continuation param
                if continuation == '':
                    url = "https://api-arbitrum.reservoir.tools/orders/bids/v6?contracts=0x47A91457a3a1f700097199Fd63c039c4784384aB"
                else:
                    url = "https://api-arbitrum.reservoir.tools/orders/bids/v6?contracts=0x47A91457a3a1f700097199Fd63c039c4784384aB&continuation="+continuation
                response = requests.get(url, headers=headers)
                await asyncio.sleep(1)
                data = json.loads(response.text)
                response_code = response.status_code
                if response_code == 429:
                    await asyncio.sleep(5)
                else:
                    break
            

            #Go through all the transfers on the contract looking for ones that have a price associated with them (sale events)
            for i in data['orders']:
                offer_id = i['id']
                #Once we reach the last one we posted, we can stop calling the API and stop adding the events to our list
                #Additionally, sometimes a bid seems to disappear from Reservoir's results. So if that happens to our latest listing, it ends up starting from the beginning of the contract.
                #So we're also going to limit the results to bids less than 60 minutes old. Which should still catch everything, but limit the amount of duplicates when that happens
                if offer_id == latest_offer_id or (i['originatedAt'] != None and ((datetime.utcnow() - datetime.strptime(i['originatedAt'], '%Y-%m-%dT%H:%M:%S.%fZ')) > timedelta(minutes = 60))):
                    exit_flag = True
                    break
                else:
                    #If we come across a canceled or fulfilled offer, we don't want to post that
                    if i['status'] == "active":
                        offers.append(i)

            continuation = data['continuation']

        exit_flag = False
        continuation = ''

        #'Continuation' refers to pagination within the API responses
        while continuation != None and not exit_flag:
            #Check if we've been rate limited, and if so, wait 5 seconds and try again
            while True:
                #If it's our first time through the loop, we leave off the continuation param
                if continuation == '':
                    url = "https://api-arbitrum.reservoir.tools/orders/asks/v5?contracts=0x47a91457a3a1f700097199fd63c039c4784384ab"
                else:
                    url = "https://api-arbitrum.reservoir.tools/orders/asks/v5?contracts=0x47a91457a3a1f700097199fd63c039c4784384ab&continuation="+continuation
                response = requests.get(url, headers=headers)
                await asyncio.sleep(1)
                data = json.loads(response.text)
                response_code = response.status_code
                if response_code == 429:
                    await asyncio.sleep(5)
                else:
                    break
            

            #Go through all the transfers on the contract looking for ones that have a price associated with them (sale events)
            for i in data['orders']:
                listing_id = i['id']
                #Once we reach the last one we posted, we can stop calling the API and stop adding the events to our list
                #Additionally, sometimes a listing seems to disappear from Reservoir's results. So if that happens to our latest listing, it ends up starting from the beginning of the contract.
                #So we're also going to limit the results to listings less than 60 minutes old. Which should still catch everything, but limit the amount of duplicates when that happens
                if listing_id == latest_listing_id or (i['originatedAt'] != None and ((datetime.utcnow() - datetime.strptime(i['originatedAt'], '%Y-%m-%dT%H:%M:%S.%fZ')) > timedelta(minutes = 60))):
                    exit_flag = True
                    break
                else:
                    #If we come across a canceled or fulfilled listing, we don't want to post that
                    if i['status'] == "active":
                        listings.append(i)

            continuation = data['continuation']

        conn = psycopg2.connect(DATABASE_TOKEN, sslmode='require')
        cur = conn.cursor()

        #Go through our list in reverse order so that we post the oldest events first
        for i in reversed(mints):
            #cur.execute("select * from prohibition_mints where id = '{0}'".format(i['txHash']))
            results = [] #cur.fetchall()
            if results == []:
                token_id = i['token']['tokenId']
                collection_id = int(int(token_id)/1000000)
                collection_name = i['token']['collection']['name']
                token_name, token_artist = collection_name.rsplit(" by ", 1)
                if token_id[-6:].lstrip('0') == "":
                    token_name = token_name + " #0"
                else:
                    token_name = token_name + " #"+ token_id[-6:].lstrip('0')
                timestamp = i['timestamp']
                image_url = "https://prohibition-arbitrum.s3.amazonaws.com/" + token_id + ".png"
                #the amount of time to wait for the render is 30 minutes and that timer starts at the time of mint
                wait_time = 1800 - (int(time.time()) - timestamp)
                #try to get the image url
                response = requests.get(image_url, headers=headers)
                response_code = response.status_code
                while response_code != 200 and wait_time > 0:
                    await asyncio.sleep(60)
                    response = requests.get(image_url, headers=headers)
                    response_code = response.status_code
                    wait_time -= 60
                
                #We're gonna wait at least 5 minutes from the mint time to refresh the metadata
                wait_time = 300 - (int(time.time()) - timestamp)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

                url = "https://api-arbitrum.reservoir.tools/tokens/refresh/v1"
                payload = {
                    "liquidityOnly": False,
                    "overrideCoolDown": False,
                    "token": "0x47A91457a3a1f700097199Fd63c039c4784384aB:" + token_id
                }
                #Check if we've been rate limited, and if so, wait 5 seconds and try again
                while True:
                    response = requests.post(url, json=payload, headers=refreshHeaders)
                    data = json.loads(response.text)
                    response_code = response.status_code
                    if response_code == 429:
                        await asyncio.sleep(5)
                    else:
                        break
                
                owner = i['to']
                owner_handle, owner_profile = await getUser(owner)
                latest_mint_hash = i['txHash']

                embed = discord.Embed(title=f"{token_name} by {token_artist}", description=f"{token_name} was minted by [{owner_handle}]({owner_profile}) at <t:{timestamp}:f>.\n\nhttps://prohibition.art/token/{token_id}")
                embed.set_image(url=image_url)
                #If this mint is from the H-C collection
                if collection_id == 100:
                    await hc_mint_channel.send(embed=embed)
                else:
                    await mint_channel.send(embed=embed)
                #Update our latest event so we know where we left off for next time
                command = "update globalvariables set value = '{0}' where name = 'prohibition_latest_mint_hash'".format(latest_mint_hash)
                cur.execute(command)
                conn.commit()
                #cur.execute("insert into prohibition_mints (id, timestamp) values ('{0}', {1})".format(i['txHash'], int(time.time())))
                #conn.commit()
                #Call the OpenSea refresh metadata endpoint and get the newly rendered image updated
                url = "https://api.opensea.io/v2/chain/arbitrum/contract/0x47A91457a3a1f700097199Fd63c039c4784384aB/nfts/" + token_id + "/refresh"
                response = requests.post(url, headers=OSheaders)
                await asyncio.sleep(1)
                #We'll pause for a second so we don't get rate limited
            else:
                break
            

        #Go through our list in reverse order so that we post the oldest events first
        for i in reversed(sales):
            #cur.execute("select * from prohibition_sales where id = '{0}'".format(i['txHash']))
            results = [] #cur.fetchall()
            if results == []:
                owner = i['to']
                owner_handle, owner_profile = await getUser(owner)
                seller = i['from']
                seller_handle, seller_profile = await getUser(seller)
                token_id = i['token']['tokenId']
                collection_id = int(int(token_id)/1000000)
                collection_name = i['token']['collection']['name']
                token_name, token_artist = collection_name.rsplit(" by ", 1)
                if token_id[-6:].lstrip('0') == "":
                    token_name = token_name + " #0"
                else:
                    token_name = token_name + " #"+ token_id[-6:].lstrip('0')
                image_url = "https://prohibition-arbitrum.s3.amazonaws.com/" + token_id + ".png"
                wait_time = 60
                #try to get the image url
                response = requests.get(image_url, headers=headers)
                response_code = response.status_code
                while response_code != 200 and wait_time > 0:
                    await asyncio.sleep(60)
                    response = requests.get(image_url, headers=headers)
                    response_code = response.status_code
                    wait_time -= 1
                timestamp = i['timestamp']
                price_symbol = i['price']['currency']['symbol']
                price_amount = i['price']['amount']['decimal']
                latest_sale_hash = i['txHash']
                embed = discord.Embed(title=f"{token_name} by {token_artist}", description=f"{token_name} sold for {price_amount} {price_symbol} at <t:{timestamp}:f>.\n\n**Buyer:**\n[{owner_handle}]({owner_profile})\n\n**Seller:**\n[{seller_handle}]({seller_profile})\n\nhttps://prohibition.art/token/{token_id}")
                embed.set_image(url=image_url)
                #If this is the h+c collection
                if collection_id == 100:
                    await hc_sales_channel.send(embed=embed)
                else:
                    await sales_channel.send(embed=embed)
                #Update our latest event so we know where we left off for next time
                command = "update globalvariables set value = '{0}' where name = 'prohibition_latest_sale_hash'".format(latest_sale_hash)
                cur.execute(command)
                conn.commit()
                #cur.execute("insert into prohibition_sales (id, timestamp) values ('{0}', {1})".format(i['txHash'], int(time.time())))
                #conn.commit()
            else:
                break

        #Go through our list in reverse order so that we post the oldest events first
        for i in reversed(offers):
            #cur.execute("select * from prohibition_offers where id = '{0}'".format(i['id']))
            results = [] #cur.fetchall()
            if results == []:
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
                    collection_id = int(int(collection_id_base)/1000000)
                    offer_quantity = i['quantityRemaining']
                    url = "https://prohibition.art/api/project/0x47A91457a3a1f700097199Fd63c039c4784384aB-"+str(collection_id)
                    response = requests.get(url, headers=headers)
                    data = json.loads(response.text)
                    collection_name = data['name']
                    collection_artist = data['artistName']
                    project_slug = data['slug']
                    image_url = "https://prohibition-arbitrum.s3.amazonaws.com/" + collection_id_base + ".png"
                    embed = discord.Embed(title=f"{collection_name} by {collection_artist}", description=f"{collection_name} received {offer_quantity} collection offer(s) of {offer_price} {offer_symbol} at <t:{timestamp}:f>.\n\n**Offer Maker:**\n[{maker_handle}]({maker_profile})\n\nhttps://prohibition.art/project/{project_slug}")
                    embed.set_image(url=image_url)
                    #If this is the h+c collection
                    if collection_id == 100:
                        await hc_offers_channel.send(embed=embed)
                    else:
                        await offers_channel.send(embed=embed)
                else:
                    token_id = i['criteria']['data']['token']['tokenId']
                    collection_id = int(int(token_id)/1000000)
                    #Check if we've been rate limited, and if so, wait 5 seconds and try again
                    while True:
                        #Get info on the token
                        url = "https://api-arbitrum.reservoir.tools/tokens/v6?tokens=0x47a91457a3a1f700097199fd63c039c4784384ab%3A"+token_id
                        response = requests.get(url, headers=headers)
                        data = json.loads(response.text)
                        response_code = response.status_code
                        if response_code == 429:
                            await asyncio.sleep(5)
                        else:
                            break
                
                    collection_name = data['tokens'][0]['token']['collection']['name']
                    token_name, token_artist = collection_name.rsplit(" by ", 1)
                    if token_id[-6:].lstrip('0') == "":
                        token_name = token_name + " #0"
                    else:
                        token_name = token_name + " #"+ token_id[-6:].lstrip('0')
                    image_url = "https://prohibition-arbitrum.s3.amazonaws.com/" + token_id + ".png"
                    wait_time = 60
                    #try to get the image url
                    response = requests.get(image_url, headers=headers)
                    response_code = response.status_code
                    while response_code != 200 and wait_time > 0:
                        await asyncio.sleep(60)
                        response = requests.get(image_url, headers=headers)
                        response_code = response.status_code
                        wait_time -= 1
                    owner_address = data['tokens'][0]['token']['owner']
                    #Get info on the current owner
                    owner_handle, owner_profile = await getUser(owner_address)
                    embed = discord.Embed(title=f"{token_name} by {token_artist}", description=f"{token_name} received a {offer_price} {offer_symbol} offer at <t:{timestamp}:f>.\n\n**Offer Maker:**\n[{maker_handle}]({maker_profile})\n\n**Current Owner:**\n[{owner_handle}]({owner_profile})\n\nhttps://prohibition.art/token/{token_id}")
                    embed.set_image(url=image_url)
                    #If this is the h+c collection
                    if collection_id == 100:
                        await hc_offers_channel.send(embed=embed)
                    else:
                        await offers_channel.send(embed=embed)
                #Update our latest event so we know where we left off for next time
                command = "update globalvariables set value = '{0}' where name = 'prohibition_latest_offer_id'".format(latest_offer_id)
                cur.execute(command)
                conn.commit()
                #cur.execute("insert into prohibition_offers (id, timestamp) values ('{0}', {1})".format(i['id'], int(time.time())))
                #conn.commit()
            else:
                break

        #Go through our list in reverse order so that we post the oldest events first
        for i in reversed(listings):
            #cur.execute("select * from prohibition_listings where id = '{0}'".format(i['id']))
            results = [] #cur.fetchall()
            if results == []:
                token_id = i['criteria']['data']['token']['tokenId']
                collection_id = int(int(token_id)/1000000)
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
                #Check if we've been rate limited, and if so, wait 5 seconds and try again
                while True:
                    #Get info on the token
                    url = "https://api-arbitrum.reservoir.tools/tokens/v6?tokens=0x47a91457a3a1f700097199fd63c039c4784384ab%3A"+token_id
                    response = requests.get(url, headers=headers)
                    data = json.loads(response.text)
                    response_code = response.status_code
                    if response_code == 429:
                        await asyncio.sleep(5)
                    else:
                        break
                

                if data['tokens'] == []:
                    continue
                collection_name = data['tokens'][0]['token']['collection']['name']
                token_name, token_artist = collection_name.rsplit(" by ", 1)
                if token_id[-6:].lstrip('0') == "":
                    token_name = token_name + " #0"
                else:
                    token_name = token_name + " #"+ token_id[-6:].lstrip('0')
                image_url = "https://prohibition-arbitrum.s3.amazonaws.com/" + token_id + ".png"
                wait_time = 60
                #try to get the image url
                response = requests.get(image_url, headers=headers)
                response_code = response.status_code
                while response_code != 200 and wait_time > 0:
                    await asyncio.sleep(60)
                    response = requests.get(image_url, headers=headers)
                    response_code = response.status_code
                    wait_time -= 1
                owner_address = data['tokens'][0]['token']['owner']
                #Get info on the current owner
                owner_handle, owner_profile = await getUser(owner_address)
                embed = discord.Embed(title=f"{token_name} by {token_artist}", description=f"{token_name} was listed for sale at <t:{timestamp}:f>.\n\n**Price:**\n{listing_price} {listing_symbol}\n\n**Owner:**\n[{owner_handle}]({owner_profile})\n\nhttps://prohibition.art/token/{token_id}")
                embed.set_image(url=image_url)
                #If this is the h+c collection
                if collection_id == 100:
                    await hc_listings_channel.send(embed=embed)
                else:
                    await listings_channel.send(embed=embed)
                #Update our latest event so we know where we left off for next time
                command = "update globalvariables set value = '{0}' where name = 'prohibition_latest_listing_id'".format(latest_listing_id)
                cur.execute(command)
                conn.commit()
                #cur.execute("insert into prohibition_listings (id, timestamp) values ('{0}', {1})".format(i['id'], int(time.time())))
                #conn.commit()
            else:
                break

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