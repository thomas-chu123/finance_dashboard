from app.services.jp_etf_sync import _parse_jpx_etf_table
from app.services.market_data import _to_yf_symbol, get_symbol_currency


def test_parse_jpx_etf_table_extracts_records():
    html = """
    <table>
      <tr>
        <th>Listing Date</th>
        <th>Index</th>
        <th>Code</th>
        <th>Fund Name</th>
        <th>Management Company</th>
        <th>Trading Unit</th>
      </tr>
      <tr>
        <td>2001/7/13</td>
        <td>Nikkei 225</td>
        <td>1321</td>
        <td>Nikko Exchange Traded Fund Nikkei 225</td>
        <td>Nikko Asset Management</td>
        <td>1 unit</td>
      </tr>
    </table>
    """

    records = _parse_jpx_etf_table(html)

    assert records[0]["symbol"] == "1321"
    assert records[0]["name"] == "Nikko Exchange Traded Fund Nikkei 225"
    assert records[0]["index_name"] == "Nikkei 225"
    assert records[0]["management_company"] == "Nikko Asset Management"
    assert records[0]["trading_unit"] == "1 unit"


def test_japan_etf_symbol_mapping_and_currency():
    assert _to_yf_symbol("1321.T") == "1321.T"
    assert _to_yf_symbol("0050") == "0050.TW"
    assert get_symbol_currency("1321.T") == "JPY"


def test_parse_jpx_japanese_headers():
    html = """
    <table><tr><th>銘柄コード</th><th>銘柄名</th></tr>
    <tr><td>1321</td><td>日経225連動型上場投資信託</td></tr></table>
    """
    records = _parse_jpx_etf_table(html, "ja")
    assert records[0]["symbol"] == "1321"
    assert records[0]["name_ja"] == "日経225連動型上場投資信託"
