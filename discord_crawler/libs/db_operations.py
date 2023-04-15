import datetime
import json
from typing import Optional, List, Dict

import psycopg
from psycopg.rows import dict_row, Row
import os
import logging.config
import settings


logging.config.dictConfig(settings.DEFAULT_LOGGING)
logger = logging.getLogger(__name__)


def get_db_conn(
    url: Optional[str] = None,
    autocommit: bool = True,
) -> psycopg.Connection:
    """
    Connect to a Postgres database.

    You can pass in a database url or pull it from a set environment
    variable (default is DATABASE_URL).

    NOTE: url overrides env_var_name if both are passed in.

    Args:
        url: A database URL
        autocommit: Bool - True or False if we should autocommit

    Returns:
        A psycopg3 database connection handle
    """
    db_url = url if url else settings.DATABASE_URI
    return psycopg.connect(db_url, row_factory=dict_row, autocommit=autocommit)


def get_selfbots(conn: psycopg.Connection) -> Optional[List[Row]]:
    """
    Fetch a list of selfbots and their tokens to access the Discord API.

    :param conn: database handle
    :return: A List of selfbot database objects or None
    """
    with conn.cursor() as cur:
        selfbots = cur.execute("""
            SELECT id, username, token 
                FROM selfbot
        """).fetchall()
        if selfbots:
            return selfbots

    return None


def upsert_guild(conn: psycopg.Connection, guild: Dict, selfbot_id: int) -> None:
    """
    Upsert a guild into the database.

    Conflicts / duplicates are ignored.

    :param conn: Database handle
    :param guild: Guild object
    :param selfbot_id: primary key on the selfbot database row
    :return: None
    """
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO guild (id, name, raw_data, selfbot_id) 
            VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING 
            """,
            [
                guild['id'],
                guild['name'],
                json.dumps(guild),
                selfbot_id,
            ]
        )


def upsert_channel(
    conn: psycopg.Connection,
    channel: Dict,
    guild_id: int,
) -> None:
    """
    Upsert a single channel into the database.

    Conflicts / duplicates are ignored.

    :param conn: database handle
    :param channel: Discord API channel object
    :param guild_id: primary key on the guild table
    :return: None
    """
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO channel (id, name, raw_data, guild_id) 
            VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING 
            """,
            [
                channel['id'],
                channel['name'],
                json.dumps(channel),
                guild_id,
            ]
        )

def upsert_channels(
    conn: psycopg.Connection,
    channels: List,
    guild_id: int,
) -> None:
    """
    Upsert a list of channel objects into the database.

    Conflicts / duplicates are ignored.

    :param conn: database handle
    :param channels: List of Discord API channel objects
    :param guild_id: Primary key on the Guild database table
    :return: None
    """
    if not channels:
        logger.warning('No channels to upsert! guild_id: {0}'.format(guild_id))
        return

    if not guild_id:
        raise Exception('guild_id is required.')

    logger.debug('Got {0} Channels. Upserting'.format(len(channels)))
    payload = [(c['id'], c['name'], json.dumps(c), guild_id) for c in channels]
    sql = 'INSERT INTO channel (id, name, raw_data, guild_id) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING'
    with conn.cursor() as cur:
        cur.executemany(sql, payload)


def upsert_message(
    conn: psycopg.Connection,
    message: Dict,
    channel_id: int,
) -> None:

    if not isinstance(message, Dict):
        return

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO message (id, raw_data, channel_id) 
            VALUES (%s, %s, %s) ON CONFLICT DO NOTHING 
            """,
            [
                message['id'],
                json.dumps(message),
                channel_id,
            ]
        )


def upsert_messages(
    conn: psycopg.Connection,
    messages: List,
    channel_id: int,
) -> None:

    if not messages:
        logger.warning('Message length was 0 for channel {0}'.format(channel_id))
        return None

    payload = [(m['id'], json.dumps(m), m['channel_id']) for m in messages]

    with conn.cursor() as cur:
        sql = "INSERT INTO message (id, raw_data, channel_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING"
        cur.executemany(sql, payload)
        logger.debug(
            'Upserted {0} to channel {1}'.format(
                len(messages),
                channel_id,
            )
        )

    return None


def channel_crawl_enabled(
    conn: psycopg.Connection,
    channel_id: int,
    value: bool,
) -> None:
    """
    Enable or disable channel message crawling

    :param conn: The database connection
    :param channel_id: Primary key on the channel id
    :param value: True or False
    :return: None
    """
    if value is None:
        raise Exception('You must set value [Ture or False]')

    if channel_id is None:
        raise Exception('channel_id is required.')

    action = 'Enabling' if value else 'Disabling'
    logger.debug('{0} crawl for channel: {1}'.format(action, channel_id))

    with conn.cursor() as cur:
        sql = 'UPDATE channel SET crawl_enabled = %s WHERE id = %s'
        cur.execute(sql, [value, channel_id])


def channel_mark_last_update(conn: psycopg.Connection, channel_id: int) -> None:
    """
    Update the channels last update to now()

    :param conn: Database handle
    :param channel_id: Primary key on the Channel table
    :return: None
    """
    if not channel_id:
        raise Exception('channel_id is required')

    with conn.cursor() as cur:
        sql = 'UPDATE channel SET last_update = now() WHERE id = %s'
        cur.execute(sql, [channel_id])


# def get_channels_missing_history(conn: psycopg.Connection) -> List[Dict]:
#     """
#
#     :param conn:
#     :return:
#     """
#     with conn.cursor() as cur:
#         return cur.execute("""
#             SELECT
#                 min(m.id) as message_id,
#                 c.id as channel_id,
#                 c.name as channel_name,
#                 g.name as guild_name,
#                 s.username as selfbot_name
#                 from message m
#                 left join channel c on c.id = m.channel_id
#                 left join guild g on c.guild_id = g.id
#                 left join selfbot s on g.selfbot_id = s.id
#                 WHERE c.history_crawled = false
#                 group by c.id, c.name, s.username, g.name;
#         """).fetchall()


def get_channels_with_no_messages(conn: psycopg.Connection) -> List[Dict]:
    """

    :param conn:
    :return:
    """
    with conn.cursor() as cur:
        return cur.execute("""
            SELECT
                0 as message_id,
                c.id as channel_id,
                c.name as channel_name,
                g.name as guild_name,                
                s.username as selfbot_name
                from channel c 
                left join guild g on c.guild_id = g.id
                left join selfbot s on g.selfbot_id = s.id
                WHERE c.crawl_enabled = true
                group by c.id, c.name, s.username, g.name
                LIMIT 10;
        """).fetchall()


def create_channel_crawl_log(
    conn: psycopg.Connection,
    channel_id: int,
    low_id: int,
    high_id: int,
    start_time: datetime,
    end_time: datetime,
) -> None:

    sql = """
    INSERT INTO channel_crawl_log (
        started_at,
        ended_at,
        low_message_id,
        high_message_id,
        channel_id
    ) VALUES (%s, %s, %s, %s, %s)"""
    with conn.cursor() as cur:
        cur.execute(sql, [start_time, end_time, low_id, high_id, channel_id])
        logger.debug('Created crawl_entry for {0}'.format(channel_id))
