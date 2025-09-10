from gptnl_pii_mappers import PII_Everything

if __name__ == "__main__":
    input_text = """Helga Maria Jansen en Carla Li zaten samen in een klein theater in Rotterdam, waar een voorstelling van hun oude vriend, acteur Jan Vermeer, op het punt stond te beginnen. Helga M. Jansen, die altijd van theater had gehouden, was bijzonder enthousiast. Naast hen zaten nog wat oude bekenden uit hun studietijd: Mark Peters, een kunstcriticus met wie mevrouw M.J. Jansen vroeger college had gevolgd, en Linda Bakker, een fotografe die de avond vastlegde met haar camera. Mevrouw Li had echter haar twijfels over de voorstelling; ze was nooit een groot fan van Jan’s wat abstracte werk geweest. “We zullen zien, Carla,” zei Jansen glimlachend toen de lichten dimden, terwijl Li haar blik naar het podium richtte.
    Na de voorstelling verzamelden de vrienden zich in de foyer, waar ze werden vergezeld door Emma Vos, de regisseur van de voorstelling, en Alex Mulder, een energieke jonge dramaturg. Li complimenteerde Emma op de meeslepende sfeer van de avond, hoewel ze toe moest geven dat sommige scènes haar niet hadden aangesproken. Jansen, altijd enthousiast, begon een gepassioneerde discussie met Mark en Alex over de artistieke keuzes die Jan had gemaakt. Terwijl Carla met Linda en Emma stond te praten, schoot Helga Maria haar een glimlach toe; ze was blij dat haar vriendin, ondanks haar twijfels, toch was meegekomen. Toen de avond ten einde liep, liepen mevrouw Li en Jansen samen de frisse nachtlucht in, pratend over alles wat ze hadden gezien en beleefd."""

    formatter = PII_Everything()
    formatted_text, metadata = formatter.format(
        input_text, language="nl", with_metadata=True
    )

    print("Input text:\n", input_text, "\n\n")
    print("Output text:\n", formatted_text, "\n")
    print("Metadata:\n", metadata)
