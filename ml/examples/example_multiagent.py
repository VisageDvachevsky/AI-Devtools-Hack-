from ml.agents.registry import agent_registry
from typing import Dict, Any
import os


@agent_registry.register(
    name="research_agent",
    description="Agent for researching topics using external APIs"
)
async def research_agent(input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Агент для исследования темы.
    Собирает информацию из разных источников.
    """
    topic = input_data.get("topic", "")

    results = {
        "topic": topic,
        "sources": []
    }

    # Здесь можно вызывать tools напрямую
    # В реальном проекте используй LangChain для автоматического выбора tools

    return {
        "agent": "research_agent",
        "findings": results,
        "next_action": "Pass to analytics_agent for processing"
    }


@agent_registry.register(
    name="analytics_agent",
    description="Agent for analyzing collected data"
)
async def analytics_agent(input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Агент для анализа данных.
    Обрабатывает информацию от research_agent.
    """
    data = input_data.get("data", {})

    analysis = {
        "summary": f"Analyzed {len(data)} items",
        "key_points": [],
        "sentiment": "neutral"
    }

    return {
        "agent": "analytics_agent",
        "analysis": analysis,
        "next_action": "Pass to reporting_agent"
    }


@agent_registry.register(
    name="reporting_agent",
    description="Agent for generating reports"
)
async def reporting_agent(input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Агент для генерации отчетов.
    Создает финальный отчет на основе анализа.
    """
    analysis = input_data.get("analysis", {})

    report = {
        "title": "Research Report",
        "content": "Generated report based on analysis",
        "format": "markdown"
    }

    return {
        "agent": "reporting_agent",
        "report": report,
        "status": "completed"
    }


@agent_registry.register(
    name="coordinator_agent",
    description="Coordinator for multi-agent system"
)
async def coordinator_agent(input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Координатор мультиагентной системы.
    Управляет workflow между агентами.

    Пример использования:
    {
        "task": "Research AI trends in 2024",
        "workflow": ["research", "analyze", "report"]
    }
    """
    task = input_data.get("task", "")
    workflow = input_data.get("workflow", [])

    results = {
        "task": task,
        "steps_completed": [],
        "final_output": {}
    }

    # Простая логика координации
    # В реальном проекте используй LangChain Agents или CrewAI

    current_data = {"topic": task}

    if "research" in workflow:
        research_result = await research_agent(
            {"topic": task},
            config
        )
        results["steps_completed"].append("research")
        current_data = research_result

    if "analyze" in workflow:
        analytics_result = await analytics_agent(
            {"data": current_data},
            config
        )
        results["steps_completed"].append("analyze")
        current_data = analytics_result

    if "report" in workflow:
        report_result = await reporting_agent(
            {"analysis": current_data},
            config
        )
        results["steps_completed"].append("report")
        results["final_output"] = report_result

    return {
        "coordinator": "completed",
        "workflow": workflow,
        "results": results
    }


@agent_registry.register(
    name="business_automation_agent",
    description="Agent for business process automation using LangChain"
)
async def business_automation_agent(input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Пример агента с LangChain для бизнес-автоматизации.

    Требует установки:
    - langchain
    - langchain-openai
    """
    try:
        from langchain_openai import ChatOpenAI
        from langchain.agents import AgentExecutor, create_openai_functions_agent
        from langchain.prompts import ChatPromptTemplate

        api_key = os.getenv("EVOLUTION_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"error": "No LLM API key configured"}

        llm = ChatOpenAI(
            api_key=api_key,
            base_url=os.getenv("EVOLUTION_API_URL", "https://api.openai.com/v1"),
            model="gpt-3.5-turbo",
            temperature=config.get("temperature", 0.7)
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a business automation assistant."),
            ("human", "{input}")
        ])

        query = input_data.get("query", "")
        response = await llm.ainvoke(prompt.format_messages(input=query))

        return {
            "agent": "business_automation",
            "response": response.content,
            "model": "Evolution/GPT-3.5"
        }

    except ImportError:
        return {
            "error": "LangChain not installed. Run: pip install langchain langchain-openai"
        }
    except Exception as e:
        return {"error": str(e)}
