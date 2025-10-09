from pathlib import Path


def test_load_privateai_module():
    """Pytest that tests loading and intializing the PrivateAI PII Module."""
    from gptnl_pii_mappers import PII_PrivateAI_TNO

    pf_csv_files = [
        Path("./gptnl_pii_mappers/_backend/public_figures/names_aliases_en.csv")
    ]

    _ = PII_PrivateAI_TNO(
        api_endpoint="https://privateai-cpu.ada.tnods.nl/",
        replacement_type="SYNTHETIC",
        entity_grouping_window=1024,
        check_public_figure=True,
        record_entities=True,
        public_figure_csv_files=pf_csv_files,
    )

    assert True
