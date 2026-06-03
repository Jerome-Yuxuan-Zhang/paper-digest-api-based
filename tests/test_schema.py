from paper_digest.schemas import EvidenceItem, PaperCard


def test_paper_card_defaults_and_validation() -> None:
    card = PaperCard(paper_id="paper_001", file_name="paper.pdf")
    assert card.title == "not stated"
    assert card.authors == []
    assert card.citation_risk == "medium"


def test_evidence_item_defaults() -> None:
    item = EvidenceItem()
    assert item.verification_needed is True
    assert item.page == "not stated"

