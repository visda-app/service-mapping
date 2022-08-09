"""
A module to get the words and multi-word words from the sentence.

Tired this for multi word, but didn't work.
https://datascience.stackexchange.com/questions/17294/nlp-what-are-some-popular-packages-for-multi-word-tokenization
"""

import re
import os
import nltk

from lib.logger import logger


logger.info("Downloading NLP models...")
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
nltk.download('omw-1.4')
logger.info("Downloading NLP models Done!")


def get_tokens(sentence):
    """
    small caps words
    """
    sentence = sentence.lower()
    single_words = nltk.tokenize.word_tokenize(sentence)
    return single_words


def get_sentences(text):
    sentences = nltk.tokenize.sent_tokenize(text)
    return sentences


def _get_lemmatize(word):
    lemma = nltk.wordnet.WordNetLemmatizer()
    return lemma.lemmatize(word)


def get_pruned_stem(word):
    stemmed = _get_lemmatize(word)
    res = re.sub(r'[^\w\d\s]', '', stemmed)
    return res

