import nltk


def post_install():
    nltk.download("punkt")
    nltk.download("punkt_tab")
    nltk.download("stopwords")


def __main__():
    post_install()
