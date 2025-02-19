import discord
import aiohttp

from discord.ext import commands
from discord.ui import Modal, TextInput, View, Button
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1329702316353523742 
CITIZEN_ROLE_ID = 1329704083380244573  # ID ролі "Громадянин"
APPLICATIONS_CHANNEL_ID = 1330793797080191017 # ID каналу для анкет
ADMIN_ROLE_ID = 1332690277944791090
ROBLOX_GROUP_ID = 35520090  # ID групи в Roblox

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True  
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def is_in_roblox_group(username: str) -> bool:
    username = username.strip()
    print(f"🔍 Перевіряємо користувача: {username}")

    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://users.roblox.com/v1/users/search?keyword={username}&limit=10") as resp:
            if resp.status != 200:
                return False

            data = await resp.json()
            if "data" in data and len(data["data"]) > 0:
                user_id = data["data"][0]["id"]
            else:
                return False

        async with session.get(f"https://groups.roblox.com/v1/users/{user_id}/groups/roles") as group_resp:
            if group_resp.status != 200:
                return False

            group_data = await group_resp.json()
            return any(group["group"]["id"] == ROBLOX_GROUP_ID for group in group_data.get("data", []))

class ApplicationModal(Modal, title="Подати анкету"):
    roblox_nickname = TextInput(label="Введіть ваш нік в Roblox")
    question1 = TextInput(label="Де ви дізнались про нас?", style=discord.TextStyle.long)
    question2 = TextInput(label="Чому саме обрали нас?", style=discord.TextStyle.long)
    question3 = TextInput(label="Ви в нашій групі роблокс? (Так/Ні)")
    question4 = TextInput(label="Погоджуєтесь з правилами? (Так/Ні)")

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.guild.id != GUILD_ID:
            await interaction.response.send_message("❌ Цей бот доступний лише на офіційному сервері!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        if await is_in_roblox_group(self.roblox_nickname.value):
            embed = discord.Embed(title=" Нова анкета!", color=discord.Color.blue())
            embed.add_field(name=" Нік в Roblox", value=self.roblox_nickname.value, inline=False)
            embed.add_field(name=" Де дізнались про нас?", value=self.question1.value, inline=False)
            embed.add_field(name=" Чому обрали нас?", value=self.question2.value, inline=False)
            embed.add_field(name=" У групі роблокс?", value=self.question3.value, inline=False)
            embed.add_field(name=" Приймає правила?", value=self.question4.value, inline=False)
            embed.add_field(name=" Discord", value=interaction.user.mention, inline=False)
            embed.set_footer(text=str(interaction.user.id))
            
            channel = bot.get_channel(APPLICATIONS_CHANNEL_ID) or await bot.fetch_channel(APPLICATIONS_CHANNEL_ID)
            if channel:
                await channel.send(embed=embed, view=ApplicationView())
            else:
                await interaction.followup.send("❌ Помилка: канал для анкет не знайдено!", ephemeral=True)

class ApplicationView(View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Схвалити", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.id != GUILD_ID:
            await interaction.response.send_message("❌ Цей бот доступний лише на офіційному сервері!", ephemeral=True)
            return

        admin_roles = [role.id for role in interaction.user.roles]
        if ADMIN_ROLE_ID not in admin_roles:
            await interaction.response.send_message("❌ У вас недостатньо прав!", ephemeral=True)
            return

        try:
            user_id = int(interaction.message.embeds[0].footer.text)
            user = interaction.guild.get_member(user_id)
        except (IndexError, ValueError):
            await interaction.response.send_message("❌ Помилка отримання ID користувача!", ephemeral=True)
            return

        role = interaction.guild.get_role(CITIZEN_ROLE_ID)
        if user and role:
            await user.add_roles(role)
            await interaction.response.send_message(f"{user.mention}, ти отримав роль Громадянина! ✅", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Не вдалося видати роль!", ephemeral=True)
        await interaction.message.delete()

    @discord.ui.button(label="Відхилити", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild.id != GUILD_ID:
            await interaction.response.send_message("❌ Цей бот доступний лише на офіційному сервері!", ephemeral=True)
            return
        
        admin_roles = [role.id for role in interaction.user.roles]
        if ADMIN_ROLE_ID not in admin_roles:
            await interaction.response.send_message("❌ У вас недостатньо прав!", ephemeral=True)
            return
        
        await interaction.message.delete()
        await interaction.response.send_message("Анкета відхилена. ❌", ephemeral=True)

@bot.tree.command(name="getcitizenship", description="Подати анкету")
async def getcitizenship(interaction: discord.Interaction):
    if interaction.guild.id != GUILD_ID:
        await interaction.response.send_message("❌ Цей бот доступний лише на офіційному сервері!", ephemeral=True)
        return
    await interaction.response.send_modal(ApplicationModal())

@bot.tree.command(name="ping", description="Перевірка працездатності бота")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong! Бот працює!", ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'✅ Бот {bot.user} запущений!')

bot.run(TOKEN)

