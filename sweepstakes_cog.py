import discord # type: ignore
from discord.ext import commands # type: ignore
from random import choice, randint
from typing import Dict, List, Optional

# When type checking, procoin_cog.Cog is a dummy object so annotations work.
from procoin_cog import Cog
from procoin.core import ProCoin
from procoin.items import Item


class Sweepstakes(Cog):
    __slots__ = ('bot', 'next_event', 'next_item', 'in_race')
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.next_event = 0
        self.__set_timer()
        self.next_item: Optional[Item] = None
        self.in_race = False

    @property
    def pc(self) -> ProCoin:
        cog = self.bot.get_cog('General commands')
        assert cog
        return cog.pc

    @commands.Cog.listener()
    async def on_message(self, message) -> None:
        if message.author.bot or message.guild is None:
            return

        if self.in_race:
            if self.bot.user.mentioned_in(message):
                self.in_race = False
                await self.give_prize(message)
            return
        else:
            self.next_event -= 1

        if self.next_event <= 0:
            self.__set_timer()
            self.__set_new_item()
            if randint(0, 1) == 1:
                # Do sweepstakes
                await self.do_sweepstake(message)
            else:
                # Start a race
                assert self.next_item
                await message.channel.send(f'The next person to @mention me ' \
                    f'will receive 1 {self.next_item.prefixed_name}!')
                self.in_race = True

    async def do_sweepstake(self, message) -> None:
        # Keep mypy happy
        assert self.next_item

        user = self.pc.users.get_or_create(message.author.id)
        user.add_item(self.next_item, 1)
        await message.channel.send(f'Sweepstakes! ' \
            f'{message.author.mention} won a {self.next_item.prefixed_name}!')
        self.next_item = None

    async def give_prize(self, message) -> None:
        assert self.next_item

        user = self.pc.users.get_or_create(message.author.id)
        user.add_item(self.next_item, 1)
        await message.channel.send(f'Congratulations! ' \
            f'{message.author.mention} won a {self.next_item.prefixed_name}!')

    # These functions start with two underscores so Python can mangle names,
    # I'm scared discord.py is going to add functions starting with a single
    # underscore.
    def __set_new_item(self) -> None:
        self.next_item = choice(tuple(self.pc.items.items.values()))

    def __set_timer(self) -> None:
        self.next_event = randint(173, 427)

def setup(bot):
    bot.add_cog(Sweepstakes(bot))
