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

app = Flask("yt_api")

song_count = 0
mutex = Lock()

def soft_clear():
    for file in os.listdir(TMP_DIR):
        path = os.path.join(TMP_DIR, file)
        try:
            os.remove(path)
        except:
            pass

def load_audio(url: str) -> str:
    """
    Takes youtube `url` as input and returns the name of downloaded file.
    """
    yt = YouTube(url)

    ys = yt.streams.get_audio_only()

    global song_count
    filename = ""
    with mutex:
        song_count += 1
        filename = str(song_count) + ".m4a"

    ys.download(output_path=TMP_DIR, filename=filename, max_retries=5)

    path = os.path.join(TMP_DIR, filename)
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