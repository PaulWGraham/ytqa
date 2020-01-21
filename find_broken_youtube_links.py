import argparse
import json

def find_broken_youtube_links(youtube_data):
    videos_with_broken_youtube_links = []
    for guid, data in youtube_data:
        try:
            if not data['items']:
                videos_with_broken_youtube_links.append(guid)
        except:
            if 'error' not in data:
                print(guid, data)
    return videos_with_broken_youtube_links


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description =  'Find the GUIDs of videos whose YouTube data '
                                                    'indicates a broken YouTube link.')
    parser.add_argument('youtube_video_data_file', type = str,
                           help =   'Path to a file that contains data about videos on YouTube.')
    parser.add_argument('output_file', type = str,
                           help =   'Path to a file where the output will be written.')
    args = parser.parse_args()


    with open(args.youtube_video_data_file) as youtube_file:
        youtube_data = json.load(youtube_file)

    print("Checking {} videos.".format(len(youtube_data)))
    videos_with_broken_youtube_links = find_broken_youtube_links(youtube_data)
    with open(args.output_file, 'w') as output_file:
        json.dump(videos_with_broken_youtube_links, output_file)

    print("Found {} videos with broken youtube links.".format(len(\
                                                        videos_with_broken_youtube_links)))
