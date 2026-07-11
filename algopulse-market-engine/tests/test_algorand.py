from algopulse.algorand import current_algod_round


class _FakeAlgod:
    def __init__(self, response=None, *, error: Exception | None = None) -> None:
        self.response = response or {}
        self.error = error

    def status(self) -> dict:
        if self.error:
            raise self.error
        return self.response


def test_current_algod_round_reads_last_round():
    assert current_algod_round(_FakeAlgod({"last-round": 12_345})) == 12_345


def test_current_algod_round_accepts_underscore_key():
    assert current_algod_round(_FakeAlgod({"last_round": 12_346})) == 12_346


def test_current_algod_round_falls_back_to_zero_on_error():
    assert current_algod_round(_FakeAlgod(error=RuntimeError("offline"))) == 0
