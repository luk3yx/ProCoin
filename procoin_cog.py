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
from procoin.users import User

def _plural(n: Union[int, float]) -> str:
    return '' if n == 1 else 's'

# This can't inherit from both commands.Cog and ProCoin, as attributes such as
# "store" conflict.
class BotInterface(Cog):
    def __init__(self, bot: commands.Bot, directory: str) -> None:
        self.bot = bot
        self.pc = ProCoin(os.path.join(directory, 'items.json'),
                          os.path.join(directory, 'users.json'))

    # Get a username from a User object.
    def get_username(self, user: User) -> str:
        try:
            id = int(user.id)
        except ValueError:
            pass
        else:
            discord_user = self.bot.get_user(id)
            if discord_user:
                return discord_user.name

        # Default username
        return '#' + user.id

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
    async def bal(self, ctx, target_uid: str = '') -> None:
        target_uid = target_uid.strip(' <@!>')

        user: Optional[User]
        if target_uid:
            user = self.pc.users.find_by_id(target_uid)
        else:
            user = self.pc.users.get_or_create(ctx.author.id)

        if not user:
            await ctx.send("That user doesn't have a balance!")
            return
        await ctx.send(f'<@{user.id}> has {format_currency(user.balance)}')

    @commands.command()
    async def boost(self, ctx, target_uid: str = '') -> None:
        target_uid = target_uid.strip(' <@!>')

        user: Optional[User]
        if target_uid:
            user = self.pc.users.find_by_id(target_uid)
        else:
            user = self.pc.users.get_or_create(ctx.author.id)

        if not user:
            await ctx.send("That user doesn't have a boost!")
            return
        await ctx.send(f'<@{user.id}> has a boost of '
                       f'{format_currency(user.boost)}')

    @commands.command(aliases=['inventory'])
    async def inv(self, ctx, target_uid: str = '') -> None:
        target_uid = target_uid.strip(' <@!>1')

        user: Optional[User]
        if target_uid:
            user = self.pc.users.find_by_id(target_uid)
        else:
            user = self.pc.users.get_or_create(ctx.author.id)

        if not user:
            await ctx.send("That user doesn't have an inventory!")
            return

        username: str = self.get_username(user)
        embed = discord.Embed(title=f"{username}'s inventory.",
            description=user.inv, colour=0xfdd835)
        await ctx.send(embed=embed)

    @commands.command()
    async def info(self, ctx, *parameters: str) -> None:
        item_string = ' '.join(parameters)
        item = self.pc.items.lookup(item_string)
        if not item:
            await ctx.send("Couldn't find that item!")
            return
        msg: str = f'Cost: {format_currency(item.cost)}\n' \
                   f'Boost: {format_currency(item.boost)}'
        embed = discord.Embed(title=item.prefixed_name, description=msg,
                              colour=0xfdd835)
        await ctx.send(embed=embed)

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
    async def sell(self, ctx, *parameters: str) -> None:
        if len(parameters) < 1:
            await ctx.send("Idk what you want to sell. :shrug:")
            return

        try:
            qty = int(parameters[-1])
            item_string = ' '.join(parameters[:-1])
        except ValueError:
            qty = 1
            item_string = ' '.join(parameters)

        try:
            sale_price = self.pc.sell(ctx.author.id, item_string, qty)
        except Error as e:
            await ctx.send(str(e))
            return

        await ctx.send(f'{ctx.author.mention} sold {qty}'\
                       f' {self.pc.items.lookup(item_string)}{_plural(qty)}'
                       f' for {format_currency(sale_price)}.')

    @commands.command()
    async def store(self, ctx) -> None:
        next_update = self.pc.store.last_update + 3600
        delay = round(max(next_update - time.time(), 0) / 60)
        msg: str = self.pc.store.store_string
        msg += f'\r\n*The store resets in {delay} minute{_plural(delay)}.*'
        embed = discord.Embed(title='The Store', description=msg,
                              colour=0xfdd835)
        await ctx.send(embed=embed)

    @commands.command()
    async def pay(self, ctx, target_uid: str, raw_amount: str) -> None:
        # Remove the @mention wrapper from the UID
        target_uid = target_uid.strip(' <@!>')

        try:
            amount = int(raw_amount)
        except ValueError:
            await ctx.send(f'`{raw_amount}` is not a number!')
            return

        try:
            self.pc.pay(ctx.author.id, target_uid, amount)
        except Error as e:
            await ctx.send(str(e))
        else:
            await ctx.send(f'{ctx.author.mention} paid <@{target_uid}> '
                           f'{format_currency(amount)}.')

    @commands.command()
    async def give(self, ctx, target_uid: str, *parameters: str) -> None:
        if len(parameters) < 1:
            await ctx.send("Idk what you want to give. :shrug:")
            return

        try:
            qty = int(parameters[-1])
            item_string = ' '.join(parameters[:-1])
        except ValueError:
            qty = 1
            item_string = ' '.join(parameters)

        # Remove the @mention wrapper from the UID
        target_uid = target_uid.strip(' <@!>')

        try:
            self.pc.give_item(ctx.author.id, target_uid, item_string, qty)
        except Error as e:
            await ctx.send(str(e))
        else:
            await ctx.send(f'{ctx.author.mention} gave <@{target_uid}> {qty} '
                           f'{self.pc.items.lookup(item_string)}'
                           f'{_plural(qty)}!')

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
