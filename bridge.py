#!/usr/bin/python3
# Access vimeo resources
import vimeo, requests, json, wget, os

# Constants
VIMEO_TOKEN = "xxxx-xxxx-xxxx-xxxx-xxxx-xxxxx"
VIMEO_KEY = "xxxx-xxxx-xxxx-xxxx-xxxx-xxxx-xx"
VIMEO_SECRET = "xxxx-xxxx-xxxx-xxxx-xxxx-xxxx"

BUNNY_STREAM_RW_API = "xxxx-xxxx-xxxx-xxxx-xxxx-xxxx"

results_per_page = 10

# Dict to store the list of libraries with library ID
lib_dict = {}

# Functions
# Return maximum available resolution video
def get_max_resolution(links_json):
    max_resolution_link = ""
    width = 0
    for link in links_json:
        if link['width'] > width:
            width = link['width']
            max_resolution_link = link['link']
    # print ("Width: ", width)
    return max_resolution_link

# Get Vimeo video folder
def get_folder(parent_folder):
    if (parent_folder is None):
        return "Unsorted"
    else:
        return parent_folder['name']

# Function to add new video library 
def add_video_library(lib):
    #define url, headers and payload
    url = "https://api.bunny.net/videolibrary"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "AccessKey": BUNNY_STREAM_RW_API
    }
    #payload contains name and ID of the library
    payload = {
        # No need to add id in payload, 
        # the id will be returned in response
        #"id": "",
        "name" : lib
    }

    response = requests.request("POST", url, json=payload, headers=headers)
    response = response.json()
    lib_id = response['libraryId']
    return lib_id  #############################

# Function to create new video and get video ID
def create_video(lib_id, video_title):
    url = "http://video.bunnycdn.com/library/{0}/videos".format(str(lib_id))
    headers = {
        "Content-Type": "application/*+json",
        "AccessKey": BUNNY_STREAM_RW_API
        }
    payload = {
        "title" : video_title
    }
    response = requests.request("POST", url, json = payload, headers=headers)
    response = response.json()
    video_id = resposne['videoId']
    return video_id  ##############################

# Function to upload the video 
def upload_video(lib_id, video_id, filename):
    url = "http://video.bunnycdn.com/library/libraryId/videos/videoId"
    headers = {
        "Content-Type": "application/*+json",
        "AccessKey": BUNNY_STREAM_RW_API
        }
    payload = {
        "libraryId": lib_id,
        "videoId" : video_id
    }

    # upload using requests Session
    '''files = {'file': open(filename, 'rb')}
    with requests.Session() as session:
        response = session.post(url, files=files, json = payload, headers=headers)'''


    # upload using requests PUT method
    with open(filename, 'rb') as f:    
        response = requests.request("PUT", url, json = payload, headers=headers, data = f)

    flag = True if response.status_code == 201 else False
    return flag
    

# Initialise vimeo object with access tokens
# Client Tokes
# USE WITH CARE - Avoid write operations
v = vimeo.VimeoClient(
    token = VIMEO_TOKEN,
    key = VIMEO_KEY,
    secret = VIMEO_SECRET
)

# Make the request to the server for the "/me" endpoint.
# See page and per_page variable. We need to cycle through page 
my_videos_count = v.get('/me/videos', params={"fields": "name"})

# Make sure we got back a successful response.
assert my_videos_count.status_code == 200

data_totals = my_videos_count.json()
total_videos = data_totals['total']

print ("Total videos to transfer: ", total_videos)

total_pages = total_videos // results_per_page

# Any additional page required to cover the remainder of videos
additional_page = total_videos % results_per_page

if (additional_page > 0):
    total_pages = total_pages + 1

print ("Total pages: [", total_pages, "] of [", results_per_page, "] videos per page.")

# Loop through all pages and process the videos
page = 1
while (page <= total_pages):
    print ("=============================== [Processing page: ", page, "] ===============================")
    my_videos = v.get('/me/videos', params={"fields": "name, download.link, download.size, download.width, parent_folder.name", "page": page, "per_page": results_per_page})
    assert my_videos.status_code == 200
    page = page + 1

    # Parse result and create download url
    my_videos_dictionary = my_videos.json()
    for vids in my_videos_dictionary['data']:
        video_title = vids['name'].strip()
        folder_name = get_folder(vids['parent_folder']).strip()
        vimeo_download_link = get_max_resolution(vids['download']).strip()
        print ("Transferring " + folder_name + "/" + video_title," from ", vimeo_download_link)
        
        # Download in chunks using requests package
        downloaded_file = "video.mp4"
        download_request = requests.get(download_link, stream = True)
        with open(downloaded_file, "wb") as download_buffer:
            for chunk in download_request.iter_content(chunk_size = 10485760): # 10MB chunk, increase or reduce for maximum throughput
                if chunk:
                    download_buffer.write(chunk)
                    print (".", end ="") # Download progress indicator

        #add library if not exists
        if not folder_name in lib_dict:
            lib_id = add_video_library(folder_name)
            lib_dict[folder_name] = lib_id

        #create video and get video ID
        lib_id = lib_dict[folder_name]
        video_id = create_video(lib_id, video_title)

        #upload_video
        if upload_video(lib_id, video_id, downloaded_file):
            os.remove(downloaded_file)
        else:
            raise Exception("Upload failed!")    
