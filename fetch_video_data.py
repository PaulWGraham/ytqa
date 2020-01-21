import gbapi
import argparse
import json

def fetch_video_data(api_key, delay):
    videos_generator = gbapi.PaginatedResource(api_key, gbapi.APIItem, delay_between_calls = delay,
                                                endpoint = gbapi.ENDPOINTS["VIDEOS"])

    videos = []
    for video in videos_generator:
        videos.append(video.data())
    return videos

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description =  'Collect video data for all videos on '
                                                    'Giant Bomb. Uses the Giant Bomb API.')
    parser.add_argument('filename', type = str,
                           help =   'Path to a file where the video data will be written.')
    parser.add_argument('api_key', type = str, help = 'Giant Bomb API key.')
    parser.add_argument('delay', type = float, default = gbapi.DEFAULT_DELAY_BETWEEN_CALLS,
                            help = 'The delay between calls to the Giant Bomb API.')
    args = parser.parse_args()


    videos = fetch_video_data(args.api_key, args.delay)
    with open(args.filename, "w") as video_file:
        json.dump(videos, video_file)
    print("Video data collected for {} videos.".format(len(videos)))
