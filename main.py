import base64
import os
from time import sleep
import openai
import scipy
import spotipy
from PIL import Image
from spotipy import SpotifyOAuth
from dotenv import load_dotenv
from profanity_check import predict_prob
import urllib.request
import numpy as np


def generate_artwork(i):
    global response
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
    try:
        generate_artwork(p + song_list)
    except openai.RateLimitError as error:
        print("Rate limited, will try again in 2 minutes.")
        sleep(120)
        generate_artwork(p + song_list)
    except openai.BadRequestError as error:
        print("Looks like something was wrong with the prompt. We'll try again with a different prompt.")
        generate_artwork(p)
    image_url = response.data[0].url
    print(image_url)


# region: setup
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
playlists = sp.current_user_playlists()

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

# get the tracks from the selected playlist, and get the average acousticness, danceability, energy,
# instrumentalness, liveness, speechiness, and valence

sleep(10)
tracks = sp.playlist_items(selected_playlist['id'])
track_ids = []
for track in tracks['items']:
    track_ids.append(track['track']['id'])

audio_features = sp.audio_features(track_ids)
attributes = {
    "acousticness": 0,
    "danceability": 0,
    "energy": 0,
    "instrumentalness": 0,
    "liveness": 0,
    "speechiness": 0,
    "valence": 0,
    "tempo": 0,
    "loudness": 0
}

for feature in audio_features:
    attributes["acousticness"] += feature["acousticness"]
    attributes["danceability"] += feature["danceability"]
    attributes["energy"] += feature["energy"]
    attributes["instrumentalness"] += feature["instrumentalness"]
    attributes["liveness"] += feature["liveness"]
    attributes["speechiness"] += feature["speechiness"]
    attributes["valence"] += feature["valence"]
    attributes["tempo"] += feature["tempo"]
    attributes["loudness"] += feature["loudness"]

