import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import asyncio
from myserver import server_on

# Load token dari file .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Konfigurasi bot
intents = discord.Intents.default()
intents.members = True  # Aktifkan intent untuk events member
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Flag kontrol fitur welcome
enable_welcome = False  # Ganti ke True jika ingin mengaktifkan


@bot.event
async def on_ready():
    print(f'{bot.user.name} telah terhubung ke Discord!')
    print(f'Bot tersedia di {len(bot.guilds)} server.')


async def create_welcome_image(member):
    """
    Fungsi untuk membuat gambar welcome yang menarik
    """
    # Mengunduh avatar pengguna
    avatar_url = member.display_avatar.url
    response = requests.get(avatar_url)
    avatar_image = Image.open(BytesIO(response.content))

    # Resize avatar
    avatar_image = avatar_image.resize((180, 180))

    # Membuat background hitam
    background = Image.new('RGB', (600, 350), (0, 0, 0))

    # Membuat tempat untuk avatar (lingkaran)
    mask = Image.new('L', avatar_image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + avatar_image.size, fill=255)

    # Posisi avatar di tengah-atas
    avatar_pos = ((background.width - avatar_image.width) // 2, 30)

    # Masukkan avatar ke background
    background.paste(avatar_image, avatar_pos, mask)

    # Tambahkan teks
    draw = ImageDraw.Draw(background)

    # Teks "WELCOME"
    try:
        welcome_font = ImageFont.truetype("arial.ttf", 60)
    except IOError:
        welcome_font = ImageFont.load_default()

    welcome_text = "WELCOME"
    welcome_width = draw.textlength(welcome_text, font=welcome_font)
    draw.text(((background.width - welcome_width) // 2, 220),
              welcome_text,
              fill=(255, 255, 255),
              font=welcome_font)

    # Teks username
    try:
        username_font = ImageFont.truetype("arial.ttf", 30)
    except IOError:
        username_font = ImageFont.load_default()

    username_text = member.name.upper()
    username_width = draw.textlength(username_text, font=username_font)
    draw.text(((background.width - username_width) // 2, 290),
              username_text,
              fill=(255, 255, 255),
              font=username_font)

    # Simpan gambar
    output_buffer = BytesIO()
    background.save(output_buffer, format='PNG')
    output_buffer.seek(0)

    return output_buffer


@bot.event
async def on_member_join(member):
    if not enable_welcome:
        return  # Skip jika fitur welcome dimatikan
    """
    Event ketika member baru bergabung ke server
    """
    try:
        # Menggunakan variabel global untuk memungkinkan pengaturan melalui command
        global welcome_channel_id, rules_channel_id, roles_channel_id, welcome_message_template

        # Default values jika belum diatur
        if not hasattr(bot, 'welcome_channel_id'):
            welcome_channel_id = 1334267920855076904  # Ganti dengan ID channel Anda

        if not hasattr(bot, 'rules_channel_id'):
            rules_channel_id = 1334232021156757627  # Ganti dengan ID channel rules Anda

        if not hasattr(bot, 'roles_channel_id'):
            roles_channel_id = 1334232021156757628  # Ganti dengan ID channel roles Anda

        if not hasattr(bot, 'welcome_message_template'):
            welcome_message_template = (
                "Hey {mention}, welcome to Hedid Crazy!👋\n"
                "Please read our rules on <#{rules}> and pick your roles <#{roles}> \n"
                "Biar bisa main bareng hehehe")

        # Dapatkan channel dari ID
        welcome_channel = bot.get_channel(welcome_channel_id)

        if welcome_channel:
            # Membuat gambar welcome
            welcome_image = await create_welcome_image(member)

            # Format pesan welcome dengan link yang bisa diklik
            welcome_message = welcome_message_template.format(
                mention=member.mention,
                name=member.name,
                rules=rules_channel_id,
                roles=roles_channel_id)

            # Kirim gambar dan pesan welcome
            await welcome_channel.send(content=welcome_message,
                                       file=discord.File(
                                           fp=welcome_image,
                                           filename="welcome.png"))
    except Exception as e:
        print(f"Error in welcome message: {e}")


@bot.event
async def on_member_remove(member):
    """
    Event ketika member meninggalkan server
    """
    try:
        # Menggunakan variabel global untuk memungkinkan pengaturan melalui command
        global leave_channel_id

        # Default value jika belum diatur
        if not hasattr(bot, 'leave_channel_id'):
            leave_channel_id = 1334277030048563290  # Ganti dengan ID channel Anda

        # Dapatkan channel dari ID
        leave_channel = bot.get_channel(leave_channel_id)

        if leave_channel:
            # Membuat pesan leave
            leave_message = f"**{member.name}** telah meninggalkan server. 👋"

            # Kirim pesan leave
            await leave_channel.send(leave_message)
    except Exception as e:
        print(f"Error in leave message: {e}")


# Command pengaturan welcome channel
@bot.command(name='set_welcome')
@commands.has_permissions(
    administrator=True)  # Hanya admin yang bisa menggunakan command ini
async def set_welcome_channel(ctx, channel: discord.TextChannel):
    """
    Set welcome channel dengan command !set_welcome #nama-channel
    """
    # Dalam produksi nyata, simpan ID ini ke database
    global welcome_channel_id
    welcome_channel_id = channel.id
    await ctx.send(f"Channel welcome diatur ke {channel.mention}")


# Command pengaturan leave channel
@bot.command(name='set_leave')
@commands.has_permissions(
    administrator=True)  # Hanya admin yang bisa menggunakan command ini
async def set_leave_channel(ctx, channel: discord.TextChannel):
    """
    Set leave channel dengan command !set_leave #nama-channel
    """
    # Dalam produksi nyata, simpan ID ini ke database
    global leave_channel_id
    leave_channel_id = channel.id
    await ctx.send(f"Channel leave diatur ke {channel.mention}")


# Command pengaturan channel rules
@bot.command(name='set_rules')
@commands.has_permissions(administrator=True)
async def set_rules_channel(ctx, channel: discord.TextChannel):
    """
    Set rules channel dengan command !set_rules #nama-channel
    """
    global rules_channel_id
    rules_channel_id = channel.id
    await ctx.send(f"Channel rules diatur ke {channel.mention}")


# Command pengaturan channel roles
@bot.command(name='set_roles')
@commands.has_permissions(administrator=True)
async def set_roles_channel(ctx, channel: discord.TextChannel):
    """
    Set roles channel dengan command !set_roles #nama-channel
    """
    global roles_channel_id
    roles_channel_id = channel.id
    await ctx.send(f"Channel roles diatur ke {channel.mention}")


# Tambahkan command untuk customizing welcome message template
@bot.command(name='set_welcome_message')
@commands.has_permissions(administrator=True)
async def set_welcome_message(ctx, *, message=None):
    """
    Set welcome message template dengan command !set_welcome_message <pesan>
    Gunakan {mention} untuk menyisipkan mention member
    """
    global welcome_message_template
    if message:
        welcome_message_template = message
        await ctx.send("Pesan welcome berhasil diperbarui!")
    else:
        await ctx.send(
            "Penggunaan: !set_welcome_message <pesan welcome> - gunakan {mention} untuk menyisipkan mention member"
        )


@bot.command(name='toggle_welcome')
@commands.has_permissions(administrator=True)
async def toggle_welcome(ctx):
    global enable_welcome
    enable_welcome = not enable_welcome
    status = "diaktifkan" if enable_welcome else "dinonaktifkan"
    await ctx.send(f"Fitur welcome telah {status}.")


# Jalankan bot
server_on()
bot.run(TOKEN)
