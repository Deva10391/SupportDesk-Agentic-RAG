from app.pii import mask


def test_masks_email_and_phone():
    out = mask("mail a.b@x.com or call +91 98765 43210")
    assert "a.b@x.com" not in out and "98765" not in out

def test_keeps_dates():
    assert mask("eta=2026-11-20") == "eta=2026-11-20"