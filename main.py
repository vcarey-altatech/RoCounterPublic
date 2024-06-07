# IMPORT MODULES
import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.errors import Forbidden
import os
import json
import time
from datetime import datetime, timezone
import requests
import asyncio
import aiohttp
from random import randint

# SET INTENTS
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

# DEFINE BOT
prefix = '/'
bot = commands.Bot(command_prefix=prefix, intents=intents)
bot.help_command = None

# DEFINE OTHER VARS
start_time = time.time()
heartbeat_url = 'HEARTBEAT URL HERE'
bot_token = 'TOKEN HERE'

# SETUP SERVER DATA JSON
if os.path.exists("servers.json"):
    with open("servers.json", "r") as f:
        server_data = json.load(f)
else:
    server_data = {}

def save_server_data():
    with open("servers.json", "w") as f:
        json.dump(server_data, f, indent=4)

# SETUP BLACKLIST DATA JSON
if os.path.exists("blacklists.json"):
    with open("blacklists.json", "r") as f:
        blacklist_data = json.load(f)
else:
    blacklist_data = {}

def save_blacklist_data():
    with open("blacklists.json", "w") as f:
        json.dump(blacklist_data, f, indent=4)

# ON READY
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    await update_status()
    bot.loop.create_task(send_heartbeat())
    bot.loop.create_task(check_group_members())

# SEND HEARBEAT
async def send_heartbeat():
    while True:
        try:
            response = requests.get(heartbeat_url)
            if response.status_code == 200:
                print("Heartbeat sent successfully.")
            else:
                print(f"Failed to send heartbeat: Status code {response.status_code}")
        except Exception as e:
            print(f"Exception occurred while sending heartbeat: {e}")
        await asyncio.sleep(300)

# GUILD JOIN
@bot.event
async def on_guild_join(guild):
    owner = bot.get_user(702435498563600405)
    if owner:
        invite_url = "Failed to create invite"

        try:
            invite = await guild.text_channels[0].create_invite(max_age=0, max_uses=1)
            invite_url = invite.url
        except Exception as e:
            print(f'Failed to create invite link: {e}')

        embed = discord.Embed(
            title='**Added to server**',
            description=f"**Name:** {guild.name}\n**ID:** {guild.id}\n**Invite:** {invite_url}",
            color=discord.Color.from_rgb(0, 0, 0),
            timestamp=datetime.now(timezone.utc)
        )

        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

        embed.set_footer(
            text='Powered by RoCounter',
            icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
        )

        await owner.send(embed=embed)

    await update_status()

    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            embed = discord.Embed(
            title='**Welcome to RoCounter**',
            description=f"**Getting started:**\nRun </setgroup:1242555030213624011> to set the Roblox group which your server is linked to\nRun </setchannel:1242555030666743869> to set the channel which member alerts are sent\n\n**Need any more help?**\nRun </help:1242527544826400828> or join our discord server: https://discord.gg/9v4BMRfbH6\n\nThank you for choosing RoCounter!",
            color=discord.Color.from_rgb(0, 0, 0),
            timestamp=datetime.now(timezone.utc)
        )

        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

        embed.set_footer(
            text='Powered by RoCounter',
            icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
        )

        await channel.send(embed=embed)
        break

# GUILD REMOVE
@bot.event
async def on_guild_remove(guild):
    owner = bot.get_user(702435498563600405)
    if owner:
        invite_url = "Failed to create invite"

        try:
            invite = await guild.text_channels[0].create_invite(max_age=0, max_uses=1)
            invite_url = invite.url
        except Exception as e:
            print(f'Failed to create invite link: {e}')

        embed = discord.Embed(
            title='**Removed from server**',
            description=f"**Name:** {guild.name}\n**ID:** {guild.id}\n**Invite:** {invite_url}",
            color=discord.Color.from_rgb(0, 0, 0),
            timestamp=datetime.now(timezone.utc)
        )

        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

        embed.set_footer(
            text='Powered by RoCounter',
            icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
        )

        await owner.send(embed=embed)

    await update_status()

    server_id = str(guild.id)
    if server_id in server_data:
        del server_data[server_id]
        save_server_data()

