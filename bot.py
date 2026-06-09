import discord
from discord.ext import commands
import json
import os

# ── Configuration ──────────────────────────────────────────────
TOKEN          = "YOUR_BOT_TOKEN"
CHANNEL_ID     = 1489338057206272162   # ID of the channel to track
ROLE_ID        = 1513981949084176404   # ID of the role to assign
MESSAGE_LIMIT  = 50                   # Messages required to earn the role
COUNTS_FILE    = "message_counts.json"
# ───────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


def load_counts() -> dict:
    """Load message counts from disk."""
    if os.path.exists(COUNTS_FILE):
        with open(COUNTS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_counts(counts: dict) -> None:
    """Persist message counts to disk."""
    with open(COUNTS_FILE, "w") as f:
        json.dump(counts, f, indent=2)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


@bot.event
async def on_message(message: discord.Message):
    # Ignore bots and messages outside the tracked channel
    if message.author.bot:
        return
    if message.channel.id != CHANNEL_ID:
        await bot.process_commands(message)
        return

    counts = load_counts()
    user_id = str(message.author.id)

    # Increment the counter
    counts[user_id] = counts.get(user_id, 0) + 1
    save_counts(counts)

    current = counts[user_id]
    print(f"{message.author} — {current}/{MESSAGE_LIMIT} messages in tracked channel")

    # Assign role once the threshold is crossed (only once)
    if current == MESSAGE_LIMIT:
        guild = message.guild
        role  = guild.get_role(ROLE_ID)
        member = message.author

        if role and role not in member.roles:
            await member.add_roles(role, reason=f"Reached {MESSAGE_LIMIT} messages in channel")
            await message.channel.send(
                f"🎉 Congrats {member.mention}! You've earned the **{role.name}** role "
                f"for sending {MESSAGE_LIMIT} messages here!"
            )

    await bot.process_commands(message)


# ── Optional admin commands ─────────────────────────────────────

@bot.command(name="msgcount")
@commands.has_permissions(manage_guild=True)
async def msg_count(ctx, member: discord.Member):
    """Check a user's message count. Usage: !msgcount @user"""
    counts = load_counts()
    count  = counts.get(str(member.id), 0)
    await ctx.send(f"{member.mention} has **{count}/{MESSAGE_LIMIT}** messages in the tracked channel.")


@bot.command(name="resetcount")
@commands.has_permissions(manage_guild=True)
async def reset_count(ctx, member: discord.Member):
    """Reset a user's message count. Usage: !resetcount @user"""
    counts = load_counts()
    counts[str(member.id)] = 0
    save_counts(counts)
    await ctx.send(f"Reset message count for {member.mention}.")


bot.run(TOKEN)
