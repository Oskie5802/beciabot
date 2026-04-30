import os
import discord
from discord.ext import commands
from search import StatutSearch
from keep_alive import keep_alive

TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

searcher = StatutSearch(
    files={
        "Statut Zespołu Szkół": "statut-zespolu.pdf",
        "Statut Technikum": "statuttechnikum.pdf",
    }
)


@bot.event
async def on_ready():
    print(f"Becia gotowa! Zalogowano jako {bot.user}")
    await bot.tree.sync()


@bot.hybrid_command(name="szukaj", description="Wyszukaj informację w statucie szkoły")
async def szukaj(ctx, *, pytanie: str):
    await ctx.defer()
    wynik = await searcher.odpowiedz(pytanie, gemini_key=GEMINI_KEY)
    embed = discord.Embed(
        title=f"📖 {pytanie[:100]}",
        description=wynik["odpowiedz"],
        color=discord.Color.blue(),
    )
    embed.set_footer(text=f"Źródło: {wynik['zrodlo']}")
    await ctx.reply(embed=embed)


@bot.hybrid_command(name="pomoc", description="Jak używać Beci?")
async def pomoc(ctx):
    embed = discord.Embed(
        title="📚 Becia – Bot Statutowy",
        description=(
            "Jestem botem, który wyszukuje informacje w statucie szkoły.\n\n"
            "**Użycie:**\n"
            "`!szukaj <pytanie>` lub `/szukaj <pytanie>`\n\n"
            "**Przykłady:**\n"
            "`!szukaj ile godzin nieusprawiedliwionych można mieć?`\n"
            "`!szukaj jakie są prawa ucznia?`\n"
            "`!szukaj kiedy można dostać stypendium?`\n\n"
            "**Statuty:**\n"
            "• Statut Zespołu Szkół Technicznych i Branżowych\n"
            "• Statut Technikum im. Bohaterów Westerplatte"
        ),
        color=discord.Color.green(),
    )
    await ctx.reply(embed=embed)


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        content = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if content:
            async with message.channel.typing():
                wynik = await searcher.odpowiedz(content, gemini_key=GEMINI_KEY)
                embed = discord.Embed(
                    title=f"📖 {content[:100]}",
                    description=wynik["odpowiedz"],
                    color=discord.Color.blue(),
                )
                embed.set_footer(text=f"Źródło: {wynik['zrodlo']}")
                await message.reply(embed=embed)
        else:
            await message.reply("Hej! Zapytaj mnie o coś ze statutu, np. `!szukaj jakie są prawa ucznia?`")
    await bot.process_commands(message)


keep_alive()
bot.run(TOKEN)
