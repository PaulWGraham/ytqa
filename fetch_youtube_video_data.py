import argparse
import json
import requests

PARAMS =    {
                'part' : "snippet"
            }

YOUTUBE_API_ENDPOINT = "https://www.googleapis.com/youtube/v3/videos"

def fetch_youtube_data_for_video_id(youtube_id, api_key):
    params = PARAMS.copy()
    params['id'] = youtube_id
    params['key'] = api_key
    response = requests.get(YOUTUBE_API_ENDPOINT, params = params)
    return response.json()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description =  'Collect video data for Giant Bomb videos on '
                                                    'YouTube using the YouTube API.')
    parser.add_argument('site_video_data_file', type = str,
                           help =   'Path to a file that contains data about videos on Giant Bomb.')
    parser.add_argument('output_file', type = str,
                           help =   'Path to a file where the output will be written.')
    parser.add_argument('api_key', type = str, help = 'YouTube API key.')
    args = parser.parse_args()

    with open(args.site_video_data_file) as video_file:
        videos = json.load(video_file)

    youtube_video_data = []
    for video in videos:
        youtube_id = video.get('youtube_id')
        guid = video['guid']
        if youtube_id:
            print("{} : {}".format(guid, youtube_id))
            youtube_video_data.append([guid, fetch_youtube_data_for_video_id(youtube_id, args.api_key)])


    with open(args.output_file, "w") as youtube_data_file:
        json.dump(youtube_video_data, youtube_data_file)

    print("count: ", len(youtube_video_data))
