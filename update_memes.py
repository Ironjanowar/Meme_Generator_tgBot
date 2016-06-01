import requests
import json


def update_memes():
    # Update the meme file
    r = requests.get("https://api.imgflip.com/get_memes")
    request_json = r.json()
    with open('./data/request.json', 'w') as json_file:
        json.dump(request_json, json_file)

update_memes()
