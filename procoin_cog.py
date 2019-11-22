import discord # type: ignore
from discord.ext import commands, tasks # type: ignore
from typing import Any, List, Optional, Tuple, Union, TYPE_CHECKING
import os, time, traceback

# TODO: Something better
if TYPE_CHECKING:
    class Cog:
        __slots__ = ()
        @classmethod
        def __init_subclass__(cls, **kwargs):
            return super().__init_subclass__()

        @classmethod
        def listener(self, name: Optional[str] = None):
            return lambda func : func
else:
    from discord.ext.commands import Cog

# Local imports
from procoin.core import ProCoin
from procoin.items import Item, format_currency
from procoin.store import Error
from procoin.users import User

def _plural(n: Union[int, float]) -> str:
    return '' if n == 1 else 's'

# This can't inherit from both commands.Cog and ProCoin, as attributes such as
# "store" conflict.
class BotInterface(Cog, name='General commands'):
    def __init__(self, bot: commands.Bot, directory: str) -> None:
        self.bot = bot
        self.pc = ProCoin(os.path.join(directory, 'items.json'),
                          os.path.join(directory, 'users.json'))
        self.__update_store.start()

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
    @commands.is_owner()
    @commands.command(help='Reloads the bot.', hidden=True)
    async def reload(self, ctx) -> None:
        try:
            self.bot.reload_extension(__name__)
            self.bot.reload_extension('sweepstakes_cog')
        except:
            await ctx.message.add_reaction('❌')
            raise
        else:
            await ctx.message.add_reaction('✅')
        finally:
            if self.bot.user:
                await ctx.message.remove_reaction('⌛', self.bot.user)

    @commands.is_owner()
    @commands.command(help='Starts a debugging shell.', hidden=True)
    async def drop_to_shell(self, ctx):
        await ctx.message.add_reaction('⌛')
        try:
            import code
            code.interact(local={'self': self, 'bot': self.bot})
        finally:
            if self.bot.user:
                await ctx.message.add_reaction('✅')
                await ctx.message.remove_reaction('⌛', self.bot.user)

    @commands.command(aliases=['money'], help="Gets a user's balance.",
                      usage='[@mention]')
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

    @commands.command(help="Gets a user's boost.", usage='[@mention]')
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

    @commands.command(aliases=['inventory'], help="Gets a user's inventory.",
                      usage='[@mention]')
    async def inv(self, ctx, target_uid: str = '') -> None:
        target_uid = target_uid.strip(' <@!>')

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

    @commands.command(help='Gives information on an item.',
                      usage='<item name>')
    async def info(self, ctx, *parameters: str) -> None:
        item_string = ' '.join(parameters)
        item = self.pc.items.lookup(item_string)
        if not item:
            await ctx.send("Couldn't find that item!")
            return
        msg: str = f'Cost: {format_currency(item.cost)}\n' \
                   f'Boost: {format_currency(item.boost)}'
        if item.cursed:
            msg += '\n\n*Cursed items painfully bind themselves to their ' \
                'victim/owner and cannot be removed without a scroll of ' \
                f'remove curse (see {self.bot.command_prefix}help ' \
                f'remove_curse).*'
        embed = discord.Embed(title=item.prefixed_name, description=msg,
                              colour=0xfdd835)
        await ctx.send(embed=embed)

    def __parse_item_and_quantity(self, parameters: Tuple[str, ...]) \
            -> Tuple[str, int]:
        if len(parameters) < 1:
            raise commands.UserInputError
        item_string = ' '.join(parameters)
        try:
            qty = int(parameters[-1])
            # Try finding the item string as-is for items ending in numbers
            # such as "Area 51".
            if self.pc.items.lookup(item_string):
                raise ValueError
            item_string = ' '.join(parameters[:-1])
        except ValueError:
            qty = 1

        return item_string, qty

    @commands.command(aliases=['purchase'], usage='<item name> [quantity]',
                      help='Purchases item(s) from the store.')
    async def buy(self, ctx, *parameters: str) -> None:
        if len(parameters) < 1:
            await ctx.send("Idk what you want to purchase. :shrug:")
            return
        item_string, qty = self.__parse_item_and_quantity(parameters)

        total_cost = self.pc.buy(ctx.author.id, item_string, qty)
        await ctx.send(f'{ctx.author.mention} bought {qty}'\
                       f' {self.pc.items.lookup(item_string)}{_plural(qty)}'
                       f' for {format_currency(total_cost)}.')

    @commands.command(brief='Sells item(s) to the store.',
                      help='Sells item(s) to the store.\nYou will get between '
                        '85% and 105% of the current sale price.',
                      usage='<item name> [quantity]')
    async def sell(self, ctx, *parameters: str) -> None:
        if len(parameters) < 1:
            await ctx.send("Idk what you want to sell. :shrug:")
            return
        item_string, qty = self.__parse_item_and_quantity(parameters)

        # Error objects are now caught in a global handler.
        sale_price = self.pc.sell(ctx.author.id, item_string, qty)

        await ctx.send(f'{ctx.author.mention} sold {qty}'\
                       f' {self.pc.items.lookup(item_string)}{_plural(qty)}'
                       f' for {format_currency(sale_price)}.')

    @commands.command(help='Displays the store.')
    async def store(self, ctx) -> None:
        next_update = self.pc.store.last_update + 3600
        delay = round(max(next_update - time.time(), 0) / 60)
        msg: str = self.pc.store.store_string
        msg += f'\r\n*The store resets in {delay} minute{_plural(delay)}.*'
        embed = discord.Embed(title='The Store', description=msg,
                              colour=0xfdd835)
        await ctx.send(embed=embed)

    @commands.command(help='Pays another user (in 💰).',
                      usage='<@mention> <amount>')
    async def pay(self, ctx, target_uid: str, amount: int) -> None:
        # Remove the @mention wrapper from the UID
        target_uid = target_uid.strip(' <@!>')
        self.pc.pay(ctx.author.id, target_uid, amount)
        await ctx.send(f'{ctx.author.mention} paid <@{target_uid}> '
                       f'{format_currency(amount)}.')

    @commands.command(help='Gives another person item(s).',
                      usage='<@mention> <item name> [quantity]')
    async def give(self, ctx, target_uid: str, *parameters: str) -> None:
        if len(parameters) < 1:
            await ctx.send("Idk what you want to give. :shrug:")
            return
        item_string, qty = self.__parse_item_and_quantity(parameters)

        # Remove the @mention wrapper from the UID
        target_uid = target_uid.strip(' <@!>')

        self.pc.give_item(ctx.author.id, target_uid, item_string, qty)
        await ctx.send(f'{ctx.author.mention} gave <@{target_uid}> {qty} '
                       f'{self.pc.items.lookup(item_string)}'
                       f'{_plural(qty)}!')

    @commands.command(help='Displays a list of possible merges.')
    async def merges(self, ctx) -> None:
        msg: str = self.pc.merges.get_merges()
        embed = discord.Embed(title='Possible Merges:', description=msg,
                      colour=0xfdd835)
        await ctx.send(embed=embed)

    @commands.command(help='Displays a list of possible merges.',
                      usage='<upgrade 1>, <upgrade 2>, ... [amount]')
    async def merge(self, ctx, *parameters: str) -> None:
        items: List[str] = ' '.join(parameters).split(',')
        if items:
            p = tuple(items[-1].split(' '))
            last_item, qty = self.__parse_item_and_quantity(p)
            items[-1] = last_item
        else:
            qty = 1

        names: str
        result: Item
        names, result = self.pc.merge(ctx.author.id, items, qty)

        if qty > 1:
            times = f' {qty} times'
        else:
            times = ''
        await ctx.send(f'{ctx.author.mention} merged {names}{times} to make '
                       f'{qty} {result.prefixed_name}{_plural(qty)}!')

    @commands.command(brief='Uses a scroll of remove curse.',
                      help='Uses a scroll of remove curse. You cannot control '
                           'which item the scroll will cleanse, and there is '
                           'a chance it will take a random item with it.',
                      usage='')
    async def remove_curse(self, ctx, *parameters: str) -> None:
        if any(parameters):
            raise Error('This command takes no parameters!')
        item, removed_item = self.pc.remove_curse(ctx.author.id)
        if removed_item:
            await ctx.send(f'The cursed item resists your scroll, and is '
                           f'eventually removed, but not before it can '
                           f'destroy your {removed_item.prefixed_name}!')
        await ctx.send(f'{ctx.author.mention} used a scroll of remove curse '
                       f'to remove 1 {item.prefixed_name}!')

    # This starts with two underscores to try and avoid conflicts with any
    # future commands.Cog internal function, the name will be mangled by
    # Python transparently.
    @tasks.loop(minutes=60.0)
    async def __update_store(self) -> None:
        # Save the user database (in another thread)
        self.pc.save_user_file()

        # Regenerate the store
        self.pc.store.regenerate_store()

    # Call User.add_boost() if required.
    @Cog.listener()
    async def on_message(self, message) -> None:
        user = self.pc.users.find_by_id(message.author.id)
        if user:
            user.add_boost()

    @Cog.listener()
    async def on_command_error(self, ctx, error: BaseException) -> None:
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f'Invalid command! Use {self.bot.command_prefix}'
                           f'help for a list of commands.')
        elif isinstance(error, commands.UserInputError):
            if isinstance(error, commands.MissingRequiredArgument):
                msg = 'Not enough arguments passed!'
            else:
                msg = 'Invalid command invocation!'
            await ctx.send(f'{msg} Try `'
                           f'{self.bot.command_prefix}help {ctx.command.name}'
                           f'` for more information.')
        elif isinstance(error, commands.CheckFailure):
            await ctx.send('Permission denied!')
        elif isinstance(error, commands.CommandInvokeError) and \
                isinstance(error.__cause__, Error):
            # Handle Error objects.
            await ctx.send(str(error.__cause__))
        else:
            if isinstance(error, commands.CommandInvokeError):
                error = error.__cause__
            traceback.print_exception(type(error), error, error.__traceback__)
            msg = f'{type(error).__name__}: {error or "*(no message)*"}'
            embed = discord.Embed(title='🐛 Error running command!',
                description=msg, colour=0xc62828)
            embed.set_footer(text='A full traceback has been written to '
                'stderr.')
            await ctx.send(embed=embed)

    # Save the user file (and block) when the cog is unloaded. This has to
    # block as otherwise reloads might lose data.
    def cog_unload(self) -> None:
        print('[DEBUG] Saving user file in main thread...')
        self.pc.save_user_file_blocking()
        print('[DEBUG] Done.')

def setup(bot):
    bot.add_cog(BotInterface(bot, os.getcwd()))
