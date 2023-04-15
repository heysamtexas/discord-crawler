"""Worker to get entire channel message history"""
import json
import logging.config
from typing import Optional, List, Dict, Tuple

import psycopg

from libs.api import DiscordAPI
import settings
from libs.db_operations import (
    get_db_conn,
    get_selfbots,
    get_channels_with_no_messages,
)
import concurrent.futures


logging.config.dictConfig(settings.DEFAULT_LOGGING)
logger = logging.getLogger(__name__)


MAX_WORKERS = 15


def get_snowflake(message_list: List) -> Optional[int]:
    """
    
    :param message_list: 
    :return: 
    """
    message_ids = [message['id'] for message in message_list if 'id' in message]

    if message_ids:
        return min(message_ids)

    return None


def async_message_fetch(channel_list: List[Dict], apis: Dict) -> Dict:
    """
    
    :param channel_list: 
    :param apis: 
    :return: 
    """
    messages = {
        'valid': {},
        'invalid': []
    }
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for channel in channel_list:
            selfbot_name = channel['selfbot_name']

            future = executor.submit(
                apis[selfbot_name].get_messages,
                channel['channel_id'],
                after=channel['message_id'],
                json_response=False,
            )
            future.channel_id = channel['channel_id']
            futures.append(future)

        for future in concurrent.futures.as_completed(futures):
            result = future.result().json()

            if isinstance(result, dict):
                messages['invalid'].append(future.channel_id)

            messages['valid'][future.channel_id] = result

    return messages


def flatten_batch(all_messages: Dict) -> List[Tuple[int, str, int]]:
    flattened = []

    for channel_id in all_messages.keys():
        for m in all_messages[channel_id]:
            flattened.append((m['id'], json.dumps(m), channel_id))

    return flattened


def disable_channel_crawls(conn: psycopg.Connection, channel_ids: List[int]) -> None:
    sql = 'UPDATE channel SET crawl_enabled = false WHERE id = %s'
    with conn.cursor() as cur:
        cur.executemany(sql, channel_ids)


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

    more_work = True

    while more_work:
        channels_no_history = get_channels_with_no_messages(db_conn)

        if channels_no_history:

            # This is the async fetch part
            batches = async_message_fetch(channels_no_history, discord_apis)
            disable_channel_crawls(db_conn, batches['invalid'])
            disable_channel_crawls(db_conn, batches['empty'])

        all_messages = flatten_batch(batches['valid'])






        # batches = async_message_fetch(channels, discord_apis)
        #
        # crawl_done = [channel_id for channel_id in batches.keys() if not batches[channel_id]]
        # all_messages = flatten_batch(batches)
        #
        # logger.debug('Upserting {0} messages '.format(len(all_messages)))
        # logger.debug('Marking channels history_crawled \'true\': {0}'.format(crawl_done))


        # with db_conn.cursor() as cur:
        #     logger.debug('Upserting {0} messages '.format(len(all_messages)))
        #     cur.executemany("INSERT INTO message (id, raw_data, channel_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING ", all_messages)

        # for channel_id in batches.keys():
        #     messages = batches[channel_id]
        #     snowflake = get_snowflake(messages)
        #
        #     if snowflake:
        #         logger.debug(f'Got {len(messages)} messages. Upserting')
        #         payload = [(message['id'], json.dumps(message), channel_id) for message in messages]
        #         with db_conn.cursor() as cur:
        #             cur.executemany(
        #                 "INSERT INTO message (id, raw_data, channel_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING ",
        #                 messages
        #             )
        #         # [upsert_message(db_conn, message, channel_id) for message in messages]
        #     else:
        #         logger.debug('Marking channel history_crawled \'true\': {0}'.format(channel_id))
        #         mark_channel_history_complete(db_conn, channel_id)

    db_conn.close()
    print('DONE')
