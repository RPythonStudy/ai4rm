import os
import pytest
from ff3 import FF3Cipher
import common.get_cipher as get_cipher

def test_missing_env_vars_raise(monkeypatch):
    # load_dotenv를 막아서 .env 다시 읽지 않도록
    monkeypatch.setattr(get_cipher, "load_dotenv", lambda *a, **kw: None)

    for var in ["FF3_KEY", "FF3_TWEAK", "FF3_ALPHABET"]:
        monkeypatch.delenv(var, raising=False)
        with pytest.raises(RuntimeError):
            get_cipher.get_cipher()


def test_invalid_key(monkeypatch):
    monkeypatch.setattr(get_cipher, "load_dotenv", lambda *a, **kw: None)
    monkeypatch.setenv("FF3_KEY", "1234")  # invalid length
    monkeypatch.setenv("FF3_TWEAK", "cafebabefacedbad")
    monkeypatch.setenv("FF3_ALPHABET", "0123456789")
    with pytest.raises(ValueError):
        get_cipher.get_cipher()

def test_invalid_tweak(monkeypatch):
    monkeypatch.setattr(get_cipher, "load_dotenv", lambda *a, **kw: None)
    monkeypatch.setenv("FF3_KEY", "2bd6459f82c5b300952c49104881ff48")
    monkeypatch.setenv("FF3_TWEAK", "1234")  # invalid tweak
    monkeypatch.setenv("FF3_ALPHABET", "0123456789")
    cipher = get_cipher.get_cipher()
    with pytest.raises(Exception):
        cipher.encrypt("12345678")
