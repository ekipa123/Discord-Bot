import discord
from discord.ext import commands
import imaplib
import email
import re
import os
from bs4 import BeautifulSoup

TOKEN = os.getenv("TOKEN")
EMAIL = os.getenv("EMAIL")
HASLO = os.getenv("HASLO")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def pobierz_kod(tresc):
    wzorce = [
        r'kod logowania[:\s]*(\d{6})',
        r'kod[:\s]*(\d{6})',
        r'code[:\s]*(\d{6})',
        r'logowania[:\s]*(\d{6})',
        r'\b(\d{6})\b',
    ]
    for wzor in wzorce:
        wynik = re.search(wzor, tresc, re.IGNORECASE)
        if wynik:
            return wynik.group(1)
    return None

def sprawdz_poczte():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL, HASLO)
        mail.select("inbox")

        # Szukamy TYLKO nieprzeczytanych wiadomości (UNSEEN) od podanego nadawcy
        status, wiadomosci = mail.search(None, '(UNSEEN FROM "hello@maturazlewusem.pl")')
        if status != "OK" or not wiadomosci[0]:
            mail.logout()
            return None

        numery = wiadomosci[0].split()[-10:]

        for num in reversed(numery):
            status, dane = mail.fetch(num, "(RFC822)")
            if status != "OK":
                continue

            msg = email.message_from_bytes(dane[0][1])
            tresc = ""

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    try:
                        payload = part.get_payload(decode=True)
                        if not payload:
                            continue
                        tekst = payload.decode(errors="ignore")

                        if content_type == "text/plain":
                            tresc += tekst + " "
                        elif content_type == "text/html":
                            soup = BeautifulSoup(tekst, "html.parser")
                            tresc += soup.get_text(separator=" ") + " "
                    except:
                        continue
            else:
                try:
                    tresc = msg.get_payload(decode=True).decode(errors="ignore")
                except:
                    pass

            kod = pobierz_kod(tresc)
            if kod:
                # Oznaczamy maila jako przeczytany, żeby następnym razem bot go pominął
                mail.store(num, '+FLAGS', '\\Seen')
                mail.logout()
                return kod

        mail.logout()
        return None

    except Exception as e:
        print(f"Błąd: {e}")
        return None

@bot.event
async def on_ready():
    print(f"Bot działa jako {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Zsynchronizowano {len(synced)} komend slash")
    except Exception as e:
        print(f"Błąd synchronizacji: {e}")

@bot.tree.command(name="kod", description="Sprawdza najnowszy kod z poczty")
async def kod_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    znaleziony_kod = sprawdz_poczte()
    if znaleziony_kod:
        await interaction.followup.send(f"**Kod logowania do kursu maturalnego:** `{znaleziony_kod}`")
    else:
        await interaction.followup.send(f"**Nowy kod logowania nie jest jeszcze dostępny.**")

@bot.command()
async def kod(ctx):
    await ctx.send("Sprawdzam pocztę...")
    znaleziony_kod = sprawdz_poczte()
    if znaleziony_kod:
        await ctx.send(f"**Kod logowania do kursu maturalnego:** `{znaleziony_kod}`")
    else:
        await ctx.send(f"**Nowy kod logowania nie jest jeszcze dostępny.**")

bot.run(TOKEN)
