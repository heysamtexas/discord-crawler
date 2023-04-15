"""Periodically refresh guilds and add them to the database."""

import logging.config
from libs.api import DiscordAPI
import settings
from libs.db_operations import (
    get_db_conn,
    get_selfbots,
    upsert_guild,
)


logging.config.dictConfig(settings.DEFAULT_LOGGING)
logger = logging.getLogger(__name__)


if __name__ == '__main__':

    logger.info('Starting up...')
    db_conn = get_db_conn()
    selfbots = get_selfbots(db_conn)

    if not selfbots:
        logger.warning('No selfbot tokens. Add them to the database.')

    for sb in selfbots:
        discord = DiscordAPI(sb['token'])

        logger.debug('Getting Guilds...')
        guilds = discord.get_guilds()

        if guilds:
            logger.debug('Got {0} Guilds. Upserting'.format(len(guilds)))
            [upsert_guild(db_conn, guild, sb['id']) for guild in guilds]

    db_conn.close()
    logger.info('DONE')