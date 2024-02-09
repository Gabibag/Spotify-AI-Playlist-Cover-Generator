import base64
import os
import random
import time
from time import sleep
from openai import OpenAI
import scipy
import spotipy
from PIL import Image
from spotipy import SpotifyOAuth
from dotenv import load_dotenv
import urllib.request
import numpy as np
import requests as rq
import os
import numpy as np
from PIL import Image


def generate_artwork(i):
    global response
    client = OpenAI()
    response = client.images.generate(
        model="dall-e-3",
        prompt=i,
        size="1024x1024",
        quality="standard",
        n=1,
    )




def generate_image():
    global error, image_url
    print("Generating artwork...")

    generate_artwork(p)
    
    image_url = response.data[0].url
    # send the url to a url shortener
    u = rq.post("https://cleanuri.com/api/v1/shorten", data={"url": image_url}).json()["result_url"]
    os.system('clear')
    print(u)
    return image_url


def remove_all(word, text):
    # remove all instances of word regardless of case in a text, which is a string
    text = text.lower()
    word = word.lower()
    text = text.replace(" " + word + " ", " ")
    return text


# region: setup
os.system('clear')
# now we check if the user has a .env file, if they don't, we create one and ask them to fill it out
if not os.path.isfile(".env"):
    print("No .env file found. Seems like you're a first time user. Creating one now.")
    f = open(".env", "w+")
    print(".env file created. In order to use this program, you need to fill out the .env file with your Spotify API ")
    print("credentials. You can get them from https://developer.spotify.com/dashboard/applications. Press create app,")
    print("then fill out the form. Check the  Use http://127.0.0.1:3000/ as the redirect url. Everything else doesn't "
          "matter.")
    print("Once you've created the app, you can find your client id and client secret by clicking on the app and ")
    print("hitting settings. Paste your CLIENT ID below.")
    f.write("SPOTIPY_CLIENT_ID=" + input("CLIENT ID: ") + "\n")
    print("Now paste your CLIENT SECRET below.")
    f.write("SPOTIPY_CLIENT_SECRET=" + input("CLIENT SECRET: ") + "\n")
    f.write("SPOTIPY_REDIRECT_URI=http://localhost:3000/\n")
    print("Now we need an openai api key. You can get one from https://beta.openai.com/account/api-keys. Create an "
          "account if you don't have one, then paste your api key below.")
    f.write("OPENAI_API_KEY=" + input("API KEY: ") + "\n")
    f.close()
    print("Created .env file.")
    exit(0)

load_dotenv()
SPOTIPY_CLIENT_ID = os.environ.get("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.environ.get("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.environ.get("SPOTIPY_REDIRECT_URI")

s = ["user-library-read", "playlist-read-private", "ugc-image-upload", "playlist-modify-public", "playlist-modify"
                                                                                                 "-private"]

try:
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                                   client_secret=SPOTIPY_CLIENT_SECRET,
                                                   redirect_uri=SPOTIPY_REDIRECT_URI,
                                                   scope=s))
except spotipy.oauth2 as e:
    print("Looks like your .env file is invalid. Resetting it now.")
    os.remove(".env")
    print("Here is the error if you need it:" + e)
    exit(0)

user = sp.me()
# endregion

# region: get data
# get a list of playlists and print them out, then ask the user to select one
print("Getting playlists...")
playlists = sp.current_user_playlists()
os.system('clear')
for i, playlist in enumerate(playlists['items']):
    if playlist['owner']['id'] != user['id']:
        continue
    print(f"{i}: {playlist['name']}")

print("Not seeing a playlist? Make sure it's yours and doesn't contain a + in the name.")
selection = input("Select a playlist: ")
while selection.isdigit() == False or int(selection) >= len(playlists['items']):
    print("Invalid selection. Use the number next to the playlist.")
    selection = input("Select a playlist: ")
selection = int(selection)
selected_playlist = playlists['items'][selection]
# clear the console
os.system('clear')
print(f"Selected playlist: {selected_playlist['name']}")
print("Getting playlist data...")
# get the tracks from the selected playlist, and get the average acousticness, danceability, energy,
# instrumentalness, liveness, speechiness, and valence

tracks = sp.playlist_items(selected_playlist['id'])
track_ids = []
for track in tracks['items']:
    track_ids.append(track['track']['id'])

