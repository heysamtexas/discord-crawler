import logging.config
from libs.api import DiscordAPI
import settings
from libs.db_operations import (
    get_db_conn,
    get_selfbots,
    channel_crawl_enabled,
)


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
        channels = cur.execute("""
            SELECT c.id, c.name, s.username as selfbot_name, g.name as guild_name
            FROM channel c
            LEFT JOIN guild g on c.guild_id=g.id
            LEFT JOIN selfbot s ON g.selfbot_id = s.id 
            WHERE c.crawl_enabled = true
            ORDER BY c.created_at DESC;
        """).fetchall()

    for channel in channels:
        channel_id = channel['id']
        logger.debug(
            'Getting messages for channel {0}-{1}-{2}'.format(
                channel['guild_name'],
                channel['name'],
                channel_id,
            )
        )
        messages = discord_apis[channel['selfbot_name']].get_messages(channel_id)

        if isinstance(messages, dict):
            channel_crawl_enabled(db_conn, channel_id, False)

    db_conn.close()
    print('DONE')