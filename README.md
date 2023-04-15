# Purpose

The discord crawler is a self-bot that will crawl all messages in all channels
available to the user.

# Requirements
  - Minimum one discord account in good standing. We suggest you create a new one.
  - Docker
  - Postgresql Database

# Environment variables
You can configure of the logging and other setting with environment vars. You
can set these values in the `.env` file:
  - `DATABASE_URL`: string: postgres formatted URI string.
  - `VERBOSE`: boolean: True or False - set logging verbosity.  Optional. Default False
  - `LOG_LEVEL`: enum: (DEBUG, WARNING, ERROR, INFO) - required
  - `USER_AGENT`: string: Reported user agent when requesting to API. Optional

# Developer Requirements
  - python 3.8 or greater
  - dbmate for database migrations
  - Postgresql Server

# Services to run
  - `always_online`: Keep self-bots online and your session tokens fresh.
  - `refresh_guilds`: Refresh all guilds/servers the self-bots have access to.
  - `refresh_channels`: Refresh all channels in all guilds.
  - `crawl_messages`: Download all messages in all channels in all guilds. 
    Optionally you can as this service to fetch all messages back in time.
  - `refresh_users`: Refresh all users in the guild if self-bots have access.

# Limitations

  - Self-bots are a violation of the terms of service fo Discord. So this is in 
    a gray area. Use at your own rist to your accounts. I suggest you create a
    new account and run it this way.
  - Self-bots are limited to 200 guilds (servers) per user. Crawling more than
    that will require multiple accounts.
  - You will need to export a token from your logged in user session. This is
    easily done.
  - You will probably want to run a 24/7 service that will keep your self-bot
    online and active. Otherwise you will go idle and eventually the token
    will expire. Re-authenticating can become a pain.