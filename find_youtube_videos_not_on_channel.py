import argparse
import json

def find_youtube_videos_not_on_channel(site_videos, youtube_videos):
    youtube_videos_ids = {youtube_video['snippet']['resourceId']['videoId'] for youtube_video in youtube_videos}
    missing_videos = []
    for site_video in site_videos:
        if site_video['youtube_id'] is not None and site_video['youtube_id'] not in youtube_videos_ids:
            missing_videos.append(site_video)
    return missing_videos

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description =  ''
                                                    '')
    parser.add_argument('giantbomb_video_data_file', type = str,
                           help =   'Path to a file that contains data about videos on Giant Bomb.')
    parser.add_argument('youtube_video_data_file', type = str,
                           help =   'Path to a file that contains data about videos on a YouTube channel.')
    parser.add_argument('output_file', type = str,
                           help =   'Path to a file where the output will be written.')
    args = parser.parse_args()

    with open(args.giantbomb_video_data_file) as giantbomb_file:
        giantbomb_data = json.load(giantbomb_file)

    with open(args.youtube_video_data_file) as youtube_file:
        youtube_data = json.load(youtube_file)

    print("Checking {} videos.".format(len(youtube_data)))
    videos_with_incorrect_youtube_links = find_youtube_videos_not_on_channel(giantbomb_data, youtube_data)
    links = [(video['youtube_id'], video) for video in videos_with_incorrect_youtube_links]
    print(links)
    # with open(args.output_file, 'w') as output_file:
    #     json.dump(videos_with_incorrect_youtube_links, output_file)

    print("Found {} videos with incorrect youtube links.".format(len(\
                                                        videos_with_incorrect_youtube_links)))
