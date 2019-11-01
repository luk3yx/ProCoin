import discord # type: ignore
from discord.ext import commands, tasks # type: ignore
from typing import Any, Optional, Tuple, Union, TYPE_CHECKING
import os, time

# TODO: Something better
if TYPE_CHECKING:
    class Cog:
        @classmethod
        def listener(self, name: Optional[str] = None):
            return lambda func : func
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

    @commands.command(aliases=['money'])
    async def bal(self, ctx) -> None:
        user = self.pc.users.get_or_create(ctx.author.id)
        await ctx.send(f'{ctx.author.mention} has '
                       f'{format_currency(user.balance)}')

    @commands.command()
    async def boost(self, ctx) -> None:
        user = self.pc.users.get_or_create(ctx.author.id)
        await ctx.send(f'{ctx.author.mention} has a boost of '
                       f'{format_currency(user.boost)}')

    @commands.command(aliases=['buy'])
    async def purchase(self, ctx, *parameters: str) -> None:
        if len(parameters) < 1:
            await ctx.send("Idk what you want to purchase. :shrug:")
            return

        try:
            qty = int(parameters[-1])
            item_string = ' '.join(parameters[:-1])
        except ValueError:
            qty = 1
            item_string = ' '.join(parameters)

        try:
            total_cost = self.pc.buy(ctx.author.id, item_string, qty)
        except Error as e:
            await ctx.send(str(e))
            return

        await ctx.send(f'{ctx.author.mention} bought {qty}'\
                       f' {self.pc.items.lookup(item_string)}{_plural(qty)}'
                       f' for {format_currency(total_cost)}.')

    @commands.command()
    async def store(self, ctx) -> None:
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
        # Save the user database (in another thread)
        self.pc.save_user_file()

        # Regenerate the store
        self.pc.store._generate_store()

    # Call User.add_boost() if required.
    @Cog.listener()
    async def on_message(self, message):
        user = self.pc.users.find_by_id(message.author.id)
        if user:
            user.add_boost()

    # Save the user file (and block) when the cog is unloaded. This has to
    # block as otherwise reloads might lose data.
    def cog_unload(self) -> None:
        print('[DEBUG] Saving user file in main thread...')
        self.pc.save_user_file_blocking()
        print('[DEBUG] Done.')

def setup(bot):
    bot.add_cog(BotInterface(bot, os.getcwd()))
