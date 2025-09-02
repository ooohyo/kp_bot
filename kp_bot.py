import requests, discord, asyncio, os
from discord.ext import commands, tasks

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1358704363253661821

upper_threshold = None  # KP above this will trigger alert
lower_threshold = None  # KP below this will trigger alert

# ---- Intents ----
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---- Data functions ----
def get_usdkrw():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/USDKRW=X?interval=5m"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    data = resp.json()
    return data['chart']['result'][0]['meta']['regularMarketPrice']

def get_usdtkrw():
    url = "https://api.upbit.com/v1/ticker?markets=KRW-USDT"
    resp = requests.get(url).json()
    # Upbit returns a list with one object; 'trade_price' is the KRW per USDT
    return float(resp[0]['trade_price'])

def get_kp():
    usdkrw = get_usdkrw()
    usdtkrw = get_usdtkrw()
    kp = usdtkrw / usdkrw - 1
    return usdtkrw, usdkrw, kp

# ---- Commands ----
@bot.command()
async def set_upper(ctx, value: float):
    """Set upper KP threshold (%)"""
    global upper_threshold
    upper_threshold = value
    await ctx.send(f"Upper threshold set to {upper_threshold:.2f}%")

@bot.command()
async def set_lower(ctx, value: float):
    """Set lower KP threshold (%)"""
    global lower_threshold
    lower_threshold = value
    await ctx.send(f"Lower threshold set to {lower_threshold:.2f}%")

@bot.command()
async def kp(ctx):
    """Instantly check current KP"""
    try:
        usdtkrw, usdkrw, kp_value = get_kp()
        msg = f"[KP Bot] USDT/KRW={usdtkrw:.2f}, USD/KRW={usdkrw:.2f}, KP={kp_value*100:.2f}%"
        await ctx.send(msg)
    except Exception as e:
        await ctx.send(f"Error fetching KP: {e}")

@bot.command()
async def clear(ctx):
    """Clear all KP thresholds"""
    global upper_threshold, lower_threshold
    upper_threshold = None
    lower_threshold = None
    await ctx.send("✅ All thresholds have been cleared.")

# ---- Background task ----
@tasks.loop(minutes=1)
async def check_kp():
    try:
        usdtkrw, usdkrw, kp_value = get_kp()
        msg = f"[KP Bot] USDT/KRW={usdtkrw:.2f}, USD/KRW={usdkrw:.2f}, KP={kp_value*100:.2f}%"
        print(msg)
        channel = bot.get_channel(CHANNEL_ID)

        if upper_threshold is not None and kp_value*100 >= upper_threshold:
            await channel.send(f"@everyone 🚨 KP is above upper threshold ({upper_threshold:.2f}%):\n{msg}")
        if lower_threshold is not None and kp_value*100 <= lower_threshold:
            await channel.send(f"@everyone 🚨 KP is below lower threshold ({lower_threshold:.2f}%):\n{msg}")
    except Exception as e:
        print("Error in check_kp:", e)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    check_kp.start()

bot.run(TOKEN)
