import nltk


def post_install():
    nltk.download("punkt"),
    nltk.download("punkt_tab")


def __main__():
    post_install()
