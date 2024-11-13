import requests as req
import discord
from discord.ext import commands
from discord import Embed 
import asyncio
import locale
import re
import pandas as pd
import os
from fuzzywuzzy import process
from dotenv import load_dotenv
import logging

load_dotenv()
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
USAJOBS_API_KEY = os.getenv('USAJOBS_API_KEY')
USER_AGENT = os.getenv('USER_AGENT')
FILE_PATH = os.getenv('FILE_PATH', 'agency_codes.csv')
TARGET_CHANNEL = 1305297660650983516
print("Loading environment variables...") #cpoint 2
class JobBot(commands.Bot):
    def __init__(self, csv_file):
        print("Initializing bot...") #cpoint 1
        intents= discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        super().__init__(command_prefix='|', intents=intents)
        #Load environment variables from .env file
        
        
        #Fetch credenntials from environment variables
        
        self.csv_file = os.path.join(os.path.dirname(__file__), csv_file) 
        print("CSV File Loaded...", self.csv_file) #cpoint 4

        if not all([DISCORD_BOT_TOKEN, USAJOBS_API_KEY, USER_AGENT,  self.csv_file]):
            raise ValueError("Missing required environment variables")
        
        logging.basicConfig(level=logging.DEBUG)


        print("current directory:", os.getcwd())

        self.csv_file = csv_file
        self.agency_dict = {}

        #load agency codes and initialize discord bot
        self.agency_dict = self.load_agency_data()
        
    if not DISCORD_BOT_TOKEN:
        raise ValueError("Missing DISCORD_BOT_TOKEN")
    if not USAJOBS_API_KEY:
        raise ValueError("Missing USAJOBS_API_KEY")
    if not USER_AGENT:
        raise ValueError("Missing USER_AGENT")
    if not FILE_PATH:
        raise ValueError("Missing FILE_PATH")


    async def setup_hook(self):
        #register commands)
        await self.setup_bot()
        print("running setup hook....") #cpoint 5
    
    async def on_ready(self):
        #Method is called when the bot is ready
        print(f'Logging in as {self.user} (ID: {self.user.id})')
        print("Bot is ready and connected to Discord")
    
    
    
    async def setup_bot(self):
        #register the 

    

        @self.command()
        async def search(ctx, *, query):
            flags = self.parse_flags(query)
            jobs = self.get_jobs(flags)
            if ctx.channel.id != TARGET_CHANNEL:
                await ctx.send("Please use the bot in the designated channel")
                return 

            if 'SearchResult' in jobs and 'SearchResultItems' in jobs['SearchResult']:
                results= jobs['SearchResult']['SearchResultItems']
                if not results:
                    await ctx.send("No jobs found")
                    return
                # Break results into pages of 5 jobs each
                pages = [results[i:i+5] for i in range(0, len(results), 6)]
                current_page = 0
                locale.setlocale(locale.LC_ALL, 'en_US.UTF-8') 
                #generate embed
            
            def generate_embed(page_num):
                    embed = Embed(title="Job Search Results", color=0x00ff00)
                    for item in pages[page_num]:
                        min_salary = item['MatchedObjectDescriptor']['PositionRemuneration'][0]['MinimumRange']
                        max_salary = item['MatchedObjectDescriptor']['PositionRemuneration'][0]['MaximumRange']
                        embed.add_field(
                            name=item['MatchedObjectDescriptor']['PositionTitle'], 
                        value=(
                            f"**Organization**: {item['MatchedObjectDescriptor']['OrganizationName']}\n"
                            f"**Location**: {item['MatchedObjectDescriptor']['PositionLocationDisplay']}\n"
                            f"**Who May Apply**: {item['MatchedObjectDescriptor']['UserArea']['Details']['WhoMayApply']['Name']}\n"
                            f"Minimum Salary: "
                            f"{locale.currency(float(min_salary), grouping=True) if min_salary != 'N/A' else 'N/A'}\n"
                            f"Maximum Salary: "
                            f"{locale.currency(float(max_salary), grouping=True) if max_salary != 'N/A' else 'N/A'}\n"

                            f"[Apply Here]({item['MatchedObjectDescriptor']['PositionURI']})"
                            
                        ),       
                        inline=False
                        )  
                    embed.set_footer(text=f"Page {page_num + 1} of {len(pages)}")
                    return embed
                

                    
            message = await ctx.send(embed=generate_embed(current_page))

                    #Add reaction buttons
            await message.add_reaction('◀️')
            await message.add_reaction('▶️')


                    #reaction handler
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️"] and reaction.message.id == message.id
            


            while True:
                try:
                    #wait for reaction
                    reaction, user = await self.wait_for('reaction_add', timeout=600.0, check=check)

                    if str(reaction.emoji) == "▶️" and current_page < len(pages) - 1:
                        current_page += 1
                        await message.edit(embed=generate_embed(current_page))
                    elif str(reaction.emoji) == "◀️" and current_page > 0:
                        current_page -= 1
                        await message.edit(embed=generate_embed(current_page))

                    #remove the user's reaction
                    await message.remove_reaction(reaction, user)

                except asyncio.TimeoutError:
                    break


        



            await message.clear_reactions()
        channel = self.get_channel(1305297660650983516) #Channel ID


        #run the bot using the token

    def load_agency_data(self):
        df = pd.read_csv(self.csv_file)
        return self.create_comb_dict(df)
    


    def create_comb_dict(self, df):
        agency_dict = {}
        for _, row in df.iterrows():
            agency_name = row['Agency Name'].strip().lower()
            agency_code = row['Agency Code']
            agency_dict[agency_name] = agency_code

        shorthand = self.generate_shorthand(df)
        agency_dict.update(shorthand)

        for code in df['Agency Code']:
            agency_dict[code.lower()] = code
        return agency_dict
    


    def generate_shorthand(self, df):
        shorthand_names = {}
        for _, row in df.iterrows():
            agency_name = row['Agency Name']
            agency_code = row['Agency Code']
            words = agency_name.split()
            
            # Add acronym if there are multiple words in the agency name
            if len(words) > 1:
                acronym = ''.join(word[0] for word in words).upper()
                shorthand_names[acronym] = agency_code

                # If the name contains "Department", add the second word as shorthand
                if 'Department' in words:
                    shorthand = words[1].lower()
                    shorthand_names[shorthand] = agency_code

            # Add the first word as shorthand regardless of length
            shorthand_names[agency_name.split()[0].lower()] = agency_code

        return shorthand_names

    def find_closest_agency(self, user_input):
        user_input = user_input.strip().lower()
        match = process.extractOne(user_input, self.agency_dict.keys())

        threshold = 80
        if match and match[1] >= threshold:
            return self.agency_dict[match[0]]
        
        return None

    def parse_flags(self, query):
        flags = {
            'Keyword': None,
            'LocationName': None,
            'PositionTitle': None,
            'min_salary': None,
            'max_salary': None,
            'Organization': None,
            'AgencyCode': None
        }

        matches = re.findall(r'-(\w)\s+([\w\s,]+)', query)
        for flag, value in matches:
            value = value.strip()
            if flag == 'l':
                formatted_loc = value.replace(" ", "%20")
                flags['LocationName'] = formatted_loc.replace(',', '')
                
            elif flag == 'p':
                flags['PositionTitle'] = value.replace(',', '')
            elif flag == 'min':
                flags['min_salary'] = value.replace(',', '')
            elif flag == 'max':
                flags['max_salary'] = value.replace(',', '')
            elif flag == 'o':
                agency_codes =  self.find_closest_agency(value)
                if agency_codes:
                    flags['Organization'] = agency_codes
            

            # Remove the flag from the query
        keyword = re.sub(r'-(\w+)\s+[\w\s,]+', '', query).strip()
        if keyword:
            flags['Keyword'] = keyword

        return flags
    

    





    def get_jobs(self, flags):
        url= 'https://data.usajobs.gov/api/search'
        method= 'GET'
        headers = {
            "Host": "data.usajobs.gov",
            "User-Agent": USER_AGENT,
            "Authorization-Key": USAJOBS_API_KEY
        }
        params = {
            'Keyword': flags['Keyword'] if flags['Keyword'] else '',
            'LocationName': flags['LocationName'] if flags['LocationName'] else '',
            'PositionTitle': flags['PositionTitle'] if flags['PositionTitle'] else '',
            'RemunerationMinimumAmount': flags['min_salary'] if flags['min_salary'] else '',
            'RemunerationMaximumAmount': flags['max_salary'] if flags['max_salary'] else '',
            'Organization': flags['Organization'] if flags['Organization'] else '',

        }

        # print("API ParametersL", params)

        response = req.get(url, headers=headers, params=params)
        # print("API Sratus Code:", response.status_code)
        #print("API Response Content:", response.content)

        data = response.json()
        return data

    
#Discord Bot Setup


    
myBot = JobBot(FILE_PATH)
myBot.run(DISCORD_BOT_TOKEN)