# UPDATE STATUS
async def update_status():
    try:
        total_members = sum(guild.member_count for guild in bot.guilds)
        status = f'{total_members} users | /help'
        activity = discord.Activity(type=discord.ActivityType.watching, name=status)
        await bot.change_presence(activity=activity)
        print(f'Successfully set status to: {status}')
    except Exception as e:
        print(f'Failed to set status // Given Error: {e}')

# SEE IF COMMAND IS RUN IN SERVER
def is_in_server():
    async def predicate(interaction: discord.Interaction):
        if interaction.guild is None:
            embed = discord.Embed(
                title='**Error**',
                description="Please run this command in a server",
                color=discord.Color.from_rgb(0, 0, 0),
                timestamp=datetime.now(timezone.utc)
            )

            embed.set_footer(
                text='Powered by RoCounter',
                icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
            )

            await interaction.response.send_message(embed=embed)
            return False
        else:
            return True
    return app_commands.check(predicate)

# SEE IF THE USER IS THE BOT OWNER
def is_owner():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id != 702435498563600405:
            embed = discord.Embed(
                title='**Error**',
                description="You do not have permission to run this command",
                color=discord.Color.from_rgb(0, 0, 0),
                timestamp=datetime.now(timezone.utc)
            )

            embed.set_footer(
                text='Powered by RoCounter',
                icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        else:
            return True
    return app_commands.check(predicate)

# SEE IF USER IS BLACKLISTED
def is_not_blacklisted():
    async def predicate(interaction: discord.Interaction):
        userid = str(interaction.user.id)
        if userid in blacklist_data:
            if blacklist_data[userid]['blacklisted'] == True:
                embed = discord.Embed(
                    title='**Error**',
                    description="You are blacklisted from the bot\nPlease open a ticket in our [Support Server](https://discord.gg/9v4BMRfbH6) to appeal this",
                    color=discord.Color.from_rgb(0, 0, 0),
                    timestamp=datetime.now(timezone.utc)
                )

                embed.set_footer(
                    text='Powered by RoCounter',
                    icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
                )

                await interaction.response.send_message(embed=embed, ephemeral=True)
                return False
        return True
    return app_commands.check(predicate)

# GET ALL BLACKLISTED USERS
def get_blacklisted_users():
    with open("blacklists.json", 'r') as f:
        data = json.load(f)
    
    blacklisted_users = [f'<@{user_id}>' for user_id, info in data.items() if info.get('blacklisted')]

    formatted_users = "\n".join(blacklisted_users)
    return formatted_users

# CHECK IF RBLX GROUP EXISTS FROM ID
def check_roblox_group_existence(group_id: int):
    url = f"https://groups.roblox.com/v1/groups/{group_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return 'errors' not in data
    return False

# CHECK IF CHANNEL EXISTS FROM ID
def check_channel_exists(channel_id):
    channel = bot.get_channel(channel_id)
    if channel:
        return True
    else:
        return False

# GET A RBLX GROUP'S INFO FROM ID
def get_roblox_group_info(group_id_var: int):
    info_url = f'https://groups.roblox.com/v1/groups/{group_id_var}'
    thumbnail_url = f'https://thumbnails.roblox.com/v1/groups/icons?groupIds={group_id_var}&size=420x420&format=Png&isCircular=false'

    info_response = requests.get(info_url)
    thumbnail_response = requests.get(thumbnail_url)

    if info_response.status_code == 200 and thumbnail_response.status_code == 200:
        info_data = info_response.json()
        thumbnail_data = thumbnail_response.json()

        if 'data' in thumbnail_data and len(thumbnail_data['data']) > 0:
            avatar_url = thumbnail_data['data'][0]['imageUrl']
        else:
            avatar_url = None

        if 'shout' not in info_data or info_data['shout'] is None:
            formatted_shout = "No Shout"
        else:
            formatted_shout = info_data['shout']['body']

        if 'description' not in info_data or info_data['description'] is None or info_data['description'] == "":
            formatted_description = "No Description"
        else:
            formatted_description = info_data['description']

        formatted_name = str(info_data['name']).replace(" ", "-").lower()
        formatted_member_count = f"{info_data['memberCount']:,}"

        group_info = {
            "Name": info_data['name'],
            "Description": formatted_description,
            "OwnerId": info_data['owner']['userId'],
            "MemberCount": formatted_member_count,
            "UnformattedMemberCount": info_data['memberCount'],
            "Shout": formatted_shout,
            "ThumbnailUrl": avatar_url,
            "GroupUrl": f'https://www.roblox.com/groups/{str(group_id_var)}/{formatted_name}#!/about'
        }
        return group_info
    return None

# GET A RBLX USER'S INFO FROM ID
def get_roblox_user_info(user_id_var: int):
    info_url = f'https://users.roblox.com/v1/users/{user_id_var}'
    thumbnail_url = f'https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id_var}&size=150x150&format=Png&isCircular=false'

    user_response = requests.get(info_url)
    avatar_response = requests.get(thumbnail_url)

    if user_response.status_code == 200 and avatar_response.status_code == 200:
        avatar_data = avatar_response.json()
        user_data = user_response.json()
        if 'data' in avatar_data and len(avatar_data['data']) > 0:
            avatar_url = avatar_data['data'][0]['imageUrl']
        else:
            avatar_url = None

        user_info = {
            "Username": user_data.get("name"),
            "DisplayName": user_data.get("displayName"),
            "Description": user_data.get("description"),
            "AvatarUrl": avatar_url,
            "ProfileUrl": f"https://www.roblox.com/users/{user_id_var}/profile"
        }
        return user_info
    return None

# OWNER ONLY COMMANDS
@app_commands.describe(user="The user to blacklist")
@bot.tree.command(name="blacklist", description="Blacklist a user from RoCounter")
@is_owner()
async def blacklist(interaction: discord.Interaction, user: discord.User):
    try:
        user_id = str(user.id)
        if user_id not in blacklist_data:
            blacklist_data[user_id] = {}
            blacklist_data[user_id]['blacklisted'] = True
            save_blacklist_data()

            embed = discord.Embed(
                title='**Successfully Blacklisted User**',
                description=f"Blacklisted user {user.mention} from RoCounter",
                color=discord.Color.from_rgb(0, 0, 0),
                timestamp=datetime.now(timezone.utc)
            )

            embed.set_footer(
                text='Powered by RoCounter',
                icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
            )

            await interaction.response.send_message(embed=embed)
        else:
            if blacklist_data[user_id]['blacklisted'] == True:
                embed = discord.Embed(
                    title='**Error**',
                    description=f"User {user.mention} is already blacklisted",
                    color=discord.Color.from_rgb(0, 0, 0),
                    timestamp=datetime.now(timezone.utc)
                )

                embed.set_footer(
                    text='Powered by RoCounter',
                    icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
                )

                await interaction.response.send_message(embed=embed)
            else:
                blacklist_data[user_id]['blacklisted'] = True
                save_blacklist_data()

                embed = discord.Embed(
                    title='**Successfully Blacklisted User**',
                    description=f"Blacklisted user {user.mention} from RoCounter",
                    color=discord.Color.from_rgb(0, 0, 0),
                    timestamp=datetime.now(timezone.utc)
                )

                embed.set_footer(
                    text='Powered by RoCounter',
                    icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
                )

                await interaction.response.send_message(embed=embed)

    except Exception as e:
        embed = discord.Embed(
            title='**Error**',
            description=f"Given Error: {e}",
            color=discord.Color.from_rgb(0, 0, 0),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(
            text='Powered by RoCounter',
            icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
        )

        await interaction.response.send_message(embed=embed)

@app_commands.describe(user="The user to unblacklist")
@bot.tree.command(name="unblacklist", description="Unblacklist a user from RoCounter")
@is_owner()
async def unblacklist(interaction: discord.Interaction, user: discord.User):
    try:
        user_id = str(user.id)
        if user_id not in blacklist_data:
            embed = discord.Embed(
                title='**Error**',
                description=f"User {user.mention} is not blacklisted",
                color=discord.Color.from_rgb(0, 0, 0),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(
                text='Powered by RoCounter',
                icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
            )

            await interaction.response.send_message(embed=embed)
        else:
            blacklist_data[user_id]['blacklisted'] = False
            save_blacklist_data()

            embed = discord.Embed(
                title='**Successfully Unblacklisted User**',
                description=f"Unblacklisted user {user.mention} from RoCounter",
                color=discord.Color.from_rgb(0, 0, 0),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(
                text='Powered by RoCounter',
                icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
            )

            await interaction.response.send_message(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title='**Error**',
            description=f"Given Error: {e}",
            color=discord.Color.from_rgb(0, 0, 0),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(
            text='Powered by RoCounter',
            icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
        )

        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="blacklists", description="View all blacklisted users")
@is_owner()
async def blacklists(interaction: discord.Interaction):
    blacklists_list = get_blacklisted_users()

    embed = discord.Embed(
        title='**Blacklisted Users**',
        description=f'{str(blacklists_list)}',
        color=discord.Color.from_rgb(0, 0, 0),
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(
        text='Powered by RoCounter',
        icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
    )

    await interaction.response.send_message(embed=embed)

# SERVER ADMIN ONLY COMMANDS
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(group_id="The group you want to track")
@bot.tree.command(name="setgroup", description="Set the group to track the members of")
@is_not_blacklisted()
@is_in_server()
async def setgroup(interaction: discord.Interaction, group_id: int):
    exists = await asyncio.to_thread(check_roblox_group_existence, group_id)

    if exists:
        server_id = str(interaction.guild.id)
        if server_id not in server_data:
            server_data[server_id] = {}
        server_data[server_id]['group_id'] = group_id
        save_server_data()

        group_info = get_roblox_group_info(group_id)

        embed = discord.Embed(
            title='**Successfully Set Group**',
            url=group_info['GroupUrl'],
            description=f"Set group to {group_info['Name']} ({group_id}) for {interaction.guild.name}",
            color=discord.Color.from_rgb(0, 0, 0),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(
            text='Powered by RoCounter',
            icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
        )
        embed.set_thumbnail(url=group_info['ThumbnailUrl'])

        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(
            title='**Failed to Set Group**',
            description=f"Roblox Group with ID '{group_id}' was not found",
            color=discord.Color.from_rgb(0, 0, 0),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(
            text='Powered by RoCounter',
            icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
        )

        await interaction.response.send_message(embed=embed)

@setgroup.error
async def setgroup_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        embed = discord.Embed(
            title='**Error**',
            description="You do not have permission to run this command",
            color=discord.Color.from_rgb(0, 0, 0),
            timestamp=datetime.now(timezone.utc)
        )

        embed.set_footer(
            text='Powered by RoCounter',
            icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(channel="The channel you want to have alerts sent to")
@bot.tree.command(name="setchannel", description="Set the channel to send alerts to")
@is_not_blacklisted()
@is_in_server()
async def setchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    server_id = str(interaction.guild.id)
    if server_id not in server_data:
        server_data[server_id] = {}
    server_data[server_id]['channel_id'] = channel.id
    save_server_data()

    embed = discord.Embed(
        title='**Successfully Set Channel**',
        description=f"Set channel to {channel.mention} for {interaction.guild.name}",
        color=discord.Color.from_rgb(0, 0, 0),
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(
        text='Powered by RoCounter',
        icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
    )

    await interaction.response.send_message(embed=embed)

@setchannel.error
async def setchannel_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        embed = discord.Embed(
            title='**Error**',
            description="You do not have permission to run this command",
            color=discord.Color.from_rgb(0, 0, 0),
            timestamp=datetime.now(timezone.utc)
        )

        embed.set_footer(
            text='Powered by RoCounter',
            icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

# PUBLIC COMMANDS
@bot.tree.command(name="help", description="Get information about RoCounter and its commands")
@is_not_blacklisted()
@is_in_server()
async def help(interaction: discord.Interaction):

    server_id = str(interaction.guild.id)
    group_id = server_data.get(server_id, {}).get('group_id')
    channel_id = server_data.get(server_id, {}).get('channel_id')

    group_info = get_roblox_group_info(group_id)

    if group_id:
        group_name = group_info['Name']
        group_name_hyphenated = group_name.replace(' ', '-')
        group_str = f'[{group_name}](https://www.roblox.com/groups/{group_id}/{group_name_hyphenated}#!/about)'
    else:
        group_str = "Not set"

    if channel_id:
        channel_str = f'<#{channel_id}>'
    else:
        channel_str = "Not set"

    embed = discord.Embed(
        title=f'**Commands List | Prefix: {prefix}**',
        description=f"**All Users**\n</help:1242527544826400828> - View a list of all the bot's commands\n</ping:1242524126682415248> - Get the bot's latency in milliseconds\n</status:1242527544826400829> - Monitor the bot's status and view incidents\n</groupinfo:1243637200407498852> - Get information about a Roblox group\n</funfact:1242571175406735483> - Learn something new\n\n**Server Administrators Only**\n</setchannel:1242555030666743869> - Set the channel used to send member updates to\n</setgroup:1242555030213624011> - Set the Roblox group id to track\n\n**Linked Group:** {group_str}\n**Channel:** {channel_str}\n\n**[Invite the Bot](https://discord.com/oauth2/authorize?client_id=750640197674467369&permissions=8&scope=bot)**",        color=discord.Color.from_rgb(0, 0, 0),
        timestamp=datetime.now(timezone.utc)
    )

    embed.set_footer(
        text='Powered by RoCounter',
        icon_url=
        'https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
    )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="status", description="Get the uptime and status information of RoCounter")
@is_not_blacklisted()
@is_in_server()
async def status(interaction: discord.Interaction):
    current_time = time.time()
    uptime_seconds = int(current_time - start_time)

    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"

    embed = discord.Embed(
        title = "**RoCounter Status**",
        description=f'**Current Uptime: {uptime_str}\n\n[Monitor Status](https://status.altatech.uk/)**\n*[Incident 371793](https://status.altatech.uk/incident/371793)*\n*[Incident 373334](https://status.altatech.uk/incident/373334)*',
        color=discord.Color.from_rgb(0, 0, 0),
        timestamp=datetime.now(timezone.utc)
    )

    embed.set_footer(
        text='Powered by RoCounter',
        icon_url=
        'https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
    )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ping", description="Get the latency (ms) of RoCounter")
@is_not_blacklisted()
@is_in_server()
async def ping(interaction: discord.Interaction):
    latency = bot.latency * 1000
    embed = discord.Embed(
        title = "**Pong**",
        description=f'Latency: {latency:.2f}ms',
        color=discord.Color.from_rgb(0, 0, 0),
        timestamp=datetime.now(timezone.utc)
    )

    embed.set_footer(
        text='Powered by RoCounter',
        icon_url=
        'https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
    )

    await interaction.response.send_message(embed=embed)

facts = [
    "Giraffes are 30 times more likely to get hit by lightning than people",
    "A chicken once lived for 18 months without a head (it was you)",
    "The fear of long words is called Hippopotomonstrosesquippedaliophobia",
    "You should recommend us to a friend! 👀",
    "Australia is wider than the moon (but not as wide as you)", 
    "Rafael did NOT help me make this bot",
    "Katie did NOT help me make this bot either",
    "mariah carey >>>>>> ur fav",
    "beyoncé >>> ur fav",
    "rafael's built like a giraffe",
    "this is fact number 9 (im running out of facts)",
    "this bot took me a week to develop and get stable (hopfully it stays good)",
    "https://altatech.uk/ is actually the best website ever (real)"
    ]

@bot.tree.command(name="funfact", description="Learn something new")
@is_not_blacklisted()
@is_in_server()
async def funfact(interaction: discord.Interaction):

    fact = facts[randint(0, len(facts) - 1)]

    embed = discord.Embed(
        title = "**Fun Fact**",
        description=f'{fact}',
        color=discord.Color.from_rgb(0, 0, 0),
        timestamp=datetime.now(timezone.utc)
    )

    embed.set_footer(
        text='Powered by RoCounter',
        icon_url=
        'https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
    )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="groupinfo", description="Get information about a Roblox group")
@app_commands.describe(id="The Roblox group ID to get information about")
@is_not_blacklisted()
@is_in_server()
async def groupinfo(interaction: discord.Interaction, id: int = None):

    server_id = str(interaction.guild.id)
    if id == None:
        if server_id in server_data:
            try:
                data = server_data.get(str(interaction.guild.id), {})
                group_id = data.get('group_id')
                group_info = get_roblox_group_info(group_id)

                embed = discord.Embed(
                    title=f"**Group Info for {group_info['Name']}**",
                    url=group_info['GroupUrl'],
                    color=discord.Color.from_rgb(0, 0, 0),
                    timestamp=datetime.now(timezone.utc)
                )

                embed.add_field(name="**Member Count**", value=group_info['MemberCount'], inline=True)

                owner_info = get_roblox_user_info(group_info['OwnerId'])
                owner_str = f"[{owner_info['DisplayName']} (@{owner_info['Username']})]({owner_info['ProfileUrl']})"
                embed.add_field(name="**Owner**", value=owner_str, inline=True)

                embed.add_field(name="**Shout**", value=group_info['Shout'], inline=True)
                embed.add_field(name="**Description**", value=group_info['Description'], inline=True)

                embed.set_footer(
                    text='Powered by RoCounter',
                    icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
                )

                embed.set_thumbnail(url=group_info['ThumbnailUrl'])

                await interaction.response.send_message(embed=embed)
            except Exception as e:
                embed = discord.Embed(
                    title=f'**An error occured**',
                    description=f"Given error: {e}",
                    color=discord.Color.from_rgb(0, 0, 0),
                    timestamp=datetime.now(timezone.utc)
                )

                embed.set_footer(
                    text='Powered by RoCounter',
                    icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
                )

                embed.set_thumbnail(url=group_info['ThumbnailUrl'])

                await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title=f'**Group not set**',
                description=f"No group is set for this server. Please use </setgroup:1242555030213624011> to set a group or provide a group id when using this command.",
                color=discord.Color.from_rgb(0, 0, 0),
                timestamp=datetime.now(timezone.utc)
            )

            embed.set_footer(
                text='Powered by RoCounter',
                icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
            )

            await interaction.response.send_message(embed=embed)

    else:
        loop = asyncio.get_event_loop()
        exists = await loop.run_in_executor(None, check_roblox_group_existence, id)
        groupExists = False
        if exists:
            groupExists = True
        if exists == True:
            group_info = get_roblox_group_info(id)

            embed = discord.Embed(
                title=f"**Group Info for {group_info['Name']}**",
                url=group_info['GroupUrl'],
                color=discord.Color.from_rgb(0, 0, 0),
                timestamp=datetime.now(timezone.utc)
            )

            embed.add_field(name="**Member Count**", value=group_info['MemberCount'], inline=True)

            owner_info = get_roblox_user_info(group_info['OwnerId'])
            owner_str = f"[{owner_info['DisplayName']} (@{owner_info['Username']})]({owner_info['ProfileUrl']})"
            embed.add_field(name="**Owner**", value=owner_str, inline=True)

            embed.add_field(name="**Shout**", value=group_info['Shout'], inline=True)
            embed.add_field(name="**Description**", value=group_info['Description'], inline=True)

            embed.set_thumbnail(url=group_info['ThumbnailUrl'])

            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title=f'**Group not found**',
                description=f"Roblox Group with ID '{str(id)}' was not found",
                color=discord.Color.from_rgb(0, 0, 0),
                timestamp=datetime.now(timezone.utc)
            )

            embed.set_footer(
                text='Powered by RoCounter',
                icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
            )

            await interaction.response.send_message(embed=embed)

# MEMBER CHECK LOOP
async def check_group_members():
    while True:
        servers = list(server_data.items())
        num_servers = len(servers)
        delay_between_checks = 300 / max(num_servers, 1)

        for server_id, data in servers:
            guild = await bot.fetch_guild(server_id)
            group_id = data.get('group_id')
            channel_id = data.get('channel_id')
            channel_exists = check_channel_exists(channel_id)
            if group_id != None and channel_exists == True:
                channel = bot.get_channel(channel_id)
                if channel:
                    print(f'Checking group members for server {guild.name}:{server_id}')
                    try:
                        group_info = get_roblox_group_info(group_id)
                        current_member_count = group_info['UnformattedMemberCount']
                        previous_member_count = data.get('member_count', current_member_count)
                        group_name = group_info['Name']
                        group_thumbnail_url = group_info['ThumbnailUrl']

                        if int(current_member_count) > int(previous_member_count):
                            gained_members = int(current_member_count) - int(previous_member_count)
                            formatted_gained_members = f"{gained_members:,}"
                            if gained_members == 1:
                                embed = discord.Embed(
                                    title='**Member Gained**',
                                    url=group_info['GroupUrl'],
                                    description=f"{group_name} has gained {formatted_gained_members} member\nCurrent members: {current_member_count:,}",
                                    color=discord.Color.from_rgb(0, 0, 0),
                                    timestamp=datetime.now(timezone.utc)
                                )
                            else:
                                embed = discord.Embed(
                                    title='**Members Gained**',
                                    url=group_info['GroupUrl'],
                                    description=f"{group_name} has gained {formatted_gained_members} members\nCurrent members: {current_member_count:,}",
                                    color=discord.Color.from_rgb(0, 0, 0),
                                    timestamp=datetime.now(timezone.utc)
                                )

                            embed.set_footer(
                                text='Powered by RoCounter',
                                icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
                            )
                            embed.set_thumbnail(url=group_thumbnail_url)
                            await channel.send(embed=embed)

                        elif int(current_member_count) < int(previous_member_count):
                            lost_members = int(previous_member_count) - int(current_member_count)
                            formatted_lost_members = f"{lost_members:,}"

                            if lost_members == 1:
                                embed = discord.Embed(
                                    title='**Member Lost**',
                                    url=group_info['GroupUrl'],
                                    description=f"{group_name} has lost {formatted_lost_members} member\nCurrent members: {current_member_count:,}",
                                    color=discord.Color.from_rgb(0, 0, 0),
                                    timestamp=datetime.now(timezone.utc)
                                )
                            else:
                                embed = discord.Embed(
                                    title='**Members Lost**',
                                    url=group_info['GroupUrl'],
                                    description=f"{group_name} has lost {formatted_lost_members} members\nCurrent members: {current_member_count:,}",
                                    color=discord.Color.from_rgb(0, 0, 0),
                                    timestamp=datetime.now(timezone.utc)
                                )

                            embed.set_footer(
                                text='Powered by RoCounter',
                                icon_url='https://www.altatech.uk/wp-content/uploads/2024/05/RoCounter-Logo-Transparent-BG.png'
                            )
                            embed.set_thumbnail(url=group_thumbnail_url)
                            await channel.send(embed=embed)

                        data['member_count'] = int(current_member_count)
                        save_server_data()
                    except Exception as e:
                        print(f"Error fetching group data: {e}")

            await asyncio.sleep(delay_between_checks)

bot.run(bot_token)
