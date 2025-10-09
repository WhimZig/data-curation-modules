from . import FTFYFormatter

TEST_INPUT = "The Mona Lisa doesnÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢t have eyebrows."

TEST_OUTPUT = "The Mona Lisa doesn't have eyebrows."


def test():
    f = FTFYFormatter(normalization="NFC")

    assert f.format(TEST_INPUT) == TEST_OUTPUT
