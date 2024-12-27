import discord
import google.generativeai as genai
import os
import asyncio

# Discord Setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Gemini Setup
GOOGLE_API_KEY = os.getenv("CLE-API-ICI")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Récupérer l'ID du salon cible depuis une variable d'environnement ou utiliser une valeur par défaut
TARGET_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "ID-DU-SALON-ICI")
print(f"TARGET_CHANNEL_ID: {TARGET_CHANNEL_ID}")

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    print(f"Début de la fonction on_message, Channel ID: {message.channel.id}, TARGET_CHANNEL_ID: {TARGET_CHANNEL_ID}")

    if message.author == client.user:
        print("Message ignoré car envoyé par le bot")
        return

    # Vérification du salon
    if message.channel.id != TARGET_CHANNEL_ID:
        print("Message ignoré car mauvais salon")
        return  # Ignorer si le message n'est pas dans le bon salon

    print("Message reçu dans le bon salon")
    # Vérification que le message n'est pas vide
    if not message.content.strip():
        print("Message vide ou seulement des espaces")
        return

    # Logique pour interagir avec Gemini
    if message.content.startswith("!g"):
        print("Commande !g détectée")
        prompt = message.content[len("!g"):].strip()
        if prompt:
            try:
                print("Prompt:", prompt)
                response = await asyncio.to_thread(model.generate_content, prompt) # Correction ici
                await message.channel.send(response.text)
                print("Réponse envoyée avec succès.")
            except Exception as e:
                print(f"Une erreur est survenue lors de la génération de la réponse: {e}")
                await message.channel.send(f"Une erreur est survenue lors de la génération de la réponse: {e}")
        else:
             print("Pas de prompt après !g")
             await message.channel.send("Veuillez fournir un prompt après la commande !ge.")

client.run("TOKEN-BOT-ICI")
