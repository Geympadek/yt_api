TMP_DIR = "temp"

import flask
from flask import Flask, request
import mutagen.easymp4
import mutagen.m4a
import mutagen.mp4
from pytubefix import YouTube, Search
import os
from threading import Lock
import mutagen
from time import time

app = Flask("yt_api")

song_count = 0
mutex = Lock()

def soft_clear():
    """
    Cleares the temp directory, ignoring errors
    """
    for file in os.listdir(TMP_DIR):
        path = os.path.join(TMP_DIR, file)
        try:
            os.remove(path)
        except:
            pass

def load_audio(url: str, max_retries=3, timeout = 7.5) -> str:
    """
    Takes youtube `url` as input and returns the name of downloaded file.
    """
    global song_count
    filename = ""
    with mutex:
        song_count += 1
    filename = str(song_count) + ".m4a"
        
    path = os.path.join(TMP_DIR, filename)
    
    attempt = 0
    while True:
        yt = YouTube(url)
        ys = yt.streams.get_audio_only()

        start_time = time()
        interrupted = False

        try:
            ys.download(output_path=TMP_DIR, filename=filename, timeout=timeout)
        except Exception:
            interrupted = True
            print("Error raised")

        if interrupted:
            attempt += 1
            if attempt >= max_retries:
                raise Exception("Exceeded number of retries.")
            print(f"Starting {attempt} retry.")
            continue

        if not os.path.exists(path):
            raise Exception("Unable to fetch the song from yt")
        break

    audio: mutagen.easymp4.EasyMP4 = mutagen.File(path, easy=True)
    
    if audio is not None:
        # Set the title and artist/author
        audio['title'] = yt.title  # or use a custom title
        audio['artist'] = yt.author  # or use a custom artist
        audio.save()

    return filename

@app.route("/download", methods=['GET'])
def download():
    args = request.args.to_dict()
    if 'url' not in args:
        return flask.abort(400)
    
    url = args['url']

    soft_clear()
    filename = load_audio(url)

    result = flask.send_file(os.path.join(TMP_DIR, filename), mimetype="audio/mpeg")
    return result

def search(query: str, limit: int = 8) -> list[dict]:
    raw_results = Search(query)
    videos = raw_results.videos

    results = []
    for video in videos[:limit]:
        results.append({
            "author": video.author,
            "title": video.title,
            "url": video.watch_url
        })
    return results

@app.route("/search", methods=["GET"])
def search_route():
    args = request.args.to_dict()
    if 'query' not in args:
        return flask.abort(400)
    
    query = args["query"]
    return search(query)

def main():
    os.makedirs(TMP_DIR, exist_ok=True)
    
    app.run("0.0.0.0", port=5000)

from timeit import timeit

if __name__ == "__main__":
    main()