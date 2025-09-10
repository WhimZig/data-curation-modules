from gptnl_punctuation_formatter import PunctuationFormatter


def test():
    f = PunctuationFormatter()

    assert (
        f.format(
            "，"
            "。"
            "、"
            "„"
            "”"
            "“"
            "«"
            "»"
            "１"
            "」"
            "「"
            "《"
            "》"
            "´"
            "∶"
            "："
            "？"
            "！"
            "（"
            "）"
            "；"
            "–"
            "—"
            "．"
            "～"
            "’"
            "…"
            "━"
            "〈"
            "〉"
            "【"
            "】"
            "％"
            "►"
        )
        == ',.,""""""""""\'::?!();- - . ~\'...-<>[]%-'
    )

    assert (
        f.format(
            """Maar waarom kregen we nu kwart voor tien niet nog een 【korte】 film na? Het forum 《Persoonlijk》 was na al die spanning toch wel erg saai. Dan was Ncrv's nieuwe "Popparlement" voor achten heel wat fleuriger, een goede synthese tussen een forum en een amusementsprogramma met de ingelaste interviews en de optredende artiesten als afwisseling."""
        )
        == """Maar waarom kregen we nu kwart voor tien niet nog een [korte] film na? Het forum "Persoonlijk" was na al die spanning toch wel erg saai. Dan was Ncrv's nieuwe "Popparlement" voor achten heel wat fleuriger, een goede synthese tussen een forum en een amusementsprogramma met de ingelaste interviews en de optredende artiesten als afwisseling."""
    )
