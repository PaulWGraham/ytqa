import json
import logging
import os
import sys
import tempfile
import time
import uuid

import fetch_video_data
import fetch_youtube_video_list_for_channel
import fetch_youtube_video_data
import find_broken_youtube_links
import find_orphaned_youtube_videos
import find_youtube_videos_not_on_channel
import gbapi

from flask import Flask
from google.cloud import storage, pubsub_v1

# Environment variable names
GCP_BUCKET_NAME_LABEL = 'BUCKET'
GCP_PROJECT_NAME_LABEL = 'PROJECT'
GCP_PUB_SUB_TOPIC_NAME_LABEL = 'TOPIC'

YOUTUBE_API_KEY_LABEL = 'YOUTUBE_API_KEY'
GIANTBOMB_API_KEY_LABEL = 'GIANTBOMB_API_KEY'
GIANTBOMB_API_CALL_DELAY_LABEL = 'GIANTBOMB_API_CALL_DELAY'
ORPHANED_YOUTUBE_VIDEOS_NAME_MATCH_THRESHOLD_LABEL = \
    'ORPHANED_YOUTUBE_VIDEOS_NAME_MATCH_THRESHOLD'

DEFAULT_ORPHANED_YOUTUBE_VIDEOS_NAME_MATCH_THRESHOLD = 1

app = Flask(__name__)

