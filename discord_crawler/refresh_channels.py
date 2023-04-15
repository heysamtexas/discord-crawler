"""Periodically refresh all channels / all guilds"""

import logging.config
import time

from libs.api import DiscordAPI
import settings
from libs.db_operations import get_db_conn, get_selfbots, upsert_channels


logging.config.dictConfig(settings.DEFAULT_LOGGING)
logger = logging.getLogger(__name__)


if __name__ == '__main__':

    logger.info('Starting up...')
    db_conn = get_db_conn()
    selfbots = get_selfbots(db_conn)

    if not selfbots:
        logger.warning('No selfbot tokens. Add them to the database.')

    discord_apis = {}
    for sb in selfbots:
        discord_apis[sb['username']] = DiscordAPI(sb['token'])

    with db_conn.cursor() as cur:
        guilds = cur.execute("""
            SELECT g.id, g.name, s.username as selfbot_name
            FROM guild g
            LEFT JOIN selfbot s ON g.selfbot_id = s.id 
            WHERE g.crawl_enabled = true
            ORDER BY g.crawl_priority DESC 
        """).fetchall()

    for guild in guilds:
        guild_id = guild['id']
        logger.debug(
            'Getting channels for guild {0}-{1}'.format(
                guild['name'],
                guild_id,
            ),
        )
        channels = discord_apis[guild['selfbot_name']].get_channels(guild_id)

        if channels:
            upsert_channels(db_conn, channels, guild_id)
        else:
            logger.warning('No channels found for Guild {0} | {1}'.format(guild['name'], guild_id))

        time.sleep(3)

    db_conn.close()
    logger.info('DONE')
