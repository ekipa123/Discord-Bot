import discord
from discord.ext import commands
import imaplib
import email
import re
import os
from email.utils import parsedate_to_datetime

TOKEN = os.getenv("TOKEN")
EMAIL = os.getenv("EMAIL")
HASLO = os.getenv("HASLO")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def pobierz_kod(tresc):
    wzorce = [
        r'\b\d{6}\b',
        r'\b\d{4}\b',
        r'\b\d{5}\b',
        r'\b\d{7}\b',
        r'\b\d{8}\b',
        r'kod[:\s]*(\d{4,8})',
        r'code[:\s]*(\d{4,8})',
        r'hasło[:\s]*(\d{4,8})',
        r'logowania[:\s]*(\d{4,8})',
    ]
    for wzor in wzorce:
        wynik = re.search(wzor, tresc, re.IGNORECASE)
        if wynik:
            return wynik.group(1) if wynik.groups() else wynik.group(0)
    return None

def sprawdz_poczte():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL, HASLO)
        mail.select("inbox")

        # Pobieramy ostatnie 15 maili (od najnowszych)
        status, wiadomosci = mail.search(None, "ALL")
        if status != "OK" or not wiadomosci[0]:
            mail.logout()
            return None

        numery = wiadomosci[0].split()
        # Bierzemy od najnowszych
        numery = numery[-15:]

        znalezione = []

        for num in reversed(numery):  # od najnowszego
            status, dane = mail.fetch(num, "(RFC822)")
            if status != "OK":
                continue

            msg = email.message_from_bytes(dane[0][1])

            tresc = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            tresc += part.get_payload(decode=True).decode(errors="ignore")
                        except:
                            pass
            else:
                try:
                    tresc = msg.get_payload(decode=True).decode(errors="ignore")
                except:
                    pass

            kod = pobierz_kod(tresc)
            if kod:
                # Oznaczamy jako przeczytany
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

@bot.command()
async def kod(ctx):
    await ctx.send("Sprawdzam pocztę...")
    znaleziony_kod = sprawdz_poczte()
    if znaleziony_kod:
        await ctx.send(f"**Kod do logowania:** `{znaleziony_kod}`")
    else:
        await ctx.send("Nie znalazłem żadnego nowego kodu.")

bot.run(TOKEN)
