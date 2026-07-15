"""一週財經大事結構化經濟數據服務測試。"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.economic_data_service import (
    _fetch_bls_data,
    _fetch_ism_pmi,
    format_economic_data_for_prompt,
)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_bls_data_calculates_cpi_and_nonfarm_changes():
    """CPI 應計算月年增率，非農應以兩期總人數差額表示新增人數。"""
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "status": "REQUEST_SUCCEEDED",
        "Results": {
            "series": [
                {
                    "seriesID": "CUSR0000SA0",
                    "data": [
                        {"year": "2026", "period": "M06", "value": "332.0"},
                        {"year": "2026", "period": "M05", "value": "331.0"},
                        {"year": "2025", "period": "M06", "value": "323.0"},
                    ],
                },
                {
                    "seriesID": "CES0000000001",
                    "data": [
                        {"year": "2026", "period": "M06", "value": "158984"},
                        {"year": "2026", "period": "M05", "value": "158927"},
                    ],
                },
            ]
        },
    }
    client = AsyncMock()
    client.post.return_value = response

    result = await _fetch_bls_data(client)

    assert result["cpi"]["period"] == "2026-06"
    assert result["cpi"]["month_over_month_pct"] == pytest.approx((332 / 331 - 1) * 100)
    assert result["cpi"]["year_over_year_pct"] == pytest.approx((332 / 323 - 1) * 100)
    assert result["nonfarm"]["value"] == 158984
    assert result["nonfarm"]["change"] == 57


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ism_parser_extracts_actual_and_previous_value():
    """ISM 官方頁面應解析月份、實際 PMI 與前值。"""
    response = MagicMock()
    response.status_code = 200
    response.text = """
        <h1>Manufacturing PMI® at 53.3%</h1>
        <h2>June 2026 ISM® Manufacturing PMI® Report</h2>
        <p>The Manufacturing PMI® registered 53.3 percent in June,
        0.7 percentage point lower than in May.</p>
    """
    client = AsyncMock()
    client.get.return_value = response

    with patch("app.services.economic_data_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = MagicMock(year=2026, month=7)
        mock_datetime.side_effect = lambda *args, **kwargs: __import__("datetime").datetime(*args, **kwargs)
        result = await _fetch_ism_pmi(client)

    assert result["period"] == "2026-06"
    assert result["value"] == 53.3
    assert result["previous_value"] == pytest.approx(54.0)
    assert result["source"] == "ISM"


@pytest.mark.unit
def test_prompt_formatter_includes_period_value_unit_and_change():
    """交給 Ollama 的資料文字必須包含可核對的實際數據。"""
    text = format_economic_data_for_prompt(
        [
            {
                "name": "美國非農就業",
                "period": "2026-06",
                "value": 158984,
                "unit": "千人",
                "previous_value": 158927,
                "change": 57,
                "change_unit": "千人",
                "source": "BLS",
                "source_url": "https://data.bls.gov/example",
            }
        ]
    )

    assert "2026-06" in text
    assert "實際值 158984 千人" in text
    assert "較前值變動 +57.00 千人" in text
    assert "來源 BLS" in text


@pytest.mark.unit
@pytest.mark.asyncio
async def test_weekly_brief_fetches_economic_data_before_search_and_prompts_values():
    """一週財經大事應先取數據，再搜尋，並把數值交給 Ollama。"""
    from app.services.news_briefing_service import _generate_weekly_finance_events

    calls = []
    record = {
        "type": "economic_data",
        "key": "pmi",
        "name": "美國 ISM 製造業 PMI",
        "period": "2026-06",
        "value": 53.3,
        "unit": "指數",
        "previous_value": 54.0,
        "source": "ISM",
        "source_url": "https://www.ismworld.org/report",
        "reference_url": "https://www.macromicro.me/pmi",
    }

    async def fetch_data():
        calls.append("economic_data")
        return [record]

    async def search(*args, **kwargs):
        calls.append("search")
        return [{"title": "Fed event", "description": "rate", "url": "https://example.com"}]

    generate = AsyncMock(return_value="含有 2026-06 PMI 53.3 指數的評測")
    with (
        patch("app.services.economic_data_service.fetch_weekly_economic_data", side_effect=fetch_data),
        patch("app.services.searxng_service.search_news", side_effect=search),
        patch("app.services.ollama_service.generate_custom_brief", generate),
    ):
        news_items, summary = await _generate_weekly_finance_events()

    assert calls == ["economic_data", "search"]
    prompt = generate.await_args.args[0]
    assert "實際值 53.3 指數" in prompt
    assert "禁止只做" in prompt
    assert news_items[0]["economic_data"]["value"] == 53.3
    assert summary.startswith("【最新實際經濟數據】")
    assert "53.3" in summary
