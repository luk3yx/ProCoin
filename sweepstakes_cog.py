import discord
from discord.ext import commands
from random import choice, randint

from procoin.core import ProCoin


class sweepstakes(commands.Cog):

    __slots__ = ('bot', 'next_event', 'next_item', 'in_race')
    def __init__(self, bot: commands.Bot):
      self.bot = bot
      self.next_event = 1
      self.next_item = None
      self.in_race = False
      
    @commands.Cog.listener()
    async def on_message(self, message) -> None:
        if message.author.bot or message.guild is None:
            return
            
        if not self.in_race:
            self.next_event -= 1
        else:    
            if self.bot.user.mentioned_in(message):
                self.in_race = False
                await self.give_prize(message)
                return

        if self.next_event <= 0:
            self.next_event = 1
            self.set_new_item()
            if randint(0, 1) == 1:
                # Do sweepstakes
                await self.sweepstake(message)

            else:
                # Start a race
                await message.channel.send(f'The next person to @mention me '\
                    f' will receive 1 {self.next_item}!')
                self.in_race = True
                
    async def sweepstake(self, message):
        user = self.pc.users.get_or_create(message.author.id)
        item = self.pc.items.get_item(self.next_item)
        user.add_item(item, 1)
        await message.channel.send('Sweepstakes! '\
            f' {message.author.mention} won 1 {self.next_item}!')
        
    async def give_prize(self, message):
        user = self.pc.users.get_or_create(message.author.id)
        item = self.pc.items.get_item(self.next_item)
        user.add_item(item, 1)
        await message.channel.send('Congratulations! '\
            f' {message.author.mention} won the {self.next_item}!')
            
    def set_new_item(self):
        self.next_item = choice(list(self.pc.items.items.keys()))
                
    @property
    def pc(self) -> ProCoin:
        cog = self.bot.get_cog('General commands')
        assert cog
        return cog.pc
                    
def setup(bot):
    bot.add_cog(sweepstakes(bot))