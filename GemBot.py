import discord
import google.generativeai as genai
import os
import asyncio
from dotenv import load_dotenv
import ssl
import logging
import time
import tracemalloc

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


#Ajout de cette ligne afin de désactiver la vérification du certificat.
ssl._create_default_https_context = ssl._create_unverified_context

# Variable pour le suivi de l'activité
last_activity = time.time()

async def send_long_message(channel, text):
    sentences = text.split(". ")
    chunk_size = 1990
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 2 < chunk_size:
            current_chunk += sentence + ". "
        else:
            try:
                await asyncio.wait_for(channel.send(current_chunk), timeout=5) #ajout du timeout
            except asyncio.TimeoutError:
                logger.error(f"Error during sending message. Timed out: {current_chunk}")
            current_chunk = sentence + ". "
    if current_chunk:
        try:
                await asyncio.wait_for(channel.send(current_chunk), timeout=5) #ajout du timeout
        except asyncio.TimeoutError:
                logger.error(f"Error during sending message. Timed out: {current_chunk}")

tracemalloc.start()

@client.event
async def on_ready():
    logger.info(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    global last_activity
    last_activity = time.time() # Met à jour la dernière activité
    logger.info(f"Début de la fonction on_message, Channel ID: {message.channel.id}")
    logger.info(f"GOOGLE_API_KEY récupérée dans le code: {GOOGLE_API_KEY}")
    logger.info(f"Contenu du message reçu: {message.content}")

    if message.author == client.user:
        logger.info("Message ignoré car envoyé par le bot")
        return

    logger.info("Message reçu dans un bon salon")
    # Vérification que le message n'est pas vide
    if not message.content.strip():
        logger.info("Message vide ou seulement des espaces")
        return

    # Logique pour interagir avec Gemini
    if message.content.startswith("!g"):
        logger.info("Commande !g détectée")
        prompt = message.content[len("!g"):].strip()
        if prompt:
            try:
                logger.info(f"Prompt: {prompt}")
                response = await asyncio.to_thread(model.generate_content, prompt) # Correction ici
                logger.info(f"Réponse Gemini: {response.text}")
                await send_long_message(message.channel, response.text)
                logger.info("Réponse envoyée avec succès.")
            except Exception as e:
                 logger.error(f"Une erreur est survenue lors de la génération de la réponse: {e}")
                 await message.channel.send(f"Une erreur est survenue lors de la génération de la réponse: {e}")
        else:
           logger.info("Pas de prompt après !g")
           await message.channel.send("Veuillez fournir un prompt après la commande !g.")

    else :
       logger.info(f"Message non reconnu: {message.content}") #Log les messages que le bot ne reconnait pas
    try: #Catch all clause pour capturer toutes les erreurs possibles
        current, peak = tracemalloc.get_traced_memory() # On récupère l'utilisation de mémoire
        logger.info(f"Current memory usage is {current / 10**6:.2f}MB; Peak was {peak / 10**6:.2f}MB") # On affiche l'utilisation de mémoire
    except Exception as e:
        logger.error(f"Error during memory check: {e}") # Si une erreur se produit lors de la vérification de la mémoire


client.run("TOKEN-DU-BOT-ICI")
