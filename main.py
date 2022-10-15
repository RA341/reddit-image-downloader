import time
import praw
from workers.file_manager import dumpPickle, readPickle, readSubreddits, createFiles
import tkinter as tk
from tkinter import filedialog
import urllib.request
from workers.data_paths import subreddits_file, old_wallpaper_list
from workers.reddit_auth import redditAuthCheck


def getSavedWallpapers(reddit, downloaded_images):
    print("Initializing please wait....")

    subreddits = readSubreddits(subreddits_file)

    if len(subreddits) == 0:
        print("Error no subreddits detected")
        print("Add your subreddits in", subreddits_file)
        quit(-1)

    post_list = {}

    tmp = []
    saved = []
    start = time.perf_counter()
    try:
        saved = list(reddit.user.me().saved(limit=None))
        print('Successfully captured saved posts')
        print("There are ", len(saved), "saved posts")

    except Exception as e:
        print('failure to get saved posts')
        print(e)
        quit(-1)

    try:
        print("Filtering posts")
        for item in saved:
            if str(item.subreddit) in subreddits:
                if not item.is_self:
                    try:
                        if item.is_gallery:
                            for i in list(item.media_metadata):
                                tmp.append(item.media_metadata[i]['s']['u'].replace('preview', 'i').split('?')[0])
                            if not downloaded_images.get(item.id):
                                post_list[item.id] = tmp
                                print("Adding ", item.id)
                            else:
                                print("Skipping", item.id, 'already downloaded')
                            tmp = []  # resetting gallery image list
                    except Exception:
                        # Not a Gallery
                        if not downloaded_images.get(item.id):
                            post_list[item.id] = item.url
                            print("Adding ", item.id)
                        else:
                            print("Skipping", item.id, 'already downloaded')
    except Exception as e:
        print("curses", e)

    stop = time.perf_counter()

    print("time taken ", stop - start)
    print("Found", len(post_list), "new saved posts from matching subreddits")

    return post_list


def downloadWallpapers(post_list, downloaded_images):
    if len(post_list.keys()) == 0:
        print("All images are downloaded\nNothing to download\nExiting")
        quit(-1)
    success = 0
    failed = 0
    total = 0
    tmp = []
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askdirectory() + "/"
    start = time.perf_counter()
    for key in post_list.keys():
        link = post_list.get(key)
        if type(link) == list:
            for index, data in enumerate(link):
                print('downloading', key, str(index + 1) + '.png')
                total += 1
                try:
                    urllib.request.urlretrieve(data, file_path + '{}_'.format(key) + '{}.png'.format(index + 1))
                    downloaded_images.update({key: tmp})
                    success += 1
                except Exception as e:
                    failed += 1
                    print("failed to download", key, str(index + 1) + '.png')
                    print(e)
        else:
            print('downloading', key + '.png')
            total += 1
            try:
                urllib.request.urlretrieve(link, file_path + "{}.png".format(key))
                downloaded_images.update({key: link})
                success += 1
            except Exception as e:
                failed += 1
                print("failed to download", key + '.png')
                print(e)
    dumpPickle(old_wallpaper_list, downloaded_images)
    end = time.perf_counter()
    print("Finished in", end - start)
    print("Downloaded", success, 'images', 'out of', total)
    print("Failed to download", failed, 'images', 'out of', total)


if __name__ == '__main__':
    createFiles()
    try:
        token = redditAuthCheck()
    except Exception as e:
        print("Error getting token")
        print(e)
        quit(-1)

    reddit = praw.Reddit(
        client_id='63NRVVv_imYBeWE9Dwb-eg',
        client_secret=None,
        refresh_token=token,
        user_agent='A app to download wallpapers',
    )
    downloaded_images = readPickle(old_wallpaper_list)
    posts = getSavedWallpapers(reddit, downloaded_images)
    downloadWallpapers(posts, downloaded_images)
