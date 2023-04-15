from typing import Union, List, Dict, Optional
import settings
import requests
import logging.config

logging.config.dictConfig(settings.DEFAULT_LOGGING)
logger = logging.getLogger(__name__)


MESSAGE_LIMIT = 100


class DiscordAPIException(Exception):
    pass


class DiscordAPI429(Exception):
    pass


class DiscordAPI(object):

    def __init__(self, token: str = None):
        if not token:
            raise DiscordAPIException('Token required')
        self.TOKEN = token
        self.BASE_URL = settings.BASE_URL
        self.HEADERS = {
            'User-Agent': settings.USER_AGENT,
            'authorization': '{0}'.format(self.TOKEN),
        }
        self.VERBOSE = settings.VERBOSE

    def _get(
        self, url: str = None,
        params: Dict = None,
    ) -> Optional[requests.models.Response]:

        if params is None:
            params = {}
        if not url:
            raise DiscordAPIException('"url" is a required parameter ')

        resp = requests.get(url, headers=self.HEADERS, params=params)

        if self.VERBOSE:
            logger.debug("""Response headers: {0}""".format(resp.headers))

        if resp.status_code == 429:
            raise DiscordAPI429(resp.json())

        return resp

    def get_guilds(self) -> Union[List[Dict], Dict, None]:
        url = self.BASE_URL.format('users/@me/guilds')
        return self._get(url).json()

    def get_channels(self, guild_id: int) -> Union[List[Dict], Dict, None]:
        channel_url = 'guilds/{0}/channels'.format(guild_id)
        url = self.BASE_URL.format(channel_url)
        return self._get(url).json()

    def get_members(self, guild_id: int) -> Union[List[Dict], Dict, None]:
        """
        Get the members from a guild given the URL

        :param guild_id:
        :return:
        :raises requests.exceptions.JSONDecodeError: If the response body does not
            contain valid json.
        """
        members_url = 'guilds/{0}/members'.format(guild_id)
        url = self.BASE_URL.format(members_url)
        return self._get(url).json()

    def get_messages(
        self,
        channel_id: int,
        after: int = None,
        json_response: bool = True,
    ) -> Union[List[Dict], Dict, None]:
        """

        :param channel_id:
        :param after:
        :param json_response:
        :return:
        """

        messages_url = 'channels/{0}/messages'.format(channel_id)
        url = self.BASE_URL.format(messages_url)

        params = {
            'limit': MESSAGE_LIMIT
        }

        if after is not None:
            params['after'] = after

        logger.debug(f'Fetching messages snowflake channel_id: {channel_id} | message_id: {after}')

        if self.VERBOSE == True:
            logger.debug(f"\nrequests.get(\n\t'{url}',\n\tparams={params},\n\theaders={self.HEADERS}\n)\n")

        ret = self._get(url, params=params)

        if json_response:
            return ret.json()

        return ret