attributes["acousticness"] = int(attributes["acousticness"] * 100 // len(audio_features))
attributes["danceability"] = int(attributes["danceability"] * 100 // len(audio_features))
attributes["energy"] = int(attributes["energy"] * 100 // len(audio_features))
attributes["instrumentalness"] = int(attributes["instrumentalness"] * 100 // len(audio_features))
attributes["liveness"] = int(attributes["liveness"] * 100 // len(audio_features))
attributes["speechiness"] = int(attributes["speechiness"] * 100 // len(audio_features))
attributes["valence"] = int(attributes["valence"] * 100 // len(audio_features))
attributes["tempo"] = int(attributes["tempo"] // len(audio_features))
attributes["loudness"] = int(attributes["loudness"] // len(audio_features))

# print out the averages
print(
    f"acousticness: {attributes['acousticness']}%, danceability: {attributes['danceability']}%, energy: {attributes['energy']}%, instrumentalness: {attributes['instrumentalness']}%, liveness: {attributes['liveness']}%, speechiness: {attributes['speechiness']}%, valence: {attributes['valence']}%, tempo: {attributes['tempo']}bpm, loudness: {attributes['loudness']}db.")

# correlate the averages to a phrase. If the average is below 25, use "low". If the average is above 25 and below 75,
# use medium. If the average is above 75, use high.
levels = {}
for key, value in attributes.items():
    if value < 0:
        # it's loudness, so we want to use negative numbers
        if value > -2:
            levels[key] = "high"
        elif -2 > value > -6:
            levels[key] = "medium"
        else:
            levels[key] = "low"

    if value < 35:
        levels[key] = "low"
    elif 35 < value < 60:
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
if levels['valence'] == "sad":
    music_describers.append("The artwork should be a dark forms for colors, like dark green, dark purple, dark blue, "
                            "etc.")
elif levels['valence'] == "happy" or levels['danceability'] == "high":
    music_describers.append("The artwork should be a bright, vibrant colors, like yellow, orange or red")
elif levels['acousticness'] == "high":
    music_describers.append("The artwork should be in orange sunset colors, like orange, yellow.")
elif levels['energy'] == "low":
    music_describers.append("The artwork should be in cool colors, like blue or green.")
elif levels['energy'] == "high":
    music_describers.append("The artwork should be in warm colors, like red or orange.")
elif levels['speechiness'] == "high":
    music_describers.append("The artwork should be beige, off white, light grey or brown colors.")
else:
    # try grabbing the colors from 4 songs in the playlist using the track id
    img_urls = []
    for i, track in enumerate(tracks['items']):
        if i >= 4:
            break
        img_urls.append(sp.track(track['track']['id'])['album']['images'][0])
    imgs = []
    colors = []
    for url in img_urls:
        urllib.request.urlretrieve(url['url'], "image.png")
        imgs.append(Image.open("image.png"))
        os.remove("image.png")
    # get the average color of each image and store it in colors.
    for img in imgs:
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
    # convert the colors to hex
    for i, color in enumerate(colors):
        colors[i] = '#%02x%02x%02x' % (color[0], color[1], color[2])

    music_describers.append(f"The artwork should be in the colors {colors[0]}, {colors[1]}, {colors[2]}, and "
                            f"{colors[3]}")
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
    music_describers.append("The artwork should be a smooth texture, like a gradient")
elif (
        (levels['energy'] == "high" and levels['loudness'] != "low")
        or
        (levels['valence'] == "happy" and levels['loudness'] != "low")
        or
        (levels['acousticness'] == "low" and levels['loudness'] != "low")
):
    music_describers.append("The artwork should be a roughly textured with noise")
# endregion
# region: objects
if (
        (levels['valence'] == "happy" and levels['energy'] != "low")
        or
        (levels['energy'] == "high" and levels['loudness'] != "low")
        or
        (levels['acousticness'] == "low" and levels['loudness'] != "low")
):
    music_describers.append("The artwork should be an abstract scene, such as a sunset.")
elif (
        (levels['valence'] == "sad" and levels['energy'] != "high")
        or
        (levels['energy'] == "low" and levels['loudness'] != "high")
        or
        (levels['acousticness'] == "high" and levels['loudness'] != "high")
):
    music_describers.append("The artwork should be a realistic object in the outdoors, such as a moon or a flower.")
    # neutral scene
elif (levels['energy'] == "medium" and levels['loudness'] == "medium" and levels['acousticness'] == "medium"
      and levels['valence'] == "neutral"):
    music_describers.append("The artwork should be a simple shape, such as a circle or a square. Include only one "
                            "shape, and use only two colors.")

# endregion


p = f'I am going to describe the artwork for a playlist called "{selected_playlist["name"]}". The playlist is '

for value in music_describers:
    p += value + " "

p += "Here are some songs from the playlist:\n"

song_list = ""

loopNum = 5
for i, track in enumerate(tracks['items']):
    if i >= min(loopNum, len(tracks['items'])):
        break
    # check if the track's name contains bad words
    if predict_prob([track['track']['name']]) == 1:
        loopNum += 1
        continue
    song_list += track['track']['name'] + "\n"

print("using prompt:" + p + song_list)
client = openai.OpenAI()

response = None

generate_image()
userResponse = ""
while userResponse.lower() != "exit":

    print("Done! Press enter to apply the artwork, 'exit' to exit, or 'retry' to generate a new artwork.")
    userResponse = input()
    if userResponse.lower() == "exit":
        break
    elif userResponse == "":

        print("Applying artwork...")
        # formats the image url to be in base64 as a jpg
        urllib.request.urlretrieve(image_url, "image.png")
        im = Image.open("image.png")
        rgb_im = im.convert('RGB')
        rgb_im.save('image.jpg')
        with open("image.jpg", "rb") as f:
            image = open("image.jpg", 'rb')
        with open("image.jpg", "rb") as f:
            encoded_image = base64.b64encode(f.read()).decode('utf-8')

        os.remove("image.png")
        os.remove("image.jpg")

        sp.playlist_upload_cover_image(selected_playlist['id'], encoded_image)
        print("Done!")
        break

    generate_image()
