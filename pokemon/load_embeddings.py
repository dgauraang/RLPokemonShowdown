import csv
import os.path
import numpy as np


def load_embeddings():

    path_root = os.path.abspath(os.path.dirname(__file__))
    move_path = os.path.join(path_root, 'movembeddings.csv')
    poke_path = os.path.join(path_root, 'pokembeddings.csv')
    move_embeddings = {}
    with open(move_path, 'r', newline='') as csv_file:
        reader = csv.reader(csv_file, delimiter=',', quotechar='"')
        for row in reader:
            name = row[0]
            name = name.replace(' ', '')
            name = name.lower()
            vec = row[1:]
            """
            if name == 'watergun':
                name = 'water gun'
                print(name)"""
            move_embeddings[name] = np.array(vec)

    poke_embeddings = {}
    with open(poke_path, 'r', newline='') as csv_file:
        reader = csv.reader(csv_file, delimiter=',', quotechar='"')
        for row in reader:
            name = row[0]
            vec = row[1:]
            poke_embeddings[name] = np.array(vec)
    move_embeddings['recharge'] = np.zeros((10))
    return move_embeddings, poke_embeddings
