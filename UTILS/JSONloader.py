import json

def JSONloader(path):
    with open(path, 'r', encoding='utf-8') as file:
        cfg = json.load(file)
    return cfg