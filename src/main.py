from math import ceil
from typing import Final

from dotenv import load_dotenv
from os import getenv

from discord import option
from discord import Intents
from discord import Message
from discord import Bot
from discord import ApplicationContext


def load_archive(path: str) -> tuple[list[str], int]:
    try:
        with open(path, 'r') as file:
            lines: Final[list[str]] = file.readlines()

            return lines, len(lines)
    except IOError:
        return [], 0


def write_archive(path: str, lines: list[str], start_index: int) -> None:
    with open(path, 'a+') as file:
        file.writelines('\n'.join(lines[start_index:]))


ARCHIVE_PATH: Final[str] = 'archive.txt'

PAGE_SIZE: Final[int] = 10

INTENTS: Final[Intents] = Intents(message_content=True)

load_dotenv()

bot: Final[Bot] = Bot(intents=INTENTS)

archive_lines: list[str]
archive_start_index: int
archive_current_index: int

archive_lines, archive_start_index = load_archive(ARCHIVE_PATH)
archive_current_index = archive_start_index


@bot.slash_command(name='archive',
                   description='Archives the nth last message.')
@option('n',
        description='Enter the nth last message to archive or none for the previous message.',
        required=False,
        default=1)
async def archive(ctx: ApplicationContext, n: int) -> None:
    try:
        n = int(n)

        if n <= 0:
            raise ValueError(f'An invalid message index of {n} was provided.')
        else:
            global archive_current_index

            message: Final[Message] = (await ctx.channel.history(limit=n).flatten())[0]
            archive_line: Final[str] = f'\"{message.content}\" - {message.author}'

            archive_lines.append(archive_line)

            archive_current_index += 1

            await ctx.respond(f'{archive_line} archived as message {archive_current_index}')

    except ValueError:
        await ctx.respond(f'An invalid message index of {n} was provided.')


@bot.slash_command(name='delete',
                   description='Deletes the nth archived message.')
@option('n', description='Enter the nth message to delete.', required=True)
async def delete(ctx: ApplicationContext, n: int) -> None:
    try:
        global archive_current_index

        n = int(n)

        if n < 1 or n > archive_current_index:
            raise ValueError(f'An invalid message index of {n} was provided.')
        else:
            archive_current_index -= 1

            await ctx.respond(f'{archive_lines.pop(n - 1)} at index {n} was deleted.')

    except ValueError:
        await ctx.respond(f'An invalid message index of {n} was provided.')


@bot.slash_command(name='get', description='Gets the nth archived message.')
@option('n', description='Enter the nth message to get.', required=True)
async def get(ctx: ApplicationContext, n: int) -> None:
    try:
        n = int(n)

        if n < 1 or n > archive_current_index:
            raise ValueError(f'An invalid message index of {n} was provided.')
        else:
            await ctx.respond(archive_lines[n - 1])
    except ValueError:
        await ctx.respond(f'An invalid message index of {n} was provided.')


@bot.slash_command(name='page',
                   description='Gets the nth page of archived messages.')
@option('n',
        description='Enter the nth page of messages to get.',
        required=False,
        default=1)
async def page(ctx: ApplicationContext, n: int) -> None:
    try:
        n = int(n)

        if archive_current_index == 0:
            await ctx.respond('No messages have been archived.')
        elif n < 1 or n > ceil(archive_current_index / PAGE_SIZE):
            raise ValueError(f'An invalid page index of {n} was provided.')
        else:
            offset: Final[int] = (n - 1) * PAGE_SIZE

            page: str = f'Page {n}:\n'

            for i, archive_line in \
                    enumerate(archive_lines[max(0, offset - PAGE_SIZE):max(archive_current_index, offset)]):
                page += f'{offset + i + 1}. {archive_line}\n'

            await ctx.respond(page)
    except ValueError:
        await ctx.respond(f'An invalid page index of {n} was provided.')


bot.run(getenv('TOKEN'))

write_archive(ARCHIVE_PATH, archive_lines, archive_start_index)
