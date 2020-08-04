import json
import numpy as np
from sklearn.manifold import TSNE


FILE_NAME = "etc/output.json"

with open(FILE_NAME, 'r') as f:
    lines = f.readlines()

in_array = []
for line in lines:
    vect = json.loads(line).get('embedding')
    in_array. append(vect)

X = np.array(in_array)
X_embedded = TSNE(n_components=2).fit_transform(X)
X_embedded.shape