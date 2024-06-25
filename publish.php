<?php

/**
 * Fetch last episode from podcast feed
 */
function fetch_last_episode($feed_url): SimpleXMLElement|false
{
    $feed = simplexml_load_file($feed_url);
    return $feed->channel->item[0];
}

/**
 * Publish last episode to Telegram channel
 * @param $last_episode
 * @param $telegram_chat_id
 * @param $telegram_api_key
 * @param $template
 * @return false|string
 */
function publish_to_telegram($last_episode, $telegram_chat_id, $telegram_api_key, $template): false|string
{
    $content = str_replace(
        ['{title}', '{link}'],
        [$last_episode->title, $last_episode->link],
        $template
    );

    $data = array(
        'chat_id' => $telegram_chat_id,
        'text' => $content,
    );

    $options = array(
        'http' => array(
            'header' => "Content-type: application/x-www-form-urlencoded\r\n",
            'method' => 'POST',
            'content' => http_build_query($data),
        ),
    );

    $url = "https://api.telegram.org/bot$telegram_api_key/sendMessage";
    $context = stream_context_create($options);
    return file_get_contents($url, false, $context);
}

/**
 * Add episode link into file
 */
function mark_as_published($last_episode, $file_path): int|false
{
    $link = $last_episode->link;

    return file_put_contents($file_path, "$link\n", FILE_APPEND);
}

/**
 * Search episode link into file
 */
function is_just_published($last_episode, $file_path): bool
{
    $link = $last_episode->link;
    $content = file_get_contents($file_path);
    return str_contains($content, $link);
}

$feed_url = getenv('PODCAST_RSS_URL');
$telegram_chat_id = getenv('TELEGRAM_CHAT_ID');
$telegram_api_key = getenv('TELEGRAM_BOT_API_KEY');
$template = getenv('TELEGRAM_TEMPLATE');
$file_path = './published_episodes.txt';

if ($last_episode = fetch_last_episode($feed_url)) {
    echo "Last episode fetched successfully: " . $last_episode->link . "\n";
}

if (!is_just_published($last_episode, $file_path)) {
    if (publish_to_telegram($last_episode, $telegram_chat_id, $telegram_api_key, $template)) {
        if (mark_as_published($last_episode, $file_path)) {
            echo "Episode published successfully\n";
        } else {
            echo "Error saving episode\n";
        }
    } else {
        echo "Error publishing episode\n";
    }
} else {
    echo "Episode already published\n";
}
