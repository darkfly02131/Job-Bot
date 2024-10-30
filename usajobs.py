import requests as req
import discord
from discord.ext import commands
from discord import Embed 
# Core Variables
host = 'data.usajobs.gov'
user_agent = 'zacharylord999@gmail.com'
api_key = 'Hc5/uUUzL6tqNIvsCTHd9TQXJDkNhPEfBaNoLI8GdGY='


def get_jobs(query):
    url= 'https://data.usajobs.gov/api/search'
    method= 'GET'
    headers = {
        "Host": host,
        "User-Agent": user_agent,
        "Authorization-Key": api_key
    }
    params = {
        'Keyword': query
    }


    response = req.get(url, headers=headers, params=params)
    data = response.json()
    return data

#Discord Bot Setup
intent = discord.Intents.default()
bot = commands.Bot(command_prefix='|', intents=intent)
intent.message_content= True
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@bot.command()
async def search(ctx, *, query):
    jobs = get_jobs(query)
    if 'SearchResult' in jobs and 'SearchResultItems' in jobs['SearchResult']:
        results= jobs['SearchResult']['SearchResultItems']
        if results:
            embed = Embed(title="Job Search Results", color=0x00ff00)
            for item in results[:5]:
                embed.add_field(
                name = item['MatchedObjectDescriptor']['PositionTitle'],
                value = (
                    f"\n"
                    f"Organization: {item['MatchedObjectDescriptor']['OrganizationName']}\n"
                    f"Location: {item['MatchedObjectDescriptor']['PositionLocationDisplay']}\n"
                    f"URL: {item['MatchedObjectDescriptor']['PositionURI']}\n"
                    f"Apply here: {item['MatchedObjectDescriptor']['ApplyURI'][0]}\n"




                ), inline=False
                )

            await ctx.send(embed=embed)
            
            
            
            
        else:
            await ctx.send("No jobs found")
    else:
        await ctx.send("Error retrieving jobs")
    
    channel = bot.get_channel(1287542979917119579) #Channel ID
    


bot.run('MTI4NzUxMjAyMTA2MzA0MTA2NA.GDhDVt.MbnHH-gS0Mw4g2yDqDbul0QIzCAGM_1v62qRBk')




