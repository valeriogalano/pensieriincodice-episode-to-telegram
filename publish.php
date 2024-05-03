<?php

/**
 * Fetch last episode from podcast feed
 */
function fetch_last_episode($feed_url)
{
    $feed = simplexml_load_file($feed_url);
    $last_episode = $feed->channel->item[0];
    return $last_episode;
}

/**
 * Publish last episode to Telegram channel
 * @param $last_episode
 * @param $telegram_chat_id
 * @param $telegram_api_key
 * @param $template
 * @return false|string
 */
function publish_to_telegram($last_episode, $telegram_chat_id, $telegram_api_key, $template)
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
function mark_as_published($last_episode, $file_path)
{
    $link = $last_episode->link;

    file_put_contents($file_path, "$link\n", FILE_APPEND);
}

/**
 * Search episode link into file
 */
function is_just_published($last_episode, $file_path)
{
    $link = $last_episode->link;
    $content = file_get_contents($file_path);
    return strpos($content, $link) !== false;
}

$feed_url = getenv('PODCAST_RSS_URL') ?? $argv[1];
$telegram_chat_id = getenv('TELEGRAM_CHAT_ID') ?? $argv[2];
$telegram_api_key = getenv('TELEGRAM_API_KEY') ?? $argv[3];
$template = getenv('TELEGRAM_TEMPLATE') ?? $argv[4];
$file_path = './published_episodes.txt';

$last_episode = fetch_last_episode($feed_url);
if (!is_just_published($last_episode, $file_path)) {
    if (publish_to_telegram($last_episode, $telegram_chat_id, $telegram_api_key, $template)) {
        mark_as_published($last_episode, $file_path);
    }
}