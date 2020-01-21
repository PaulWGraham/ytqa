import argparse
import json
import requests

PARAMS =    {
                'part' : "snippet",
                'maxResults' : 50
            }

GB_PLAYLIST_ID = "UUmeds0MLhjfkjD_5acPnFlQ"
YOUTUBE_API_ENDPOINT = "https://www.googleapis.com/youtube/v3/playlistItems"

def fetch_youtube_video_list_for_playlist(playlist_id, api_key):
    params = PARAMS.copy()
    params['playlistId'] = playlist_id
    params['pageToken'] = None
    params['key'] = api_key
    videos = []
    while True:
        response = requests.get(YOUTUBE_API_ENDPOINT, params = params)
        response.raise_for_status()
        page_data = response.json()
        videos.extend(page_data['items'])
        params['pageToken'] = page_data.get('nextPageToken')
        if not params['pageToken']:
            break
    return videos

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description =  'Gets data for all videos on the Giant Bomb '
                                                    'YouTube channel.')
    parser.add_argument('output_file', type = str,
    help =   'Path to a file where the output will be written.')
    parser.add_argument('api_key', type = str, help = 'YouTube API key.')
    args = parser.parse_args()

    videos = fetch_youtube_video_list_for_playlist(GB_PLAYLIST_ID, args.api_key)

    print("Data for {} videos found.".format(len(videos)))

    with open(args.output_file, "w") as output_file:
        json.dump(videos, output_file)
