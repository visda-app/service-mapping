from lib import nlp


def test_get_tokens():
    test_vectors = [
        {
            'sentence': 'Some',
            'tokenized': ['some']
        },
        {
            'sentence': "This is St. Patric's Day.",
            'tokenized': ['this', 'is', 'st.', 'patric', "'s", 'day', '.'],
        },
        {
            'sentence': 'Wait! what?',
            'tokenized': ['wait', '!', 'what', '?']
        },
        {
            'sentence': 'Blueberries are an important part of my breakfasts.',
            'tokenized': ['blueberries', 'are', 'an', 'important', 'part', 'of', 'my', 'breakfasts', '.']
        },
        {
            'sentence': "یک جمله فارسی!",
            'tokenized': ['یک', 'جمله', 'فارسی', '!']
        },
    ]

    for t in test_vectors:

        actual_result = nlp.get_tokens(t['sentence'])
        assert t['tokenized'] == actual_result


def test_get_senteces():
    test_vectors = [
        {
            'raw_text': '''Caution: when tokenizing a Unicode string, make sure you are not using an encoded version of the string (it may be necessary to decode it first, e.g. with s.decode("utf8").

NLTK tokenizers can produce token-spans, represented as tuples of integers having the same semantics as string slices, to support efficient comparison of tokenizers. (These methods are implemented as generators.)''',
            'sentences': [
                'Caution: when tokenizing a Unicode string, make sure you are not using an encoded version of the string (it may be necessary to decode it first, e.g.',
                'with s.decode("utf8").',
                'NLTK tokenizers can produce token-spans, represented as tuples of integers having the same semantics as string slices, to support efficient comparison of tokenizers.',
                '(These methods are implemented as generators.)',
            ],
        },
    ]

    for t in test_vectors:
        actual_results = nlp.get_sentences(t['raw_text'])
        assert actual_results == t['sentences']
