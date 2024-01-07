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

# region: setup
load_dotenv()

SPOTIPY_CLIENT_ID = os.environ.get("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.environ.get("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.environ.get("SPOTIPY_REDIRECT_URI")

s = ["user-library-read", "playlist-read-private", "ugc-image-upload"]

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope=s))
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
    if i >= max(loopNum, len(tracks['items'])):
        break
    # check if the track's name contains bad words
    if predict_prob([track['track']['name']]) == 1:
        loopNum += 1
        continue
    song_list += track['track']['name'] + "\n"

print("using prompt:" + p + song_list)
client = openai.OpenAI()


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

        print(encoded_image)
        # remove the image
        os.remove("image.png")
        try:
            sp.playlist_upload_cover_image(selected_playlist['id'], encoded_image)
        except Exception as error:
            print(error)
            print("Something went wrong uploading the image. Try again later.")
            break
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
