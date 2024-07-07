<?php

class TelegramPublisher
{
    private const ESCAPE_CHARACTERS = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!'];
    private const ESCAPED_CHARACTERS = ['\_', '\*', '\[', '\]', '\(', '\)', '\~', '\`', '\>', '\#', '\+', '\-', '\=', '\|', '\{', '\}', '\.', '\!'];
    private const TELEGRAM_API_URL = "https://api.telegram.org/bot";

    public function __construct(
        private readonly string $feed_url,
        private readonly string $telegram_chat_id,
        private readonly string $telegram_api_key,
        private readonly string $template,
        private readonly string $file_path
    )
    {
    }

    public function run(): void
    {
        try {
            $last_episode = $this->fetchLastEpisode();

            if (!$last_episode) {
                echo "No episodes found\n";
                return;
            }

            echo "Last episode fetched successfully: " . $last_episode->link . "\n";

            if ($this->isEpisodeAlreadyPublished($last_episode)) {
                echo "Episode already published\n";
                return;
            }

            $this->publishToTelegram($last_episode);

            echo "Episode published successfully\n";

            $this->markAsPublished($last_episode);

            echo "Episode mark as published successfully\n";

        } catch (Exception $e) {
            error_log("An error occurred: " . $e->getMessage() . "\n");
            exit(1);
        }
    }

    /**
     * Fetch last episode from podcast feed
     * @throws Exception
     */
    private function fetchLastEpisode(): ?SimpleXMLElement
    {
        $feed = simplexml_load_file($this->feed_url);
        if ($feed === false) {
            // Handle failed import here; perhaps throw an exception
            throw new Exception('Failed to import XML Podcast feed document.');
        }

        if (!property_exists($feed, 'channel')) {
            // Handle missing 'channel' here; perhaps throw an exception
            throw new Exception('The feed lacks the "channel" element.');
        }

        if (!property_exists($feed->channel, 'item')) {
            // Handle missing 'item' here; perhaps throw an exception
            throw new Exception('The "channel" element lacks the "item" element.');
        }

        // We can now safely access the elements
        return $feed->channel->item[0];
    }

    /**
     * Search episode link into file
     * @throws Exception
     */
    private function isEpisodeAlreadyPublished($last_episode): bool
    {
        if ($last_episode === null || !property_exists($last_episode, 'link')) {
            throw new Exception('Invalid podcast episode');
        }

        $link = $last_episode->link;
        $content = $this->getContentFromFile();

        return str_contains($content, $link);
    }

    /**
     * @throws Exception
     */
    private function getContentFromFile(): string
    {
        $content = @file_get_contents($this->file_path);

        if ($content === false) {
            throw new Exception("Failed to read from file: $this->file_path");
        }

        return $content;
    }

    /**
     * Publish last episode to Telegram channel
     * @throws Exception
     */
    private function publishToTelegram($last_episode): void
    {
        // Ensure that $last_episode has a 'link' property
        if (!property_exists($last_episode, 'link')) {
            throw new Exception('The provided object does not have a "link" property.');
        }

        // Ensure that $last_episode has a 'title' property
        if (!property_exists($last_episode, 'title')) {
            throw new Exception('The provided object does not have a "title" property.');
        }

        $file_get_contents = file_get_contents(
            self::TELEGRAM_API_URL . "$this->telegram_api_key/sendMessage",
            false,
            stream_context_create([
                'http' => [
                    'header' => "Content-type: application/x-www-form-urlencoded\r\n",
                    'method' => 'POST',
                    'content' => http_build_query([
                        'chat_id' => $this->telegram_chat_id,
                        'text' => str_replace(
                            ['{title}', '{link}'],
                            [$this->escape($last_episode->title), $this->escape($last_episode->link)],
                            $this->template
                        ),
                        'parse_mode' => 'MarkdownV2',
                        'disable_notification' => true,
                    ]),
                ],
            ])
        );

        if ($file_get_contents === false) {
            throw new Exception("Error publishing episode");
        }
    }

    /**
     * Escape string for Telegram Markdown2 style
     */
    private function escape(array|string $string): string|array
    {
        return str_replace(
            self::ESCAPE_CHARACTERS,
            self::ESCAPED_CHARACTERS,
            $string
        );
    }

    /**
     * Add episode link into file
     * @throws Exception
     */
    private function markAsPublished($last_episode): void
    {
        // Ensure that $last_episode has a 'link' property
        if (!property_exists($last_episode, 'link')) {
            throw new Exception('The provided object does not have a "link" property.');
        }

        // Ensure that the file is writable
        if (!is_writable($this->file_path)) {
            throw new Exception('The specified file path is not writable.');
        }

        $file_put_contents = file_put_contents($this->file_path, "$last_episode->link\n", FILE_APPEND);

        if ($file_put_contents === false) {
            throw new Exception("Error saving episode");
        }
    }
}

$publisher = new TelegramPublisher(
    getenv('PODCAST_RSS_URL'),
    getenv('TELEGRAM_CHAT_ID'),
    getenv('TELEGRAM_BOT_API_KEY'),
    getenv('TELEGRAM_MESSAGE_TEMPLATE'),
    './published_episodes.txt'
);

$publisher->run();
