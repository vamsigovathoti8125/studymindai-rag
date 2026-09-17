from src.agent.agent import decide_tool


def test_decide_tool_calculator():
    assert decide_tool("25 * 48") == "calculator"


def test_decide_tool_quiz():
    assert decide_tool("Generate MCQs about linear regression") == "quiz"


def test_decide_tool_summary():
    assert decide_tool("Summarize my notes on RAG") == "summary"


def test_decide_tool_rag():
    assert decide_tool("What is overfitting?") == "rag"
