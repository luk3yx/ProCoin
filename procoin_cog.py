import discord # type: ignore
from discord.ext import commands, tasks # type: ignore
from typing import Any, Tuple, Union, TYPE_CHECKING
import os, time

# TODO: Something better
if TYPE_CHECKING:
    Cog = object
else:
    from discord.ext.commands import Cog

# Local imports
from procoin.core import ProCoin
from procoin.items import format_currency
from procoin.store import Error

def _plural(n: Union[int, float]) -> str:
    return '' if n == 1 else 's'

# This can't inherit from both commands.Cog and ProCoin, as attributes such as
# "store" conflict.
class BotInterface(Cog):
    def __init__(self, bot: commands.Bot, directory: str) -> None:
        self.bot = bot
        self.pc = ProCoin(os.path.join(directory, 'items.json'),
                          os.path.join(directory, 'users.json'))

    # TODO: Permission checks
    @commands.command()
    async def reload(self, ctx, *parameters: str) -> None:
        try:
            self.bot.reload_extension(__name__)
        except:
            await ctx.message.add_reaction('❌')
            raise
        else:
            await ctx.message.add_reaction('✅')
        finally:
            if self.bot.user:
                await ctx.message.remove_reaction('⌛', self.bot.user)

    @commands.command()
    async def drop_to_shell(self, ctx, *parameters: str):
        await ctx.message.add_reaction('⌛')
        try:
            import code
            code.interact(local={'self': self, 'bot': self.bot})
        finally:
            if self.bot.user:
                await ctx.message.add_reaction('✅')
                await ctx.message.remove_reaction('⌛', self.bot.user)

    @commands.command(aliases=['buy'])
    async def purchase(self, ctx, *parameters: str) -> None:
        if len(parameters) < 2:
            await ctx.send('Not enough parameters to purchase <item> <qty>.')
            return

        user_id = ctx.author.id
        try:
            qty = int(parameters[-1])
            parameters.pop(-1)
        except ValueError:
            qty = 1
            

        item_string = ' '.join(parameters[:-1])
        try:
            total_cost = self.pc.buy(user_id, item_string, qty)
        except Error as e:
            await ctx.send(str(e))
            return

        await ctx.send(f'<@{user_id}> bought {qty}'\
                       f' {self.pc.items.lookup(item_string)}{_plural(qty)}'
                       f' for {format_currency(total_cost)}.')

    @commands.command()
    async def store(self, ctx, *parameters: str) -> None:
        if parameters:
            await ctx.send(f'This command takes zero parameters ' \
                           f'(not {len(parameters)}).')
            return

        next_update = self.pc.store.last_update + 3600
        delay = round(max(next_update - time.time(), 0) / 60)
        msg: str = self.pc.store.store_string
        msg += f'\r\n*The store resets in {delay} minute{_plural(delay)}.*'
        embed = discord.Embed(title='The Store', description=msg,
                              colour=0xfdd835)
        await ctx.send(embed=embed)

    # This starts with two underscores to try and avoid conflicts with any
    # future commands.Cog internal function, the name will be mangled by
    # Python transparently.
    @tasks.loop(minutes=60.0)
    async def __update_store(self) -> None:
        self.pc.store._generate_store()

def setup(bot):
    bot.add_cog(BotInterface(bot, os.getcwd()))
