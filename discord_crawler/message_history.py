"""Worker to get entire channel message history"""

import logging.config
import time
from datetime import datetime
from typing import Optional, List

from libs.api import DiscordAPI
import settings
from libs.db_operations import (
    get_db_conn,
    get_selfbots,
    upsert_messages,
    channel_mark_last_update, channel_crawl_enabled, create_channel_crawl_log,
)


logging.config.dictConfig(settings.DEFAULT_LOGGING)
logger = logging.getLogger(__name__)


def get_snowflake(message_list: List) -> Optional[int]:
    """
    Get the snowflake with the highest ID in a message list.

    :param message_list:
    :return: Integer - the lowest snowflake message id or None
    """
    message_ids = [message['id'] for message in message_list if 'id' in message]

    if message_ids:
        return max(message_ids)

    return None


if __name__ == '__main__':

    logger.info('Starting up...')
    db_conn = get_db_conn(autocommit=False)
    selfbots = get_selfbots(db_conn)

    if not selfbots:
        logger.critical('No selfbot tokens. Add them to the database.')
        exit(1)

    discord_apis = {}
    for sb in selfbots:
        discord_apis[sb['username']] = DiscordAPI(sb['token'])

    while True:
        with db_conn.cursor() as cur:
            channel = cur.execute("""
            SELECT 
                c.id as channel_id, 
                c.name as channel_name,
                g.name as guild_name,
                s.username as selfbot_name
            FROM channel c 
            LEFT JOIN guild g on g.id = c.guild_id
            LEFT JOIN selfbot s on s.id = g.selfbot_id
            WHERE c.crawl_enabled = true and g.crawl_enabled = true
            ORDER BY c.last_update ASC
            LIMIT 1
            FOR UPDATE of c SKIP LOCKED;
            """).fetchone()

            snowflake = cur.execute("""
            SELECT
                coalesce(max(cl.high_message_id), 0) AS snowflake_id
                from channel_crawl_log cl
                LEFT JOIN channel c on c.id = cl.channel_id
                WHERE c.id = %s            
            """, [channel['channel_id']]).fetchone()

            # channel = cur.execute("""
            # SELECT
            #     coalesce(max(cl.high_message_id), 0)  AS snowflake,
            #     c.id AS channel_id,
            #     c.name AS channel_name,
            #     g.name AS guild_name,
            #     s.username AS selfbot_name
            #     FROM channel c
            #     LEFT JOIN channel_crawl_log cl ON cl.channel_id = c.id
            #     LEFT JOIN guild g ON c.guild_id = g.id
            #     LEFT JOIN selfbot s ON g.selfbot_id = s.id
            #     WHERE c.crawl_enabled = true
            #     GROUP BY c.id, c.name, s.username, g.name
            #     ORDER BY max(c.last_update) ASC
            #     LIMIT 1;
            # """).fetchone()

        channel_id: int = channel['channel_id']
        snowflake: int = snowflake['snowflake_id']

        logger.debug(
            'Getting channel history for | {0} | {1} | {2}'.format(
                channel['guild_name'],
                channel['channel_name'],
                channel_id
            )
        )

        more_messages = True
        start_time = datetime.now()
        low_id: int = snowflake
        high_id: int = low_id
        total_messages = 0

        while more_messages:
            messages = discord_apis[channel['selfbot_name']].get_messages(channel_id, after=snowflake)

            # Has messages. Save them and calculate the next snowflake
            # messages.ok
            if isinstance(messages, list) and len(messages) > 0:
                upsert_messages(db_conn, messages, channel_id)
                snowflake = get_snowflake(messages)

            # Some kind of error came back. (Usually access related) Exit the while
            # message.has_error
            elif isinstance(messages, dict):
                channel_crawl_enabled(db_conn, channel_id, False)
                more_messages = False
                logger.warning('Channel {0} got error: {1}'.format(channel_id, messages))

            # No messages returned. We reached the max. Log the crawl
            # messages.is_empty
            elif len(messages) == 0:
                more_messages = False
                high_id = snowflake
                create_channel_crawl_log(
                    conn=db_conn,
                    low_id=low_id,
                    high_id=high_id,
                    start_time=start_time,
                    end_time=datetime.utcnow(),
                    channel_id=channel_id,
                )

        channel_mark_last_update(db_conn, channel_id)
        db_conn.commit()

    db_conn.close()
    print('DONE')
