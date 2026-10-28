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

#import all of the cogs
from src.help_cog import help_cog
from src.music_cog import music_cog




TOKEN = os.environ["DISCORD_TOKEN"]




rjecnikHrasta = {}
rjecnikHrasta.update({100: ["drvosječa", "sjekira", "pilana", "stolar", "pila", "sječa"]})
rjecnikHrasta.update({80: ["požar", "vatra", "napalm", "orange", "munja", "požar"]})
rjecnikHrasta.update({60: ["industrija", "saruman", "baba jaga", "namještaj"]})




#STOPALA DIO

stopala_list = ["https://img.freepik.com/premium-photo/beauty-anime-girl-feet-sexy-bikini-summer-bodylance_483949-10335.jpg",
           "https://i.ytimg.com/vi/bev93eKSgcI/maxresdefault.jpg",
           "https://www.picclickimg.com/kCIAAOSwiO9fkKh4/Bleach-Orihime-Feet-Sexy-Anime-Girl-Pack-Of.webp",
           "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRAqB-AELlJClw2Neanp_ijZIrzjXtVvfSbYnD1zf--1npP7-kf0-jjr4JWDLaFgqQ_Kis&usqp=CAU",
           "https://qph.cf2.quoracdn.net/main-qimg-85e2691a8ddd143018b094734e25fc7b-lq",
           "https://pbs.twimg.com/media/DiWhBSkWAAAHrQQ?format=jpg&name=medium",
           "https://www.mensjournal.com/.image/c_limit%2Ccs_srgb%2Cq_auto:good%2Cw_618/MTk2MTM2MjcyNDY5MTA4MjI5/mj-618_348_6-products-for-cleaner-healthier-feet.webp"
           ]


intent = discord.Intents.default()
intent.typing = True
intent.messages = True
intent.guilds = True
intent.message_content = True
intent.members  = True
#intent.read_channel_history = True


client = commands.Bot(command_prefix='', intents=intent, case_insensitive=True)

@client.command()
async def povijest(ctx, *args):
    #handleanje argumenata
    argumenti = ' '.join(args)
    argumenti = argumenti.split(' ')
    if (len(argumenti) < 2):
        await ctx.send("Premalo argumenata, koristi $povijest korisnik kanal")
        return
    elif (len(argumenti) > 2):
        await ctx.send("Previse argumenata, koristi $povijest korisnik kanal")
        return
    
    korisnik = argumenti[0]
    kanal = argumenti[1]

    korisnikDiscord = ""

    kanalDiscord = ""

    korisnici = []

    for korisnikTemp in ctx.guild.members:
        korisnici.append(korisnikTemp.name)
        #print(korisnikTemp.name)
        if (korisnikTemp.name == korisnik):
            korisnikDiscord = korisnikTemp

    kanali = []

    for kanalTemp in ctx.guild.channels:
        kanali.append(kanalTemp.name)
        #print(kanalTemp.name)
        if (kanalTemp.name == kanal):
            kanalDiscord = kanalTemp

    

    #print(korisnici)
    #print(kanali)

    if (korisnikDiscord == ""):
        await ctx.send("Taj korisnik ne postoji, koristi discord ime, a ne nadima")
        return

    if (kanalDiscord == ""):
        await ctx.send("Taj kanal ne postoji")
        return

    print(korisnikDiscord.name)
    print(kanalDiscord.name)

    ##odredi kanal
    thisChannel = kanalDiscord
    
    collectedMessages = []
    #sakupi poruke
        
    async for messageInHistory in thisChannel.history(limit = None):
        if messageInHistory.author == korisnikDiscord and len(messageInHistory.content) > 5 and len(messageInHistory.content.split(' ')) > 1:
                
            collectedMessages.append(messageInHistory.content)
            
        
    #posalji poruke korisniku
    # write to file
    with open("povijest.txt", "w", encoding="utf-8") as file:
        file.write('\n'.join(collectedMessages))
    
    # send file to Discord in message
    with open("povijest.txt", "rb") as file:
        await ctx.author.send("Poštovani:", file=discord.File(file, "povijest.txt"))

    await ctx.send("Poslao povijest u dm")
    #await message.author.send('\n'.join(collectedMessages))

    return

@client.command()
async def stopala(ctx, *args):
    await ctx.send("<:ramirez:800772578280865864>")
    await ctx.author.send(stopala_list[random.randint(0, len(stopala_list) - 1)])

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')



@client.event
async def on_message(message):

    
    if (message.author == client.user):
        return
    
    

    if (str(message.channel) != "proplanak" and str(message.channel) != "mudrosti-mističnoga-hrasta"):
        return

    
    breakoje = False
    for kljuc in rjecnikHrasta.keys():

        for antikrist in rjecnikHrasta.get(kljuc):
            #print(antikrist)
            if (antikrist in message.content.lower()):
                sansa = kljuc
                
                if (len(message.content.lower()) > len(antikrist)):
                    sansa -= 20
                


                if(random.randint(1, 100) > sansa):
                    continue

                rand = random.randint(1, 300)
                if (rand == 100):
                    await message.channel.send("MRZIM DRVOSJEČE!")
                    
                elif (rand == 300):
                    await message.channel.send("Ja mrzim vatru!")
                    
                elif (rand == 200):
                    await message.channel.send("мрзим Дрвосјече!")
                    
                elif (rand == 69):
                    await message.channel.send(f"Mrzim {message.author.nick}!")
                else:
                    await message.channel.send("Mrzim industriju!")
                    
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
                            await message.channel.send("MRZIM DRVOSJEČE!")
                            
                        elif (rand == 300):
                            await message.channel.send("Ja mrzim vatru!")
                            
                        elif (rand == 200):
                            await message.channel.send("мрзим Дрвосјече!")
                            
                        elif (rand == 69):
                            await message.channel.send(f"Mrzim {message.author.nick}!")
                        else:
                            await message.channel.send("Mrzim industriju!")
                                                        
                        breakoje = True
                        break
        

        if (breakoje):
            break



            
            
    

    if ("hrast" in message.content.lower()):
        rand = random.randint(1,4)

        if (rand == 1):
            #mrzim
            await message.channel.send(f"Mudar si ko kurac {message.author.nick}")
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
                await message.channel.send(f"Pičko nisi u šumi {message.author.nick}")
            
        if (rand == 3):
            #volim!
            await message.channel.send(f"Volim te {message.author.nick}")
        
        if (rand == 4):
            #neutralan
            await message.channel.send(f"Ok {message.author.nick}")
    
    await client.process_commands(message)




client.remove_command('help')


async def main():
    async with client:
        await client.add_cog(help_cog(client))
        await client.add_cog(music_cog(client))
        await client.start(TOKEN)

asyncio.run(main())
