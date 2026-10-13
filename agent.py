from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from config import GEMINI_API_KEY, GEMINI_MODEL
from schema import ResearchResult, SEOResult, VerificationResult
from prompts import (
    RESEARCHER_SYSTEM_PROMPT,
    SEO_SYSTEM_PROMPT,
    WRITER_SYSTEM_PROMPT,
    MAIN_CHAT_SYSTEM_PROMPT,
    VERIFIER_SYSTEM_PROMPT,
)
from tools.researcher_tool import researcher_toolkit
from tools.seo_tool import seo_toolkit
from tools.writer_tool import  writer_toolkit


model = ChatGoogleGenerativeAI(
    api_key=GEMINI_API_KEY,
    model=GEMINI_MODEL,
)


def researcher_agent(message: str) -> ResearchResult:
    messages = [
        SystemMessage(content=RESEARCHER_SYSTEM_PROMPT),
        HumanMessage(content=message),
    ]
    agent = create_agent(
        model=model,
        tools=researcher_toolkit,
        response_format=ResearchResult,
    )
    result = agent.invoke({"messages": messages})
    return result["structured_response"]


def seo_agent(message: str) -> SEOResult:
    messages = [
        SystemMessage(content=SEO_SYSTEM_PROMPT),
        HumanMessage(content=message),
    ]
    agent = create_agent(
        model=model,
        tools=seo_toolkit,
        response_format=SEOResult,
    )
    result = agent.invoke({"messages": messages})
    return result["structured_response"]


def writer_agent(message: str) -> str:
    messages = [
        SystemMessage(content=WRITER_SYSTEM_PROMPT),
        HumanMessage(content=message),
    ]
    agent = create_agent(model=model, tools=writer_toolkit)
    result = agent.invoke({"messages": messages})
    return _extract_text(result["messages"][-1])


def verifier_agent(brief: str, blog: str, research=None, seo=None) -> VerificationResult :
    prompt = (
        f"BRIEF:\n{brief}\n\n"
        f"RESEARCH:\n{research or 'Not provided'}\n\n"
        f"SEO:\n{seo or 'Not provided'}\n\n"
        f"BLOG:\n{blog}"
    )
    messages = [
        SystemMessage(content=VERIFIER_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]
    agent = create_agent(
        model=model,
        response_format=VerificationResult
    )
    result = agent.invoke({"messages": messages})
    return result["structured_response"]


def _extract_text(message) -> str:
    """Handle both block-style and plain-string AIMessage content."""
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(content)



@tool
def call_researcher(topic: str) -> dict:
    """Run deep research on a blog topic.

    Args:
        topic: The blog topic or working title to research.

    Returns:
        Structured research findings (facts, sources, key points, angles).
    """
    result = researcher_agent(topic)
    return result.model_dump()


@tool
def call_seo_analyst(topic: str, research_summary: str) -> dict:
    """Run SEO analysis for a blog topic, informed by prior research.

    Args:
        topic: The blog topic or working title.
        research_summary: A concise summary of the researcher's findings
            (key points, angles, statistics) so keyword analysis aligns
            with the content.

    Returns:
        Structured SEO data (keywords, intent, title/meta, headings, gaps).
    """
    prompt = f"Topic: {topic}\n\nResearch context:\n{research_summary}"
    result = seo_agent(prompt)
    return result.model_dump()


@tool
def call_writer(brief: str, research: dict, seo: dict) -> str:
    """Write the final blog post given a brief, research, and SEO data.

    Args:
        brief: The original user brief (topic, audience, tone, length,
            must-include/must-avoid points).
        research: The ResearchResult dict from call_researcher.
        seo: The SEOResult dict from call_seo_analyst.

    Returns:
        The final blog post in Markdown.
    """
    prompt = (
        f"Brief:\n{brief}\n\n"
        f"Research findings:\n{research}\n\n"
        f"SEO analysis:\n{seo}\n\n"
        "Write the final blog post in Markdown."
    )
    return writer_agent(prompt)


@tool
def call_verifier(brief: str, blog: str, research: dict | None = None, seo: dict | None = None) -> str:
    """Verify the drafted blog post and rewrite it if it fails the quality threshold.

    Args:
        brief: The original user brief (topic, audience, tone, length,
            must-include/must-avoid points).
        blog: The drafted blog post in Markdown to verify.
        research: Optional ResearchResult dict from call_researcher.
        seo: Optional SEOResult dict from call_seo_analyst.

    Returns:
        The final blog post in Markdown — unchanged if it passed verification,
        or rewritten if it failed.
    """
    result = verifier_agent(brief, blog, research, seo)
    return result.model_dump()


def main_chat_agent(message: str) -> str:
    agent = create_agent(
        model=model,
        tools=[call_researcher, call_seo_analyst, call_writer, call_verifier],
        system_prompt=MAIN_CHAT_SYSTEM_PROMPT,
    )
    result = agent.invoke({"messages": [{"role": "user", "content": message}]})
    return _extract_text(result["messages"][-1])