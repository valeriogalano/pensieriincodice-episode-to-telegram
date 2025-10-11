# pensieriincodice-episode-to-telegram

## Description
This GitHub Action sends a message to a Telegram Group or Channel with the latest episode of your podcasts. It supports multiple podcasts with separate tracking and custom message templates for each.

## Setup

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/pensieriincodice-episode-to-telegram.git
cd pensieriincodice-episode-to-telegram
```

### 2. Configure GitHub Actions Secrets
Go to your repository **Settings > Secrets and variables > Actions** and add the following **Secret**:

- `TELEGRAM_BOT_API_KEY`: Your Telegram Bot API key (get it from [@BotFather](https://t.me/botfather))

### 3. Configure GitHub Actions Variables
In the same section, under the **Variables** tab, add:

- `TELEGRAM_CHAT_ID`: Your Telegram Group or Channel ID (use [@getidsbot](https://t.me/getidsbot) to get it)
- `PODCAST1_RSS_URL`: RSS feed URL for your first podcast
- `PODCAST1_TEMPLATE`: Message template for the first podcast
- `PODCAST2_RSS_URL`: RSS feed URL for your second podcast
- `PODCAST2_TEMPLATE`: Message template for the second podcast

### 4. Message Templates
Valid placeholders for templates: `{title}`, `{link}`

Example templates:
```
🎙️ Nuovo episodio di Pensieri in Codice!

*{title}*

Ascoltalo qui: {link}
```

**Note:** The bot uses Telegram MarkdownV2 format. Special characters are automatically escaped.

### 5. Adding More Podcasts
To add more podcasts, edit `.github/workflows/cron.yml` and add additional podcast configurations in the "Create podcasts config" step:

```php
[
  "id" => "mypodcast",
  "name" => "My Podcast",
  "feed_url" => getenv("PODCAST3_RSS_URL"),
  "template" => getenv("PODCAST3_TEMPLATE")
]
```

Then add the corresponding GitHub Actions variables (`PODCAST3_RSS_URL`, `PODCAST3_TEMPLATE`).

## How It Works
- The workflow runs automatically every hour between 7 AM and 6 PM
- Each podcast is tracked separately in `published_episodes_{podcast_id}.txt`
- Only new episodes are published
- The workflow can also be triggered manually from the Actions tab   