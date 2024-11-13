# -*- coding: utf-8 -*-
"""text_classification.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1NpW4Yd-1-eFTBhV_cNtvBhwiwC_UTG41
"""

import os
import re
import shutil
import string

import matplotlib.pyplot as plt
from tensorflow.keras import layers, losses

import tensorflow as tf

URL = "https://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz"
dataset = tf.keras.utils.get_file(
    "aclImdb_v1", URL, untar=True, cache_dir=".", cache_subdir="")
dataset_dir = os.path.join(os.path.dirname(dataset), "aclImdb")

train_dir = os.path.join(dataset_dir, "train")

sample_file = os.path.join(train_dir, "pos/1181_9.txt")
with open(sample_file, encoding="utf-8") as file:
    print(file.read())

remove_dir = os.path.join(train_dir, "unsup")
shutil.rmtree(remove_dir)

BATCH_SIZE = 32
SEED = 42
raw_train_ds = tf.keras.utils.text_dataset_from_directory(
    "aclImdb/train",
    batch_size=BATCH_SIZE,
    validation_split=0.2,
    subset="training",
    seed=SEED)

for text_batch, label_batch in raw_train_ds.take(1):
    for i in range(3):
        print("Review : ", text_batch.numpy()[i])
        print("Label : ", label_batch.numpy()[i])
print("Label[0] corresponds to : ", raw_train_ds.class_names[0])
print("Label[1] corresponds to : ", raw_train_ds.class_names[1])

raw_val_ds = tf.keras.utils.text_dataset_from_directory(
    "aclImdb/train",
    batch_size=BATCH_SIZE,
    validation_split=0.2,
    subset="validation",
    seed=SEED)
raw_test_ds = tf.keras.utils.text_dataset_from_directory(
    "aclImdb/test", batch_size=BATCH_SIZE)


def custom_standardization(input_data):
    """Reform text.

    Args:
        input_data (<class 'tensorflow.python.framework.ops.EagerTensor'>): user review.

    Returns:
        (<class 'tensorflow.python.framework.ops.EagerTensor'>): reformatted text.
    """
    lowercase = tf.strings.lower(input_data)
    stripped_html = tf.strings.regex_replace(lowercase, "<br />", " ")
    return tf.strings.regex_replace(stripped_html, f"{[re.escape(string.punctuation)]}", "")


MAX_FEATURES = 10000
SEQUENCE_LENGTH = 250

vectorize_layer = layers.TextVectorization(
    standardize=custom_standardization,
    max_tokens=MAX_FEATURES,
    output_mode="int",
    output_sequence_length=SEQUENCE_LENGTH)

train_text = raw_train_ds.map(lambda x, y: x)
vectorize_layer.adapt(train_text)


def vectorize_text(text, label):
    """Text to vectorized text.

    Args:
        text (<class 'tensorflow.python.framework.ops.EagerTensor'>): reformatted user review.
        label (<class 'tensorflow.python.framework.ops.EagerTensor'>): 
        tf.Tensor(0, shape=(), dtype=int32)

    Returns:
        (<class 'tensorflow.python.framework.ops.SymbolicTensor'>): vectorized text and label.
    """
    text = tf.expand_dims(text, axis=-1)
    return vectorize_layer(text), label


text_batch, label_batch = next(iter(raw_train_ds))
first_review, first_label = text_batch[0], label_batch[0]
print("Review : ", first_review)
print("Label : ", raw_train_ds.class_names[first_label])
print("Vectorized review : ", vectorize_text(first_review, first_label))
print("1287 : ", vectorize_layer.get_vocabulary()[1287])
print("313 : ", vectorize_layer.get_vocabulary()[313])
print(f"Vocabulary size : {len(vectorize_layer.get_vocabulary())}")

train_ds = raw_train_ds.map(vectorize_text)
val_ds = raw_val_ds.map(vectorize_text)
test_ds = raw_test_ds.map(vectorize_text)

AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)
test_ds = test_ds.cache().prefetch(buffer_size=AUTOTUNE)

EMBEDDING_DIM = 16
model = tf.keras.Sequential([
    layers.Embedding(MAX_FEATURES, EMBEDDING_DIM),
    layers.Dropout(0.2),
    layers.GlobalAveragePooling1D(),
    layers.Dropout(0.2),
    layers.Dense(1, activation="sigmoid")
])
model.summary()
model.compile(loss=losses.BinaryCrossentropy(),
              optimizer="adam",
              metrics=[tf.metrics.BinaryAccuracy(threshold=0.5)]
              )

EPOCHS = 10
history = model.fit(train_ds, validation_data=val_ds, epochs=EPOCHS)

loss, accuracy = model.evaluate(test_ds)
print("Loss : ", loss)
print("Accuracy : ", accuracy)

history_dict = history.history
history_dict.keys()

acc = history_dict['binary_accuracy']
val_acc = history_dict['val_binary_accuracy']
loss = history_dict['loss']
val_loss = history_dict['val_loss']

EPOCHS = range(1, len(acc) + 1)
plt.plot(EPOCHS, loss, label="Training loss")
plt.plot(EPOCHS, val_loss, label="Validation loss")
plt.title("Training and validation loss")
plt.xlabel("Epochs")
plt.ylabel("Loss")
plt.legend()
plt.show()

plt.plot(EPOCHS, acc, label="Training accuracy")
plt.plot(EPOCHS, val_acc, label="Validation accuracy")
plt.title("Training and validation accuracy")
plt.xlabel("Epochs")
plt.ylabel("Accuracy")
plt.legend()
plt.show()

export_model = tf.keras.Sequential([
    vectorize_layer,
    model,
    layers.Activation("sigmoid")
])
export_model.compile(
    loss=losses.BinaryCrossentropy(from_logits=False),
    optimizer="adam",
    metrics=["accuracy"]
)

metrics = export_model.evaluate(raw_test_ds, return_dict=True)
print(metrics)

examples = tf.constant(
    ["The movie was great!", "The movie was okay.", "The movie was terrible..."])
export_model.predict(examples)