audio_features = sp.audio_features(track_ids)
attributes = {
    "acousticness": [],
    "danceability": [],
    "energy": [],
    "instrumentalness": [],
    "liveness": [],
    "speechiness": [],
    "valence": [],
    "tempo": [],
    "loudness": [],
    "year": []
}

for feature in audio_features:
    attributes["acousticness"].append(feature["acousticness"])
    attributes["danceability"].append(feature["danceability"])
    attributes["energy"].append(feature["energy"])
    attributes["instrumentalness"].append(feature["instrumentalness"])
    attributes["liveness"].append(feature["liveness"])
    attributes["speechiness"].append(feature["speechiness"])
    attributes["valence"].append(feature["valence"])
    attributes["tempo"].append(feature["tempo"])
    attributes["loudness"].append(feature["loudness"])

for track in tracks['items']:
    attributes["year"].append(int(track['track']['album']['release_date'][:4]))
# find median of each attribute
for key, value in attributes.items():
    multi = 100
    if key == "loudness" or key == "tempo" or key == "year":
        multi = 1

    attributes[key] = int(np.median(value) * multi)

# correlate the averages to a phrase. If the average is below 25, use "low". If the average is above 25 and below 75,
# use medium. If the average is above 75, use high.
levels = {}
for key, value in attributes.items():
    if key == "loudness":
        if value > -4:
            levels[key] = "high"
        elif -4 > value > -8:
            levels[key] = "medium"
        else:
            levels[key] = "low"
        continue
    elif key == "year":
        if value > 2020:
            levels[key] = "new"
        elif 2020 < value < 2010:
            levels[key] = "medium"
        else:
            levels[key] = "old"
        continue

    if value < 30:
        levels[key] = "low"
    elif 35 < value < 70:
        levels[key] = "medium"
    else:
        levels[key] = "high"

# special check for valence, replace low with sad, medium with neutral, and high with happy
v = levels['valence']
if v == "low":
    v = "sad"
elif v == "medium":
    v = "neutral"
elif v == "high":
    v = "happy"
levels['valence'] = v
# endregion

# region: generate artwork
music_describers = []

# region: colors
# try grabbing the colors from 4 songs in the playlist using the track id
img_urls = []
num = 8
for i, track in enumerate(tracks['items']):
    if i >= num:
        break
    # check if url appears in img_urls
    if sp.track(track['track']['id'])['album']['images'][0] in img_urls:
        num += 1
        continue
    img_urls.append(sp.track(track['track']['id'])['album']['images'][0])
imgs = []
colors = []
for url in img_urls:
    urllib.request.urlretrieve(url['url'], "image.png")
    imgs.append(Image.open("image.png"))
    os.remove("image.png")

# get the average color of each image and store it in colors.
for img in imgs:
    try:
        # dominant color in the image
        ar = np.asarray(img)
        shape = ar.shape
        ar = ar.reshape(np.product(shape[:2]), shape[2]).astype(float)
        codes, dist = scipy.cluster.vq.kmeans(ar, 5)
        vecs, dist = scipy.cluster.vq.vq(ar, codes)
        counts, bins = np.histogram(vecs, len(codes))
        index_max = np.argmax(counts)
        peak = codes[index_max]
        peak = peak.astype(int)
        colors.append(peak)
    except:
        print("Error getting color from image")
        continue

# convert the colors to hex
for i, color in enumerate(colors):
    colors[i] = '#%02x%02x%02x' % (color[0], color[1], color[2])

s = "The artwork should be only in the color " if len(colors) == 1 else "The artwork should be in the colors "
for i, color in enumerate(colors):
    if i == len(colors) - 1 and len(colors) > 1:
        s += "and " + color
    else:
        s += color + ", "
s = s[:-2] + "."
music_describers.append(s)
# endregion
# region: texture
if (
        (levels['valence'] != "happy" and levels['energy'] == "low" and levels["loudness"] != "high")
        or
        (levels['energy'] == "low" and levels['loudness'] == "low")
        or
        (levels['acousticness'] == "high" and levels['loudness'] == "medium")
        or
        (levels['speechiness'] == "low" and levels['loudness'] == "low")
):
    music_describers.append("The artwork should be a smooth texture, like a gradient, or glass, or the texture of wet, hard candy")
