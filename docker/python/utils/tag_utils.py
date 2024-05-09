from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from string import punctuation
import nltk


def _update_nltk():
    """
    Update nltk data
    :return:
    """
    nltk.download('stopwords')
    nltk.download('punkt')


def generate_tags(text: str):
    # Tokenize the text into words
    words = word_tokenize(text)

    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word.lower() not in stop_words]
    words = [word for word in words if word not in punctuation]

    # Here, we simply return the words as tags
    return words
