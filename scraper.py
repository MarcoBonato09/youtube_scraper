import requests

API_KEY = "YOUR_API_KEY"

VIDEOS_COLUMNS = ["id", "title", "description", "publishedAt", "tags", "categoryId", 
                "topicCategories", "defaultLanguage", "defaultAudioLanguage", "duration", 
                "dimension", "definition", "url", "width", "height", "caption", "allowed", 
                "blocked", "license", "publicStatsViewable", "madeForKids", "viewCount", 
                "likeCount", "commentCount"]

COMMENTS_COLUMNS = ["id", "authorDisplayName", "authorProfileImageUrl","textDisplay", 
                "textOriginal", "likeCount", "publishedAt", "updatedAt", "value", "videoId"]


def flatten(dictionary):
        result = {}
        for key, value in dictionary.items():
                if type(value) == dict:
                        result = result | flatten(dictionary[key])
                else:
                        result = result | {key: value}
        return result


def return_request(url, request_parameters):
        request = requests.get(url, params=request_parameters)
        return request.json()


def extract_resource_as_csv(resource, columns):
        csv_line = ""
        resource = flatten(resource)
        for column in columns:
                try:
                        column_data = repr(resource[column]).replace("'", "").replace('"', '')
                        if column in ["tags", "topicCategories", "allowed", "blocked"]:
                                column_data = column_data.replace("[", "").replace("]", "")
                                column_data = column_data.replace(" ", "")
                        csv_line += f'"{column_data}",'
                except KeyError:
                        csv_line += ","
        return csv_line[0:-1] + "\n"


def get_comments(video_id, columns):
        output = ""
        parameters = {"key": API_KEY, "videoId": video_id, "maxResults": "100", "part": "id, snippet", 
                        "textFormat": "html", "order": "relevance", 
                        "fields": "items(snippet(channelId, topLevelComment(id, snippet(authorDisplayName, "
                        + "authorProfileImageUrl, authorChannelId(value), videoId, textDisplay, "
                        + "textOriginal, likeCount, publishedAt, updatedAt))))"}
        comments = return_request("https://www.googleapis.com/youtube/v3/commentThreads", parameters)
        for comment in comments.get("items", []):
                output += extract_resource_as_csv(comment, columns)
        return output


def get_data(key, videos_resource_properties, comments_resource_properties):
        videos_csv_data = ""
        comments_csv_data = ""
        parameters = {"key": key, "maxResults": "50", "pageToken": " ",
                        "chart": "mostPopular", 
                        "part": "snippet, contentDetails, status, statistics, topicDetails", 
                        "fields": "nextPageToken, items(id,"
                        + "snippet(publishedAt, title, description, thumbnails, tags, categoryId, defaultLanguage, defaultAudioLanguage),"
                        + "contentDetails(duration, dimension, definition, caption, regionRestriction),"
                        + "status(license, publicStatsViewable, madeForKids),"
                        + "statistics(viewCount, likeCount, commentCount),"
                        + "topicDetails(topicCategories))"}

        while parameters["pageToken"]:
                videos = return_request("https://www.googleapis.com/youtube/v3/videos", parameters)
                for video in videos["items"]:
                        videos_csv_data += extract_resource_as_csv(video, videos_resource_properties)
                        comments_csv_data += get_comments(video["id"], comments_resource_properties)
                parameters["pageToken"] = videos.get("nextPageToken", None)
        return [videos_csv_data, comments_csv_data]


csv_data = get_data(API_KEY, VIDEOS_COLUMNS, COMMENTS_COLUMNS)
videos = open("videos.csv", "a")
videos.write(csv_data[0])
videos.close()

comments = open("comments.csv", "a")
comments.write(csv_data[1])
comments.close()