@app.route('/')
def ytqa():
    fatal_error = False
    if YOUTUBE_API_KEY_LABEL not in os.environ:
        fatal_error = True
        logging.error(f"{YOUTUBE_API_KEY_LABEL} environment variable not set.")

    if GIANTBOMB_API_KEY_LABEL not in os.environ:
        fatal_error = True
        loggin.error(f"{GIANTBOMB_API_KEY_LABEL} environment variable not set.")

    if GCP_BUCKET_NAME_LABEL not in os.environ and \
    GCP_BUCKET_NAME_LABEL not in os.environ:
        fatal_error = True
        logging.error(f"Neither the {GCP_BUCKET_NAME_LABEL} environment"
        f" variable nor the {GCP_PUB_SUB_TOPIC_NAME_LABEL} environment "
        "variable is set.")

    if GCP_PUB_SUB_TOPIC_NAME_LABEL in os.environ and \
    GCP_PROJECT_NAME_LABEL not in os.environ:
        fatal_error = True
        logging.error(f"{GCP_PUB_SUB_TOPIC_NAME_LABEL} environment variable is "
        f"set but the required {GCP_PROJECT_NAME_LABEL} environment variable "
        "is not set.")

    if fatal_error:
        quit(1)

    # Fetch data for all Giant Bomb videos.
    logging.info("Using the Giant Bomb API to fetch Giant Bomb video data.")
    if GIANTBOMB_API_CALL_DELAY_LABEL not in os.environ:
        logging.info("No delay between calls to the Giant Bomb API set. "
                f"Using default delay of {gbapi.DEFAULT_DELAY_BETWEEN_CALLS}.")
        delay = gbapi.DEFAULT_DELAY_BETWEEN_CALLS
    else:
        delay = float(os.environ[GIANTBOMB_API_CALL_DELAY_LABEL])
    gb_video_data = fetch_video_data.fetch_video_data(os.environ[GIANTBOMB_API_KEY_LABEL], delay)
    logging.info(f"Fetched data for {len(gb_video_data)} Giant Bomb videos.")

    # Fetch a list of all videos on the GB YouTube channel.
    logging.info("Using the YouTube API to fetch data for videos on the Giant Bomb YouTube channel.")
    yt_video_data = fetch_youtube_video_list_for_channel.fetch_youtube_video_list_for_playlist(\
    fetch_youtube_video_list_for_channel.GB_PLAYLIST_ID, os.environ[YOUTUBE_API_KEY_LABEL])
    logging.info(f"Fetched data for {len(yt_video_data)} YouTube videos.")

    # Look for YouTube IDs that are on the GB site but not on the list of IDs grabbed
    # from the GB YouTube channel.
    logging.info("Looking for YouTube Video IDs associated with Giant Bomb videos that are missing "
            "from the Giant Bomb YouTube channel.")
    gb_videos_with_yt_id_not_on_channel = \
    find_youtube_videos_not_on_channel.find_youtube_videos_not_on_channel(gb_video_data, yt_video_data)
    logging.info(f"Found {len(gb_videos_with_yt_id_not_on_channel)} missing YouTube links.")

    # A YouTube ID that is on the GB site but not on the GB YT channel isn't necessarily
    # a broken link (See: 2300-12968). So each potentially bad YouTube ID is checked using the
    # YouTube API.

    # Fetch the video data from YouTube.
    logging.info("Using the YouTube API to check the status of the YouTube Video IDs "
            "missing from the Giant Bomb YouTube channel.")
    yt_video_check_data = []
    for video in gb_videos_with_yt_id_not_on_channel:
        youtube_id = video.get('youtube_id')
        guid = video['guid']
        if youtube_id:
            yt_video_check_data.append(\
            [guid, fetch_youtube_video_data.fetch_youtube_data_for_video_id(youtube_id, \
                                                                os.environ[YOUTUBE_API_KEY_LABEL])])
    # Process the video data.
    logging.info("Looking for broken YouTube links.")
    broken_yt_links = find_broken_youtube_links.find_broken_youtube_links(yt_video_check_data)
    logging.info(f"Found {len(broken_yt_links)} broken YouTube links.")

    # Find videos that are on the GB YouTube channel but aren't associated with a video on the
    # GB site.
    logging.info("Looking for YouTube videos that don't have a corresponding Giant Bomb video.")
    orphaned_yt_videos = find_orphaned_youtube_videos.find_orphaned_videos(gb_video_data, \
                                                                            yt_video_data)
    logging.info(f"Found {orphaned_yt_videos} YouTube videos without a "
                "corresponding Giant Bomb video.")

    # Based on the video name find videos on the GB site that might match unassociated videos on
    # the GB YouTube channel.
    logging.info("Looking for matching Giant Bomb videos based on video name.")
    if ORPHANED_YOUTUBE_VIDEOS_NAME_MATCH_THRESHOLD_LABEL not in os.environ:
        logging.info("No orphaned youtube videos match threshold set. "
                "Using default threshold of "
                f"{DEFAULT_ORPHANED_YOUTUBE_VIDEOS_NAME_MATCH_THRESHOLD}.")
        match_threshold = DEFAULT_ORPHANED_YOUTUBE_VIDEOS_NAME_MATCH_THRESHOLD
    else:
        match_threshold = int(os.environ[ORPHANED_YOUTUBE_VIDEOS_NAME_MATCH_THRESHOLD_LABEL])

    likely_gb_matches_for_orphaned_yt_videos = \
        find_orphaned_youtube_videos.find_likely_matches_by_name(gb_video_data, orphaned_yt_videos,\
             match_threshold)
    logging.info(f"Found possible matches for {likely_gb_matches_for_orphaned_yt_videos} YouTube "
                "videos.")

    orphaned_yt_videos_output = []
    for youtube_video in orphaned_yt_videos:
        orphaned_yt_videos_output.append(youtube_video['snippet']['resourceId']['videoId'])

    likely_matches_output = []
    for youtube_video, matches in likely_gb_matches_for_orphaned_yt_videos:
        matches_output = []
        for match in matches:
            matches_output.append([match[0], match[1]['guid']])
        likely_matches_output.append([youtube_video['snippet']['resourceId']['videoId'], \
                                        matches_output])

    data = {}
    data["broken_yt_links"] = broken_yt_links
    data["orphaned_yt_videos"] = {}
    data["orphaned_yt_videos"]['videos'] = orphaned_yt_videos_output
    data["orphaned_yt_videos"]['likely_matches'] =  likely_matches_output
    data["orphaned_yt_videos"]['threshold'] = match_threshold

    # Write output to a bucket and/or a pub_sub topic
    if GCP_BUCKET_NAME_LABEL in os.environ:
        storage_client = storage.Client()
        _, temp_local_filename = tempfile.mkstemp()

        with open(temp_local_filename, "w") as temp_file:
            json.dump(data, temp_file)

        file_name = (time.strftime("%Y/%m/%d/%H/%M/%S/") + str(uuid.uuid4())
                    ).encode('utf-8')
        bucket = storage_client.bucket(os.environ[GCP_BUCKET_NAME_LABEL])
        blob = bucket.blob(file_name)
        blob.upload_from_filename(temp_local_filename)

    if GCP_PUB_SUB_TOPIC_NAME_LABEL in os.environ:
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(str(os.environ[GCP_PROJECT_NAME_LABEL]),
                                    str(os.environ[GCP_PUB_SUB_TOPIC_NAME_LABEL]))
        publisher.publish(topic_path, data = json.dumps(data).encode("utf-8"))

    return 'OK', 200

if __name__ == "__main__":
    app.run(debug=False,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))
