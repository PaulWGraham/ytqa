import argparse
import json
import Levenshtein

def find_orphaned_videos(site_videos, youtube_videos):
    site_videos_ids = {site_video['youtube_id'] for site_video in site_videos if site_video['youtube_id'] is not None}
    orphaned_videos = []
    for youtube_video in youtube_videos:
        if youtube_video['snippet']['resourceId']['videoId'] not in site_videos_ids:
            orphaned_videos.append(youtube_video)

    return orphaned_videos


def find_likely_matches_by_name(site_videos, youtube_videos, threshold = 0):
    likely_matches = []
    if threshold == 0:
        for youtube_video in youtube_videos:
            matches = []
            youtube_video_name = youtube_video['snippet']['title']
            for site_video in site_videos:
                site_video_name = site_video['name']
                if site_video_name == youtube_video_name:
                    matches.append([0, site_video])

            if matches:
                matches.sort(key = lambda match: match[0])
                likely_matches.append([youtube_video, matches])
    else:
        for youtube_video in youtube_videos:
            matches = []
            youtube_video_name = youtube_video['snippet']['title']
            for site_video in site_videos:
                site_video_name = site_video['name']
                edit_distance = Levenshtein.distance(site_video_name, youtube_video_name)
                if edit_distance <= threshold:
                    matches.append([edit_distance, site_video])

            if matches:
                matches.sort(key = lambda match: match[0])
                likely_matches.append([youtube_video, matches])

    return likely_matches

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description =  'Process video data to find YouTube videos '
                                                    'that do not have an associated Giant Bomb '
                                                    'video.')
    parser.add_argument('site_file', type = str,
                       help = 'Path to a json file containing data about the videos on Giant Bomb')
    parser.add_argument('youtube_file', type = str,
                       help = 'Path to a json file containing data about the videos on YouTube')
    parser.add_argument('output_file', type = str,
                       help = 'Path to a file where the output will be written.')
    parser.add_argument('--threshold', type = int, default = 0,help = 'When finding likely matches between '
    'orphaned YouTube videos and Giant Bomb video titles this value is used to determine what '
    'titles are considered matches. The lower the value the more exact the match needed. '
    'Defaults to 0 which means exact match.')
    parser.add_argument('--skip_matches', action = 'store_true')
    args = parser.parse_args()

    with open(args.site_file) as site_video_file:
        print("Loading Giant Bomb video data.")
        site_videos = json.load(site_video_file)
        print("Loaded data for {} Giant Bomb videos.".format(len(site_videos)))


    with open(args.youtube_file) as youtube_video_file:
        print("Loading YouTube video data.")
        youtube_videos = json.load(youtube_video_file)
        print("Loaded data for {} YouTube videos.".format(len(youtube_videos)))


    with open(args.output_file , "w") as output_file:
        print("Finding orphaned YouTube videos.")
        orphaned_videos = find_orphaned_videos(site_videos, youtube_videos)
        print("Found {} orphaned YouTube videos.".format(len(orphaned_videos)))
        orphaned_videos_output = [orphaned_video['snippet']['resourceId']['videoId'] for orphaned_video in orphaned_videos]

        output = orphaned_videos_output
        if not args.skip_matches:
            print("Finding likely matches.")
            likely_matches = find_likely_matches_by_name(site_videos, orphaned_videos, args.threshold)
            print("Found likely matches for {} orphaned YouTube videos.".format(len(likely_matches)))
            likely_matches_output = []
            for youtube_video, matches in likely_matches:
                matches_output = []
                for match in matches:
                    matches_output.append([match[0], match[1]['guid']])
                likely_matches_output.append([youtube_video['snippet']['resourceId']['videoId'], matches_output])
            output = {}
            output['orphaned_videos'] = orphaned_videos_output
            output['likely_matches'] =  likely_matches_output
            output['threshold'] = args.threshold
        print("Saving output.")
        json.dump(output, output_file)
    print("Done.")
