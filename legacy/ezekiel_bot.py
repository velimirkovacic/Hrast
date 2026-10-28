# bot.py
import os

import discord

discord.opus.load_opus("libopus.so.0")


from discord.ext import commands

import time

import datetime

import Levenshtein

import random

import asyncio

TOKEN = os.environ["DISCORD_TOKEN"]

intent = discord.Intents.default()
intent.typing = True
intent.messages = True
intent.guilds = True
intent.message_content = True
intent.members  = True
#intent.read_channel_history = True


client = commands.Bot(command_prefix='', intents=intent, case_insensitive=True)


antikristi = ["nato", "un", "plave kacige", "murija", "policija", "milicija", "antikrist", "amerika", "sotona", "satan", "lucifer", "đav", "murja", "pig", "svinj", "liberal", "cia", "nsa", "dea", "fbi", "joe", 
"fed", "glowie", "hitler", "izrael", "israel", "sad", "usa", "wumbolo", "todori", "globali", "elon", "kissinger", "eu", "vrag", "nafo", "srbi", "epstein", "gates", "soroš", "musk", "biden", "staljin"]



rjecnikAntikrista = {}

rjecnikAntikrista.update({100: ["nato", "plave kacige", "antikrist", "amerikan", "amerika", "sotona", "satan", "lucifer", "đav", "sad", "usa", "izrael", "israel", "vrag", "hitler"]})
rjecnikAntikrista.update({80: ["un", "murija", "policija", "milicija", "cia", "nsa", "fbi", "fed", "feds", "glowie", "mussolini", "globalisti", "elon", "kissinger", "eu"]})
rjecnikAntikrista.update({60: ["nafo", "srbi", "wumbolo", "pig", "svinje", "srbija"]})
rjecnikAntikrista.update({40: ["imune", "vax", "redit", "twit", "fejs", "liberal", "trump", "ugar"]})
rjecnikAntikrista.update ({20: ["split", "quagmire", "ministar", "vlada", "nda", "dea"]})



@client.event
async def on_message(message):

    

    #print(guild.channels)

    if (message.author == client.user):
        return
    
    

    if (str(message.channel) != "proplanak" and str(message.channel) != "mudrosti-mističnoga-hrasta"):
        return

    
    breakoje = False
    for kljuc in rjecnikAntikrista.keys():

        for antikrist in rjecnikAntikrista.get(kljuc):
            #print(antikrist)
            if (antikrist in message.content.lower()):
                sansa = kljuc
                
                if (len(message.content.lower()) > len(antikrist)):
                    sansa -= 20
                


                if(random.randint(1, 100) > sansa):
                    continue

                rand = random.randint(1, 300)
                if (rand == 100):
                    await message.channel.send("MRZIM ANTIKRISTA!")
                    
                elif (rand == 300):
                    await message.channel.send("Antikrista mrzim ja!")
                    
                elif (rand == 200):
                    await message.channel.send("мрзим антикриста!")
                    
                elif (rand == 69):
                    await message.channel.send(f"Mrzim {message.author.nick}!")
                else:
                    await message.channel.send("Mrzim antikrista!")
                    
                breakoje = True
                break
            else:
                #testiraj levenstajn omjer za svaku rijec u poruci, ako je > 8 onda je dobro
                for rijec in message.content.lower().split(' '):
                    if (Levenshtein.ratio(rijec, antikrist) >= 0.8):
                        sansa = kljuc

                        if (len(message.content.lower()) > len(antikrist)):
                            sansa -= 20

                        if(random.randint(1, 100) > sansa - 20):
                            continue

                        print(rijec)
                        print(antikrist)

                        rand = random.randint(1, 300)
                        if (rand == 100):
                            await message.channel.send("MRZIM ANTIKRISTA!")
                            
                        elif (rand == 300):
                            await message.channel.send("Antikrista mrzim ja!")
                            
                        elif (rand == 200):
                            await message.channel.send("мрзим антикриста!")
                            
                        elif (rand == 69):
                            await message.channel.send(f"Mrzim {message.author.nick}!")
                            
                        else:
                            await message.channel.send("Mrzim antikrista!")
                            
                        breakoje = True
                        break
        

        if (breakoje):
            break



            
            
    
    if ("bajo jajo" in message.content.lower()):
        await message.channel.send("Ja ci dam kurwa bajo jajo ty pierdolony bambusie w dupe zajebany jest do kurwy nedzy wikend zamknij te morde kurwa")
    
    if ("ezekiel" in message.content.lower()):
        rand = random.randint(1,5)

        if (rand == 1):
            #mrzim
            await message.channel.send(f"Glup si ko kurac {message.author.nick}")
            await message.author.timeout(datetime.timedelta(seconds=60), reason="Glup")
        
        if (rand == 2):
            #dolazi
            await message.channel.send(f"Dolazim po tebe {message.author.nick}")
        
            if (message.author.voice != None):
                channel = message.author.voice.channel
                await channel.connect()
                time.sleep(2)
                voice_client = message.guild.voice_client
                await message.author.move_to(None)
                await voice_client.disconnect()
            else:
                time.sleep(2)
                await message.channel.send(f"Pičko nisi u voisu {message.author.nick}")
            
        if (rand == 3):
            #volim!
            await message.channel.send(f"Volim te {message.author.nick}")
        
        if (rand == 4):
            #Polski
            await message.channel.send(f"Cholera, czy to {message.author.nick}")
            time.sleep(2)
            await message.channel.send(f"Har har har har har har har")
        
        if (rand == 5):
            #neutralan
            await message.channel.send(f"Ok {message.author.nick}")
    
    if ("gunther" in message.content.lower() or "gunter" in message.content.lower()):
        if random.randint(0, 10) == 1:
            await message.channel.send("https://pbs.twimg.com/media/GFCFdzXW4AARiz8?format=jpg&name=large")
        else:
            await message.channel.send("I call for Austria 🇦🇹 Kosovo 🇽🇰 Bosnia 🇧🇦 Ukraine 🇺🇦 to join @nato 2024 \nI call for NATO Allies Albania 🇦🇱 Montenegro 🇲🇪 North Macedonia 🇲🇰 to join European Union 🇪🇺 2024 \nI call for Ukraine 🇺🇦 Bosnia 🇧🇦 Kosovo 🇽🇰 join #EU37 2029I call UK 🇬🇧 rejoin 2029 \nSerbia must be isolated!")
    await client.process_commands(message)
    