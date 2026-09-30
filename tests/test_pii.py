from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_scrub_cccd() -> None:
    cccd = "001099012345"
    out = scrub_text(f"Số CCCD của tôi là {cccd}")
    assert cccd not in out
    assert "[REDACTED_CCCD]" in out


def test_scrub_credit_card_formats() -> None:
    cards = (
        "4111 1111 1111 1111",
        "4111-1111-1111-1111",
        "4111111111111111",
    )
    for card in cards:
        out = scrub_text(f"Card number: {card}")
        assert card not in out
        assert "[REDACTED_CREDIT_CARD]" in out


def test_scrub_multiple_pii_types() -> None:
    msg = "a@b.vn 0901234567 001099012345 4111 1111 1111 1111"
    out = scrub_text(msg)
    assert out == "[REDACTED_EMAIL] [REDACTED_PHONE_VN] [REDACTED_CCCD] [REDACTED_CREDIT_CARD]"

