# Spotify-AI-Playlist-Generator

## Description
This is a python script that creates a playlist cover image based on the tone of your playlist.
\
\
IMPORTANT: This script requires a spotify developer account, which is free and easy to make. You can get one
[here](https://developer.spotify.com/dashboard/login). It also requires an OpenAI API key, which you can get at 
[here](https://platform.openai.com/api-keys). To be able to use Dalle-3, you need to add at least 5$ as credits to your
account. Each image costs about 0.04$ to generate, so 5$ should be enough for about 125 images. 


## How do I use this thing?
### Mac
1. Download the repo by clicking the green button in the top right corner that says "Code," then click "Download ZIP"
2. Unzip the file, 
3. Hit command + spacebar to open spotlight search, type in "terminal" and hit enter
4. Type in `cd ` (with a space after) and drag the folder you just unzipped into the terminal window, then hit enter
5. Type in `pip install -r requirements.txt` and hit enter
6. Type in `python3 main.py` and hit enter
7. Follow the prompts in the terminal window

### Windows
1. Download the repo by clicking the green button in the top right corner that says "Code," then click "Download ZIP"
2. Unzip the file,
3. Open the folder you just unzipped, then click on the file called "main.py"
4. Install the required packages by opening the command prompt and typing in `pip install -r requirements.txt` and hitting enter
5. If you have python installed, it should open a terminal window and start running the script. If you don't have python installed, you can download it [here](https://www.python.org/downloads/)
6. Follow the prompts in the terminal window

### Linux
It's a basic python script.

## How does it work?
This script uses the spotify API to get the audio features of each song in your playlist. Then it tries to understand 
the theme of the playlist by looking at the average of each audio feature. Then it uses OpenAI's DALL-E 3 to generate 
a cover image based on the theme of the playlist.
