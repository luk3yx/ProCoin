from discord.ext import commands, tasks
from typing import Any, Tuple

# Local imports
from procoin.core import ProCoin


class BotInterface(commands.Cog, ProCoin):

    def __init__(self):
         super().__init__('items.json', 'users.json')

    @commands.command
    # both arguments need type annotations
    async def purchase(self, ctx, *parameters) -> None:
        
        if len(parameters) < 2:
            await ctx.send('Not enough parameters to purchase <item> <qty>.')
            
        user_id = ctx.author.id
        item_string = ''.join(parameters[:-1])
        try:
          qty = int(parameters[-1])
        except ValueError:
          await ctx.send('Quantity must be an integer.')
        
        transaction_result = self.buy(user_id, item_string, qty)
        if not transaction_result:
          await ctx.send('Transaction failed. We need some actual exceptions'\
                         ' instead of just True or False.')
                         
        await ctx.send(f'<@{user_id}> bought {qty}'\
                       f' {self.items.lookup(item_string)}')
                       
    @tasks.loop(minutes=60.0)
    def _update_store(self) -> None:
        self._generate_store()