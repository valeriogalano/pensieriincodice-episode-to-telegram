<?php

/**
 * Load podcasts configuration
 */
function load_podcasts_config(string $config_file): array
{
	if (!file_exists($config_file)) {
		error_log("Configuration file not found: $config_file");
		exit(1);
	}

	$config = json_decode(file_get_contents($config_file), true);

	if ($config === null) {
		error_log('Error parsing configuration file: ' . json_last_error_msg());
		exit(1);
	}

	return $config;
}

/**
 * Get tracking file path for a specific podcast
 */
function get_tracking_file(string $podcast_id): string
{
	return "./published_episodes_{$podcast_id}.txt";
}

/**
 * Fetch last episode from podcast feed
 */
function fetch_last_episode(string $feed_url): SimpleXMLElement|false
{
    $feed = simplexml_load_file($feed_url);

    if ($feed === false) {
        error_log('Error fetching feed: ' . print_r(error_get_last(), true));
        exit(1);
    }

    $item = $feed->channel->item[0];

    if ($item === null) {
        error_log('Error fetching last episode: ' . print_r(error_get_last(), true));
        exit(1);
    }

    return $item;
}

/**
 * Escape string for Telegram Markdown2 style
 */
function escape_telegram(array|string $string): string|array
{
    $escape_characters = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!'];
    $escaped_characters = ['\_', '\*', '\[', '\]', '\(', '\)', '\~', '\`', '\>', '\#', '\+', '\-', '\=', '\|', '\{', '\}', '\.', '\!'];

    return str_replace($escape_characters, $escaped_characters, $string);
}

/**
 * Publish last episode to Telegram channel
 */
function publish_to_telegram(SimpleXMLElement $last_episode, string $telegram_chat_id, string $telegram_api_key, string $template): false|string
{
    if (empty($title = $last_episode->title) || empty($link = $last_episode->link)) {
        error_log('Error fetching last episode: ' . print_r(error_get_last(), true));
        exit(1);
    }

    // Extract hashtags from itunes:keywords
    $hashtags = '';
    $itunes_ns = $last_episode->children('http://www.itunes.com/dtds/podcast-1.0.dtd');
    if (isset($itunes_ns->keywords)) {
        $keywords = (string)$itunes_ns->keywords;
        if (!empty($keywords)) {
            $keywords_array = array_map('trim', explode(',', $keywords));
            $hashtags_array = array_map(function($keyword) {
                return '#' . str_replace(' ', '', $keyword);
            }, $keywords_array);
            $hashtags = implode(' ', $hashtags_array);
        }
    }

    $content = str_replace(
        ['{title}', '{link}', '{hashtags}'],
        [escape_telegram((string)$title), escape_telegram((string)$link), escape_telegram($hashtags)],
        $template
    );

    echo "Publishing to Telegram: $content\n";

    $telegram_api_url = "https://api.telegram.org/bot";

    $response = file_get_contents(
        $telegram_api_url . "$telegram_api_key/sendMessage",
        false,
        stream_context_create([
            'http' => [
                'header' => "Content-type: application/x-www-form-urlencoded\r\n",
                'method' => 'POST',
                'content' => http_build_query([
                    'chat_id' => $telegram_chat_id,
                    'text' => $content,
                    'parse_mode' => 'MarkdownV2',
                    'disable_notification' => true,
                ]),
            ],
        ])
    );

    if ($response === false) {
        error_log('Error publishing to Telegram: ' . print_r(error_get_last(), true));
        exit(1);
    }

    // Ensure Telegram API acknowledged success
    $decoded = json_decode($response, true);
    if ($decoded === null) {
        error_log('Invalid response from Telegram API (non-JSON).');
        exit(1);
    }

    if (!isset($decoded['ok']) || $decoded['ok'] !== true) {
        $description = $decoded['description'] ?? 'Unknown error';
        error_log('Telegram API error: ' . $description);
        exit(1);
    }

    return $response;
}

/**
 * Add episode link into file
 */
function mark_as_published($last_episode, $file_path): void
{
    if (($link = $last_episode->link) === null) {
        error_log('Error fetching last episode: ' . print_r(error_get_last(), true));
        exit(1);
    }

    echo "Marking as published: $link\n";

    file_put_contents($file_path, "$link\n", FILE_APPEND);
}

/**
 * Search episode link into file
 */
function is_just_published($last_episode, $file_path): bool
{
    if (($link = $last_episode->link) === null) {
        error_log('Error fetching last episode: ' . print_r(error_get_last(), true));
        exit(1);
    }

	// Create file if it doesn't exist
	if (!file_exists($file_path)) {
		touch($file_path);
	}

    $content = file_get_contents($file_path);

    return str_contains($content, $link);
}

// Main execution
$telegram_chat_id = getenv('TELEGRAM_CHAT_ID');
$telegram_api_key = getenv('TELEGRAM_BOT_API_KEY');
$config_file = './podcasts.json';

// Load all podcasts configuration
$podcasts = load_podcasts_config($config_file);

echo "Found " . count($podcasts) . " podcast(s) to process\n\n";

// Process each podcast
foreach ($podcasts as $podcast) {
	echo "========================================\n";
	echo "Processing: {$podcast['name']}\n";
	echo "========================================\n";

	$feed_url = $podcast['feed_url'];
	$template = $podcast['template'];
	$file_path = get_tracking_file($podcast['id']);

	// Fetch last episode
    if ($last_episode = fetch_last_episode($feed_url)) {
		echo "Last episode fetched: " . $last_episode->link . "\n";
	} else {
		echo "Error fetching episode for {$podcast['name']}, skipping...\n\n";
		continue;
	}

	// Check if already published
 if (!is_just_published($last_episode, $file_path)) {
        if (publish_to_telegram($last_episode, $telegram_chat_id, $telegram_api_key, $template)) {
            mark_as_published($last_episode, $file_path);
            echo "✓ Successfully published!\n";
        } else {
            echo "✗ Error publishing to Telegram\n";
            // Fail the pipeline if publishing did not succeed
            exit(1);
        }
    } else {
        echo "Episode already published\n";
    }

	echo "\n";
}

echo "All podcasts processed!\n";
