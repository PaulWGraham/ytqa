ytqa
====

**ytqa** checks for broken YouTube links on giantbomb.com videos and looks for orphaned videos on the Giant Bomb YouTube channel. **ytqa** also tries to match giantbomb.com videos with the orphaned YouTube videos if finds based on the respective video's names.


**ytqa** is a docker image built to be run as a GCP Cloud Run service that is routinely triggered by a Cloud Scheduler job. **ytqa** stores it's output in a GCP Storage bucket and/or publishes it's output to a GCP Pub_Sub topic.

An example of **ytqa** output can be found at: <https://raw.githubusercontent.com/PaulWGraham/ytqa/master/exampleoutput.json>

The installation instructions below cover: uploading the docker image, enabling the needed APIs, creating the Cloud Run service, and creating the Cloud Scheduler job.


Installation:
-------------

1. **Ensure that the correct GCP project is active.**

2. **Enable the YouTube Data API v3.**

   Go to <https://console.cloud.google.com/apis/library/youtube.googleapis.com> and click enable.

3. **Create a restricted YouTube API key.**

   Go to <https://console.cloud.google.com/apis/api/youtube.googleapis.com/credentials> and click CREATE CREDENTIALS -> API KEY. On the "API key created" dialog box that appears click RESTRICT KEY. Rename the key to ytqa . Then under "API restrictions" select the "Restrict key" radio button. On the dropdown that appears select "YouTube Data API v3". Click SAVE. Note the key for later.

4. **Create a Giant Bomb API key.**

   The Giant Bomb API key should be from a premium service account with no special privileges.

5. **Download the ytqa project source.**

   Download the ytqa source from <https://github.com/PaulWGraham/ytqa/archive/master.zip>

6. **Build the ytqa docker image.**

   In the source directory:

   ```
   docker build -t ytqa .
   ```

7. **Tag and upload the ytqa docker image to the GCP project's Container Registry.**

   Use the following commands substituting the GCP project name where appropriate:

   ```
   docker tag ct gcr.io/{GCP project name}/ytqa
   ```

   ```
   gcloud docker -- push gcr.io/{GCP project name}/ytqa
   ```

8. **Enable the Cloud Run API**

   Go to <https://console.cloud.google.com/apis/library/run.googleapis.com> and click enable.

9. **Create and configure the ytqa Cloud Run service.**

   Go to <https://console.cloud.google.com/run> then click CREATE SERVICE. Now do the following:

   1. In the "Container" section find the "Container image URL" field then click SELECT. In the dialog box that appears select the ytqa image then click continue.

   2. In the "Deployment platform" section ensure that "Cloud Run (fully managed)" radio button is selected. Find the "Region" field and ensure that the appropriate region is selected.

   3. In the "Service settings" section select the "Require authentication" radio button.

   4. Click the SHOW OPTIONAL REVISION SETTINGS drop-down.

   5. In the "Revision settings" section change the "Memory allocated" drop-down to 1 GiB. Change the "Request timeout" value to 900 .

   6. Change the "Maximum number of instances" to 2 .

   7. Add the following "Environment variables":

      * `YOUTUBE_API_KEY` : {The YouTube API key created in step 3}

      * `GIANTBOMB_API_KEY` : {The Giant Bomb API key created in step 4}

      * `BUCKET` : {The name of a GCP Storage bucket.}

         (If using a bucket to collect ytqa reports.)

      * `TOPIC` : {The name of a GCP Pub_Sub topic.}

         (If using a topic to collect ytqa reports.)

      * `PROJECT` : {The name of the GCP Project containing the topic specified by TOPIC.}

         (If using a topic to collect ytqa reports.)

      * `GIANTBOMB_API_CALL_DELAY` : {Optional: The delay in seconds between each call to the GB API. Defaults to 1}

         (This is used to keep ytqa from sending too much traffic to the GB API at once. It also accounts for the majority of ytqa's run time.)

      * `ORPHANED_YOUTUBE_VIDEOS_NAME_MATCH_THRESHOLD` : {Optional: The threshold for name matches when trying to pair orphaned YouTube videos with GB videos. Defaults to 1}

   8. Click CREATE

10. **Enable the Cloud Scheduler API**

   Go to <https://console.cloud.google.com/apis/library/cloudscheduler.googleapis.com> and click enable.

11. **Create a Cloud Scheduler service account and create a Cloud Scheduler**

   Go to <https://cloud.google.com/run/docs/triggering/using-scheduler> and follow the instructions to create a service account for Cloud Scheduler to access the ytqa Cloud Run service created in step 7.

   Then follow the instructions to create a Cloud Scheduler job that will routinely run the ytqa Cloud Run service. Use <https://crontab.guru/> as a reference for the cron schedule expression syntax. A suggested schedule to use is:

   `0 9 * * 1-5`

   which runs the ytqa Cloud Run service at 09:00am every day of the week Monday through Friday.

License
-------

Copyright 2020 Paul W. Graham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
