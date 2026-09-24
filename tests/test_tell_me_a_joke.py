import tell_me_a_joke


def test_main_echoes_joke_topic(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt="": "cats")

    tell_me_a_joke.main()

    out = capsys.readouterr().out
    assert "i got the topic, i will tell a joke about this: cats" in out


def test_main_preserves_whitespace_verbatim(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt="": "  pizza  ")

    tell_me_a_joke.main()

    out = capsys.readouterr().out
    assert "i got the topic, i will tell a joke about this:   pizza  \n" in out
