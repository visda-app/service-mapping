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