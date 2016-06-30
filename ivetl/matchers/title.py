import string
import nltk.corpus
import nltk.tokenize.punkt
import nltk.stem.snowball
from nltk.corpus import wordnet

stopwords = nltk.corpus.stopwords.words('english')
stopwords.extend(string.punctuation)
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


def match_titles(a, b, threshold=0.2, tlogger=None):
    pos_a = map(_get_wordnet_pos, nltk.pos_tag(tokenizer.tokenize(a)))
    pos_b = map(_get_wordnet_pos, nltk.pos_tag(tokenizer.tokenize(b)))

    lemmae_a = [lemmatizer.lemmatize(token.lower().strip(string.punctuation), pos) for token, pos in pos_a
        if pos == wordnet.NOUN and token.lower().strip(string.punctuation) not in stopwords]

    lemmae_b = [lemmatizer.lemmatize(token.lower().strip(string.punctuation), pos) for token, pos in pos_b
        if pos == wordnet.NOUN and token.lower().strip(string.punctuation) not in stopwords]

    unique_a = set(lemmae_a)

    intersection = len(unique_a.intersection(lemmae_b))
    union = len(unique_a.union(lemmae_b))

    # calculate Jaccard similarity
    if union:
        ratio = intersection / union
    else:
        ratio = 0.0

    new_denominator = len(unique_a)
    if new_denominator:
        new_ratio = intersection / new_denominator
    else:
        new_ratio = 0.0

    return ratio >= threshold, ratio, new_ratio
