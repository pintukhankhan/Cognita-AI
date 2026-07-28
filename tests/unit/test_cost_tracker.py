import pytest
from src.services.cost_tracker import CostTracker

@pytest.mark.asyncio
async def test_record_and_summary():
    t = CostTracker()
    await t.record("gpt-4o", 1000, 500)
    s = await t.summary()
    assert s["total_usd"] > 0 and s["by_model"]["gpt-4o"]["calls"] == 1
