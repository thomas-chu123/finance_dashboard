from app.services.market_data import get_index_list


def test_requested_yahoo_symbols_are_available_as_indices():
    symbols = {item["symbol"]: item for item in get_index_list()}

    for symbol in ["^SOX", "TSM", "^TYX", "^TNX"]:
        assert symbol in symbols
        assert symbols[symbol]["category"] == "index"
