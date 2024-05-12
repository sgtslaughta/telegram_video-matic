from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from string import punctuation
import nltk


def _update_nltk():
    """
    Update nltk data
    :return:
    """
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)


def generate_tags(text: str):
    # Tokenize the text into words
    _update_nltk()
    words = word_tokenize(text)

    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word.lower() not in stop_words]
    words = [word for word in words if word not in punctuation]
    words = [word for word in words if len(word) > 1]

    # Here, we simply return the words as tags
    return words
