import base64
import os
from time import sleep
import openai
import spotipy
from PIL import Image
from spotipy import SpotifyOAuth
from dotenv import load_dotenv
from profanity_check import predict_prob
import urllib.request
import requests

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

# get a list of playlists and print them out, then ask the user to select one
playlists = sp.current_user_playlists()
# check the size of the playlist, then detirmine the wait time to avoid rate limiting


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
    "tempo": 0
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

attributes["acousticness"] = int(attributes["acousticness"] * 100 // len(audio_features))
attributes["danceability"] = int(attributes["danceability"] * 100 // len(audio_features))
attributes["energy"] = int(attributes["energy"] * 100 // len(audio_features))
attributes["instrumentalness"] = int(attributes["instrumentalness"] * 100 // len(audio_features))
attributes["liveness"] = int(attributes["liveness"] * 100 // len(audio_features))
attributes["speechiness"] = int(attributes["speechiness"] * 100 // len(audio_features))
attributes["valence"] = int(attributes["valence"] * 100 // len(audio_features))
attributes["tempo"] = int(attributes["tempo"] // len(audio_features))

# print out the averages
print(
    f"acousticness: {attributes['acousticness']}%, danceability: {attributes['danceability']}%, energy: {attributes['energy']}%, instrumentalness: {attributes['instrumentalness']}%, liveness: {attributes['liveness']}%, speechiness: {attributes['speechiness']}%, valence: {attributes['valence']}%, tempo: {attributes['tempo']}bpm.")

# endregion

# correlate the averages to a phrase. If the average is below 25, use "low". If the average is above 25 and below 75,
# use medium. If the average is above 75, use high.
attribute_levels = {}
for key, value in attributes.items():
    if value < 25:
        attribute_levels[key] = "low"
    elif 25 < value < 75:
        attribute_levels[key] = "medium"
    else:
        attribute_levels[key] = "high"

# special check for valence, replace low with sad, medium with neutral, and high with happy
v = attribute_levels['valence']
if v == "low":
    v = "sad"
elif v == "medium":
    v = "neutral"
elif v == "high":
    v = "happy"
attribute_levels['valence'] = v

p = (f'Create an abstract image, gradient, or scenery for a playlist artwork that represents the playlist\'s '
     f'attributes through colours. Create unique gradients, scenery, objects, or color to depict the '
     f'attributes. DO NOT USE TEXT IN THE IMAGE. DO NOT '
     f'USE PEOPLE IN '
     f'THE IMAGE. The name of the playlist is {selected_playlist["name"]}, theme the playlist around that. The '
     f'playlist\'s attributes '
     f'are: acousticness: {attribute_levels["acousticness"]}, danceability: {attribute_levels["danceability"]}, '
     f'energy: {attribute_levels["energy"]}, instrumentalness: {attribute_levels["instrumentalness"]}, liveness: '
     f'{attribute_levels["liveness"]}, speechiness: {attribute_levels["speechiness"]}, mood: '
     f'{attribute_levels["valence"]}. The playlist\'s tracks are: \n'

     )
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


def generate_artwork(i):
    global response
    response = client.images.generate(
        model="dall-e-3",
        prompt=i,
        size="1024x1024",
        quality="standard",
        n=1,
    )


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
userResponse = ""
while userResponse.lower() != "exit":

    print("Done! Press enter to apply the artwork, 'exit' to exit, or 'retry' to generate a new artwork.")
    userResponse = input()
    if userResponse.lower() == "exit":
        break
    elif userResponse == "":
        print("Applying artwork...")
        # encode the image url to base64
        urllib.request.urlretrieve(image_url, "image.png")
        # convert the image to jpeg
        im = Image.open("image.png")
        rgb_im = im.convert('RGB')
        rgb_im.save('image.jpg')
        # encode the image to base64

        with open("image.jpg", "rb") as f:
            image = open("image.jpg", 'rb')
        with open("image.jpg", "rb") as f:
            encoded_image = base64.b64encode(f.read()).decode('utf-8')

        # remove the image
        os.remove("image.png")
        os.remove("image.jpg")
        sp.playlist_upload_cover_image(selected_playlist['id'], encoded_image)
        print("Done!")
        break

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
