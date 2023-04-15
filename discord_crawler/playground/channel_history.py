"""Worker to get entire channel message history"""

import logging.config
from typing import Optional, List

from libs.api import DiscordAPI
import settings
from libs.db_operations import (
    get_db_conn,
    get_selfbots,
    upsert_message,
    mark_channel_history_complete,
)


logging.config.dictConfig(settings.DEFAULT_LOGGING)
logger = logging.getLogger(__name__)


def get_snowflake(message_list: List) -> Optional[int]:
    """
    Get the snowflake with the lowest ID in a message list.

    :param message_list:
    :return: Integer - the lowest snowflake message id or None
    """
    message_ids = [message['id'] for message in message_list if 'id' in message]

    if message_ids:
        return max(message_ids)

    return None


if __name__ == '__main__':

    logger.info('Starting up...')
    db_conn = get_db_conn()
    selfbots = get_selfbots(db_conn)

    if not selfbots:
        logger.critical('No selfbot tokens. Add them to the database.')
        exit(1)

    discord_apis = {}
    for sb in selfbots:
        discord_apis[sb['username']] = DiscordAPI(sb['token'])

    with db_conn.cursor() as cur:
        channels = cur.execute("""
        SELECT
            coalesce(max(m.id), 0)  AS message_id,
            c.id AS channel_id,
            c.name AS channel_name,
            g.name AS guild_name,
            s.username AS selfbot_name
            FROM channel c
            LEFT JOIN message m ON m.channel_id=c.id
            LEFT JOIN guild g ON c.guild_id = g.id
            LEFT JOIN selfbot s ON g.selfbot_id = s.id
            WHERE c.crawl_enabled = true
            GROUP BY c.id, c.name, s.username, g.name
            LIMIT 1
            FOR UPDATE OF channel;
        """).fetchall()

    for channel in channels:
        channel_id = channel['channel_id']
        logger.debug(
            'Getting channel history for | {0} | {1} | {2}'.format(
                channel['guild_name'],
                channel['channel_name'],
                channel_id,
            )
        )
        more_messages = True
        snowflake = channel['message_id']

        while more_messages:
            messages = discord_apis[channel['selfbot_name']].get_messages(
                channel_id,
                after=snowflake,
            )
            snowflake = get_snowflake(messages)

            if snowflake:
                logger.debug('Got {0} messages. Upserting'.format(len(messages)))
                [upsert_message(db_conn, message, channel_id) for message in messages]
            else:
                mark_channel_history_complete(db_conn, channel_id)
                more_messages = False

    db_conn.close()
    print('DONE')
