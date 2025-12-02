import pytest
from ml.examples.example_agent import simple_agent


@pytest.mark.asyncio
async def test_simple_agent():
    input_data = {"query": "test query"}
    config = {"temperature": 0.7}

    result = await simple_agent(input_data, config)

    assert "response" in result
    assert "metadata" in result
    assert result["metadata"]["processed"] is True
    assert "test query" in result["response"]


@pytest.mark.asyncio
async def test_simple_agent_empty_query():
    input_data = {}
    config = {}

    result = await simple_agent(input_data, config)

    assert "response" in result
