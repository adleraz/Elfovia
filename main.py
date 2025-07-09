import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import io
import os
import json
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

app = Flask('')


@app.route('/')
def home():
    return "Bot is online and running!"


def run():
    app.run(host='0.0.0.0', port=8080)


def keep_alive():
    t = Thread(target=run)
    t.start()


async def create_welcome_image(member, config):
    try:
        background = Image.open(
            config["welcome_background_image"]).convert("RGBA")
    except FileNotFoundError:
        print(
            f"خطا: فایل پس‌زمینه '{config['welcome_background_image']}' پیدا نشد."
        )
        return None

    try:
        asset = member.avatar or member.default_avatar
        avatar_data = await asset.read()
    except Exception as e:
        print(f"خطا در خواندن آواتار برای {member.name}: {e}")
        return None

    avatar = Image.open(io.BytesIO(avatar_data)).convert("RGBA")

    avatar_size = tuple(config["avatar_size"])
    avatar = avatar.resize(avatar_size)
    mask = Image.new('L', avatar.size, 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0) + avatar.size, fill=255)
    avatar.putalpha(mask)

    avatar_position = tuple(config["avatar_position"])
    background.paste(avatar, avatar_position, avatar)

    draw = ImageDraw.Draw(background)
    try:
        font_path = config["font_path"]
        font_size = config["font_size"]
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        print(
            f"خطا: فونت '{font_path}' پیدا نشد. از فونت پیش‌فرض استفاده می‌شود."
        )
        font = ImageFont.load_default()

    welcome_text = f"خوش اومدی، {member.name}!"
    text_position = tuple(config["text_position"])
    text_color = tuple(config["text_color"])

    draw.text(text_position, welcome_text, font=font, fill=text_color)

    buffer = io.BytesIO()
    background.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

if TOKEN is None:
    print("خطا: توکن 'DISCORD_TOKEN' در فایل .env پیدا نشد.")
    exit()


def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("خطا: فایل 'config.json' پیدا نشد. برنامه متوقف می‌شود.")
        exit()
    except json.JSONDecodeError:
        print("خطا: فایل 'config.json' فرمت درستی ندارد. برنامه متوقف می‌شود.")
        exit()


config = load_config()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'بات {bot.user} با موفقیت آنلاین شد! بریم که داشته باشیم!')
    await bot.change_presence(activity=discord.Game(name="درحال بردگی به سینا")
                              )


@bot.event
async def on_member_join(member):
    channel_name = config["welcome_channel_name"]
    channel = discord.utils.get(member.guild.text_channels, name=channel_name)

    if not channel:
        print(f"کانال '{channel_name}' پیدا نشد.")
        return

    print(f'{member.name} به سرور {member.guild.name} جوین شد.')

    welcome_image_buffer = await create_welcome_image(member, config)

    if welcome_image_buffer:
        await channel.send(
            f"سلام {member.mention}! به سرور **{member.guild.name}** خیلی خوش اومدی!",
            file=discord.File(welcome_image_buffer, "welcome.png"))
    else:
        await channel.send(f"سلام {member.mention}! خوش اومدی به سرور!")


@bot.command(name='sendcustom', help='یک پیام سفارشی با متن شما ارسال می‌کند.')
async def send_custom_message(ctx, *, custom_text: str):
    formatted_message = f"""
**📣 پیامی برای شما:**
>>> {custom_text}

**✨ امید که روز خوبی داشته باشید!**
"""
    await ctx.send(formatted_message)
    print(f'دستور !sendcustom توسط {ctx.author.name} اجرا شد.')


@bot.command(name='hello', help='با بات سلام و احوالپرسی کنید!')
async def hello_command(ctx):
    await ctx.send(f"سلام {ctx.author.mention}! چطوری؟ 😉")
    print(f'دستور !hello توسط {ctx.author.name} اجرا شد.')


keep_alive()
bot.run(TOKEN)
