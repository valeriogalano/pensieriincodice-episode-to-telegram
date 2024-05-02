# pensieriincodice-episode-to-telegram

## Description
This GitHub Action sends a message to a Telegram Group or Channel with the latest episode of your podcast.

## Setup
1. Clone the repository
2. Set the following GitHub Actions secret PODCAST_RSS_URL with your podcast RSS feed URL
3. Set the following GitHub Actions secret TELEGRAM_BOT_API_KEY with your Telegram Bot API key
4. Set the following GitHub Actions variable TELEGRAM_CHAT_ID with your Telegram Group or Channel ID
5. Set the following GitHub Actions variable TELEGRAM_MESSAGE with the message you want to send to the Telegram Group or Channel:
   - Valid placeholders: {title}, {link}.   