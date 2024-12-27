import discord
import google.generativeai as genai
import os
import asyncio
from dotenv import load_dotenv
import ssl
import logging
import time

load_dotenv()

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Discord Setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Gemini Setup
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Récupérer l'ID du salon cible depuis une variable d'environnement ou utiliser une valeur par défaut
TARGET_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
logger.info(f"TARGET_CHANNEL_ID: {TARGET_CHANNEL_ID}")

#Ajout de cette ligne afin de désactiver la vérification du certificat.
ssl._create_default_https_context = ssl._create_unverified_context

# Variable pour le suivi de l'activité
last_activity = time.time()

async def reconnect_with_backoff():
    """Reconnecte le bot avec un temps d'attente exponentiel."""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to reconnect to Discord... (Attempt {attempt+1})")
            await client.connect()
            return True  # Connection réussi, on sort
        except Exception as e:
            logger.error(f"Reconnection failed (Attempt {attempt+1}). {e}")
            if attempt == max_retries-1:
                return False #On sort apres 5 tentatives raté
            await asyncio.sleep(2 ** attempt) # On attend 2, 4, 8, 16, 32 sec avant de réessayer
    return False

async def check_inactivity():
    """Vérifie l'inactivité et déconnecte ou reconnecte le bot si nécessaire."""
    global last_activity
    max_inactivity = 300 # 5 minutes en secondes
    while True:
        await asyncio.sleep(60) #Vérifie toutes les minutes
        if time.time() - last_activity > max_inactivity:
            logger.warning("Inactivity timeout exceeded. Disconnecting and reconnecting...")
            await client.close()
            if not await reconnect_with_backoff():
                 logger.error("Max reconnections attempts failed, closing script")
                 await client.close() #Ferme la connection si on arrive pas à se reconnecter
                 break
            last_activity = time.time()


@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user}')
    #Démarre la tache de vérification d'inactivité en tâche de fond
    client.loop.create_task(check_inactivity())



@client.event
async def on_message(message):
    global last_activity
    last_activity = time.time() # Met à jour la dernière activité
    logger.info(f"Début de la fonction on_message, Channel ID: {message.channel.id}, TARGET_CHANNEL_ID: {TARGET_CHANNEL_ID}")
    logger.info(f"GOOGLE_API_KEY récupérée dans le code: {GOOGLE_API_KEY}")

    if message.author == client.user:
        logger.info("Message ignoré car envoyé par le bot")
        return

    # Vérification du salon
    if message.channel.id != TARGET_CHANNEL_ID:
        logger.info("Message ignoré car mauvais salon")
        return  # Ignorer si le message n'est pas dans le bon salon

    logger.info("Message reçu dans le bon salon")
    # Vérification que le message n'est pas vide
    if not message.content.strip():
        logger.info("Message vide ou seulement des espaces")
        return

    # Logique pour interagir avec Gemini
    if message.content.startswith("!gemini"):
        logger.info("Commande !gemini détectée")
        prompt = message.content[len("!gemini"):].strip()
        if prompt:
            try:
                logger.info(f"Prompt: {prompt}")
                response = await asyncio.to_thread(model.generate_content, prompt) # Correction ici
                if len(response.text) > 2000:
                    response_text = response.text[:1997] + "..." # Tronque et ajoute ... à la fin
                else:
                    response_text = response.text
                await message.channel.send(response_text)
                logger.info("Réponse envoyée avec succès.")
            except Exception as e:
                logger.error(f"Une erreur est survenue lors de la génération de la réponse: {e}")
                await message.channel.send(f"Une erreur est survenue lors de la génération de la réponse: {e}")
        else:
            logger.info("Pas de prompt après !gemini")
            await message.channel.send("Veuillez fournir un prompt après la commande !gemini.")


client.run("TOKEN-BOT-ICI")
