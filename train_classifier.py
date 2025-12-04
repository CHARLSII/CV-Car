import pickle
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from collections import Counter


# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
with open('data.pickle', 'rb') as f:
    data_dict = pickle.load(f)

data = np.asarray(data_dict['data'])
labels = np.asarray(data_dict['labels'])

print("Dataset Loaded!")
print("Total Samples:", len(data))
print("Class Distribution:", Counter(labels))


# -------------------------------------------------
# TRAIN / TEST SPLIT
# -------------------------------------------------
x_train, x_test, y_train, y_test = train_test_split(
    data, labels,
    test_size=0.20,
    shuffle=True,
    stratify=labels
)

print("\nTraining Samples:", len(x_train))
print("Testing Samples:", len(x_test))


# -------------------------------------------------
# TRAIN MODEL
# -------------------------------------------------
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)

model.fit(x_train, y_train)

# -------------------------------------------------
# EVALUATE
# -------------------------------------------------
y_pred = model.predict(x_test)
score = accuracy_score(y_test, y_pred)

print("\nAccuracy: {:.2f}%".format(score * 100))

# -------------------------------------------------
# SAVE MODEL
# -------------------------------------------------
with open('model.p', 'wb') as f:
    pickle.dump({'model': model}, f)

print("\nModel saved as model.p")
