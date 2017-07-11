import string
import nltk.corpus
import nltk.tokenize.punkt
import nltk.stem.snowball
from nltk.corpus import wordnet

stopwords = list(string.punctuation)
stopwords.append('')
tokenizer = nltk.tokenize.WordPunctTokenizer()
lemmatizer = nltk.stem.wordnet.WordNetLemmatizer()


def _get_wordnet_pos(pos_tag):
    if pos_tag[1].startswith('J'):
        return pos_tag[0], wordnet.ADJ
    elif pos_tag[1].startswith('V'):
        return pos_tag[0], wordnet.VERB
    elif pos_tag[1].startswith('N'):
        return pos_tag[0], wordnet.NOUN
    elif pos_tag[1].startswith('R'):
        return pos_tag[0], wordnet.ADV
    else:
        return pos_tag[0], wordnet.NOUN


def simplify_value(raw_value):
    pos_a = map(_get_wordnet_pos, nltk.pos_tag(tokenizer.tokenize(raw_value)))
    lemmae_a = [lemmatizer.lemmatize(token.lower().strip(string.punctuation), pos) for token, pos in pos_a
                if token.lower().strip(string.punctuation) not in stopwords]
    return ' '.join(lemmae_a)


def match_simplified_values(a, b, threshold=0.8, tlogger=None):
    lemmae_a = a.split()
    lemmae_b = b.split()

    unique_a = set(lemmae_a)

    intersection = len(unique_a.intersection(lemmae_b))
    union = len(unique_a.union(lemmae_b))

    # calculate Jaccard similarity
    if union:
        ratio = intersection / union
    else:
        ratio = 0.0

    return ratio >= threshold, ratio
