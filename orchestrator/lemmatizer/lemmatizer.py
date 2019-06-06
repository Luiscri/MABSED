import sys
sys.dont_write_bytecode = True

from cube.io_utils.conll import ConllEntry

import string

def lemmatize(tweets, lemmatizer):
    for tweet in tweets:
        words = tokenize(tweet['text'])

        lemmas = []
        tokens = []
        for idx, word in enumerate(words):
            if '@' in word or '#' in word:
                lemmas.append(word)
            if word != '':
                entry = ConllEntry(idx+1, word, "_", "_", "_", "_", 0, "_", "_", "_")
                tokens.append(entry)

        # lemmatize
        if len(tokens) != 0:
            sentences = lemmatizer([tokens])
            for entry in sentences[0]:
                if '@' in entry.lemma or '#' in entry.lemma:
                    continue
                lemmas.append(entry.lemma)
        tweet['lemmatizedText'] = ' '.join(lemmas)
    return tweets

def tokenize(text):
    # split the documents into tokens based on whitespaces
    words = text.split()
    # Nos quitamos los enalces
    words_without_links = [word for word in words if 'http' not in word]
    # Sustituimos los signos de puntuacion por espacios por si van pegadas las palabras
    t = str.maketrans("'!¡?¿.,\"()…", "           ") # Translate solo se le puede aplicar a un string
    raw_tokens = ' '.join(words_without_links).translate(t).split()
    # Strip solo quita los signos de puntuacion al principio y al final de la palabra
    # string.punctuation tiene estos caracteres: !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
    punctuation = string.punctuation.replace('@', '').replace('#', '')
    return [token.strip(punctuation).lower() for token in raw_tokens if len(token) > 1]