elif (
        (levels['energy'] == "high" and levels['loudness'] != "low")
        or
        (levels['valence'] == "happy" and levels['loudness'] != "low")
        or
        (levels['acousticness'] == "low" and levels['loudness'] != "low")
):
    music_describers.append("The artwork should have noise like slightly wrinkled paper or white noise overlayed")
elif (
        (levels['energy'] == "low" and levels['loudness'] != "high")
        or
        (levels['valence'] == "sad" and levels['loudness'] != "high")
        or
        (levels['acousticness'] == "high" and levels['loudness'] != "high")
):
    music_describers.append("The artwork should be like a watercolor painting in a traditional art style")
# endregion
# region: objects
if (
        (levels['valence'] == "happy" and levels['energy'] != "low")
        or
        (levels['energy'] == "high" and levels['loudness'] != "low")
        or
        (levels['acousticness'] == "low" and levels['loudness'] != "low")
):
    music_describers.append("The artwork should be realistic with a focus on a single random object.")
elif (
        (levels['valence'] == "sad" and levels['energy'] != "high")
        or
        (levels['energy'] == "low" and levels['loudness'] != "high")
        or
        (levels['acousticness'] == "high" and levels['loudness'] != "high")
):
    music_describers.append("The artwork should be a realistic, wide angle scenery of anything")
    # neutral scene
elif (levels['energy'] == "medium" and levels['loudness'] == "medium" and levels['acousticness'] == "medium"
      and levels['valence'] == "neutral"):
    music_describers.append("The artwork should be a simple shape, such as a circle, square, triangle, diamond, "
                            "or a hexagon. Include only one shape, and use only two colors. Be minimalistic.")

# endregion
# region: extras

if levels['valence'] == "sad" and levels['danceability'] == "low":
    music_describers.append("The artwork's colors should be darker")
if levels['valence'] == "sad" and levels['danceability'] == "high":
    music_describers.append("The artwork should be have chroma abberations.")
elif levels['valence'] == "happy" or levels['danceability'] == "high":
    music_describers.append("The artwork should have a lense flare.")
elif levels['energy'] == "low":
    music_describers.append("The artwork should be slightly fuzzy.")
elif levels['energy'] == "high":
    music_describers.append("The artwork should have a fracture through it.")


# endregion

# replace all instances of the word regardless of case


p = (f'I am going to describe the artwork for a playlist called "{selected_playlist["name"]}". DO NOT INCLUDE '
     f'PEOPLE IN THE ARTWORK. Make sure the name of the playlist are in the image. The borders of the artwork should be one solid color. The playlist should represent'
     f'an art style from the time of "{attributes["year"]}". ')

for value in music_describers:
    p += value + " "

os.system('clear')
print(
    f"acousticness: {attributes['acousticness']}%, danceability: {attributes['danceability']}%, energy: {attributes['energy']}%, instrumentalness: {attributes['instrumentalness']}%, liveness: {attributes['liveness']}%, speechiness: {attributes['speechiness']}%, valence: {attributes['valence']}%, tempo: {attributes['tempo']}bpm, loudness: {attributes['loudness']}db, year: {attributes['year']}")
print("Selected playlist: " + selected_playlist['name'] + "\n")

print("\n\n\n Here's the prompt we're sending to OpenAI: " + p)


response = None

image_url = generate_image()
userResponse = ""

while userResponse.lower() != "exit":

    print("Done! Press enter to apply the artwork, 'exit' to exit, or 'retry' to generate a new artwork.")
    userResponse = input()

    if userResponse.lower() == "exit":
        break
    elif userResponse == "":
        os.system('clear')
        print("Applying artwork...")
        # formats the image url to be in base64 as a jpg
        urllib.request.urlretrieve(image_url, "image.png")
        # now compress the png
        
        
        
        im = Image.open("image.png")
        rgb_im = im.convert('RGB')
        rgb_im.save('image.jpeg', optimize=True, quality=75)
        sleep(1)
        encoded_image = ""
        with open("image.jpeg", "rb") as f:
            encoded_image = base64.b64encode(f.read()).decode('utf-8')
        
        
        sp.playlist_upload_cover_image(selected_playlist['id'], encoded_image)
        
        os.remove("image.jpeg")
        os.remove("image.png")
        os.system('clear')
        print("Done!")
        break
    os.system('clear')
    image_url = generate_image()
