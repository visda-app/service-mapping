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


# def extract_phrases(my_tree, phrase):
#     my_phrases = []
#     if my_tree.label() == phrase:
#         my_phrases.append(my_tree.copy(True))

#     for child in my_tree:
#         if type(child) is nltk.Tree:
#             list_of_phrases = extract_phrases(child, phrase)
#             if len(list_of_phrases) > 0:
#                 my_phrases.extend(list_of_phrases)

#     return my_phrases


def get_tokens(sentence):
    """
    small caps words
    """
    sentence = sentence.lower()
    single_words = nltk.tokenize.word_tokenize(sentence)

    # grammar = "NP: {<DT>?<JJ>*<NN>|<NNP>*}"
    # cp = nltk.RegexpParser(grammar)

    # sentenceـ = nltk.pos_tag(nltk.tokenize.word_tokenize(sentence))
    # tree = cp.parse(sentenceـ)
    # # print "\nNoun phrases:"
    # list_of_noun_phrases = extract_phrases(tree, 'NP')
    # multi_word_tokens = []

    # for phrase in list_of_noun_phrases:
    #     multi_word_tokens.append("^".join([sentence[0] for sentence in phrase.leaves()]))

    # return single_words + multi_word_tokens

    return single_words


def _get_lemmatize(word):
    lemma = nltk.wordnet.WordNetLemmatizer()
    return lemma.lemmatize(word)


def get_pruned_stem(word):
    stemmed = _get_lemmatize(word)
    res = re.sub(r'[^\w\d\s]', '', stemmed)
    return res
