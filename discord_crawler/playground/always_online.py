import discord
import os
from discord.ext import commands

client = commands.Bot(command_prefix=':', self_bot=True, help_command=None)


@client.event
async def on_ready():
  await client.change_presence(status=discord.Status.online)
  os.system('clear')
  print(f'Logged in as {client.user} (ID: {client.user.id})')

client.run(os.getenv("TOKEN"))

# if __name__ == '__main__':
#   token = os.environ['TOKEN']
#   print(token)