from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field


class NewsSearchInput(BaseModel):
    query: str = Field(description="The topic or question to search for in recent news.")

class Source(BaseModel):
    title: str = Field(description="Title of the source.")
    url: str = Field(description="URL of the source.")
    date: str | None = Field(default=None, description="Publication date if available (e.g., '2024-01-15').")
    summary: str | None = Field(default=None, description="Brief summary of the relevant content from this source.")

class ResearchFinding(BaseModel):
    topic: str = Field(description="The sub-topic or aspect this finding relates to.")
    finding: str = Field(description="The key finding or insight discovered.")
    sources: list[Source] = Field(default_factory=list, description="Sources that support this finding.")

class Fact(BaseModel):
    fact: str = Field(description="A verified factual statement useful for the blog.")
    source_url: str | None = Field(default=None, description="URL of the source supporting this fact.")
    date: str | None = Field(default=None, description="Date of the source if available.")

class Statistic(BaseModel):
    value: str = Field(description="The statistic, number, or data point discovered.")
    source_url: str | None = Field(default=None, description="URL of the source for this statistic.")
    date: str | None = Field(default=None, description="Date of the source if available.")

class ResearchResult(BaseModel):
    topic: str = Field(description="The main topic researched.")
    research_objective: str = Field(description="What the research was intended to discover.")
    audience_intent: str | None = Field(default=None, description="The intended audience and purpose of the blog, if known.")
    key_questions_answered: list[str] = Field(default_factory=list, description="The key questions that were answered by the research.")
    key_findings: list[ResearchFinding] = Field(default_factory=list, description="The most important findings from the research, each with supporting sources.")
    important_facts: list[Fact] = Field(default_factory=list, description="Important verified facts useful for the blog, each with source traceability.")
    statistics: list[Statistic] = Field(default_factory=list, description="Relevant statistics, numbers, or data discovered, each with source traceability.")
    expert_industry_insights: list[str] = Field(default_factory=list, description="Insights, opinions, or quotes from experts or industry leaders.")
    current_developments: list[str] = Field(default_factory=list, description="Recent developments, news, or updates related to the topic, with dates when possible.")
    conflicting_information: list[str] = Field(default_factory=list, description="Claims or information where reliable sources disagree.")
    knowledge_gaps: list[str] = Field(default_factory=list, description="Important information that could not be verified or found.")
    source_quality_notes: list[str] = Field(default_factory=list, description="Notes on the reliability, bias, or freshness of the sources used.")
    recommended_sources: list[Source] = Field(default_factory=list, description="Most useful sources for the blog writer to reference.")
    source_urls: list[str] = Field(default_factory=list, description="A flat list of all source URLs cited in the research brief.")



class SerpApiInput(BaseModel):
    engine: Literal[
        "google",
        "google_autocomplete",
        "google_news",
        "google_images",
        "google_scholar",
        "bing",
        "youtube",
    ] = Field(
        ...,
        description=(
            "SerpApi engine to query. Common values: 'google' (regular web search), "
            "'google_autocomplete' (query suggestions), 'google_news', 'google_images', "
            "'google_scholar', 'bing', 'youtube'."
        ),
    )
    query: str = Field(..., min_length=1, description="The search query / seed keyword (maps to SerpApi's 'q' parameter).")
    num_results: int = Field(
        default=10,
        ge=1,
        le=100,
        description=(
            "Maximum number of results. Only honored by engines that support it "
            "(e.g., 'google')."
        ),
    )
    extra_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Optional extra SerpApi parameters as key-value pairs, e.g. "
            "{'gl': 'us', 'hl': 'en', 'location': 'United States'}."
        ),
    )

class GetKeywordIdeasInput(BaseModel):
    seed_keyword: str = Field(...,min_length=1, description="Seed keyword or topic to expand into keyword ideas, e.g. 'best running shoes'.",)


class AnalyzeTopCompetitorsInput(BaseModel):
    keyword: str = Field(..., min_length=1, description="Target keyword whose top-ranking pages should be analyzed.")
    num_results: int = Field(default=5, ge=1, le=10, description="Number of top organic results to fetch and analyze (1-10).",)



class SEOResult(BaseModel):
    primary_keyword: str = Field(..., description="The seed/target keyword this research is based on.",)
    search_intent: Literal[
        "informational", "commercial", "transactional", "navigational", "mixed"
    ] = Field(..., description="Dominant search intent inferred from the SERP and PAA questions.",)
    autocomplete: List[str] = Field(default_factory=list, description="Google Autocomplete suggestions for the seed keyword.")
    related_questions: List[str] = Field(default_factory=list, description="People Also Ask (PAA) questions from the SERP.",)
    related_searches: List[str] = Field(default_factory=list, description="Related searches shown at the bottom of the Google SERP.")
    competitors: List[dict] = Field(
        default_factory=list,
        description=(
            "Top competitor pages analyzed. Each item: "
            "{'title': str, 'url': str, 'headings': list[str]}."
        ),
    )
    content_outline: List[str] = Field(
        default_factory=list,
        description=(
            "Recommended H2/H3 headings for the target page, synthesized from PAA, "
            "related searches, and competitor headings."
        ),
    )
    recommendations: List[str] = Field(default_factory=list, description="Prioritized, actionable SEO recommendations based on the findings.")
    summary: str = Field(..., description="2–3 sentence executive summary of the research and the main takeaway.",)


class FailedCheck(BaseModel):
    id: str = Field(description="Check ID from the checklist, e.g. 'A1', 'E3', 'F4'.")
    name: str = Field(description="Short human-readable name of the check.")
    evidence: str = Field(description="Exact quote from the blog that triggered the failure.")


class VerificationResult(BaseModel):
    verdict: Literal["PASS", "FAIL"] = Field(
        description="PASS if every check passed, FAIL if any check failed."
    )
    failed_checks: list[FailedCheck] = Field(
        default_factory=list,
        description="Every failed check with its ID, name, and quoted evidence. Empty on PASS.",
    )
    checks_passed: int = Field(
        description="Number of checks that passed."
    )
    checks_total: int = Field(
        description="Total number of checks in the rubric."
    )
    rewrite_log: list[str] = Field(
        default_factory=list,
        description="On FAIL: one line per fix applied. Empty on PASS.",
    )
    residual_weakness: str | None = Field(
        default=None,
        description="Advisory notes (e.g. A7/F5/F6) that did not fail the article.",
    )
    final_blog: str = Field(
        description=(
            "The complete final blog post in Markdown. "
            "On PASS, the original text unchanged, character for character. "
            "On FAIL, the repaired text."
        )
    )




# class ResearchItem(BaseModel):
#     topic: str
#     findings: str
#     sources: List[Source] = Field(default_factory=list)
#
#
# class FactCheckResult(BaseModel):
#     claim: str
#     status: str  # "verified", "questionable", "false"
#     explanation: Optional[str] = None
#     source: Optional[str] = None
#
#
# class BlogState(BaseModel):
#     # -------------------------
#     # User Request
#     # -------------------------
#     topic: str
#     target_audience: Optional[str] = None
#     tone: str = "professional"
#     language: str = "English"
#
#     # -------------------------
#     # Research
#     # -------------------------
#     research: List[ResearchItem] = Field(default_factory=list)
#     sources: List[Source] = Field(default_factory=list)
#     research_complete: bool = False
#
#     # -------------------------
#     # SEO
#     # -------------------------
#     primary_keyword: Optional[str] = None
#     secondary_keywords: List[str] = Field(default_factory=list)
#     search_intent: Optional[str] = None
#     seo_notes: List[str] = Field(default_factory=list)
#
#     # -------------------------
#     # Planning
#     # -------------------------
#     title: Optional[str] = None
#     outline: List[str] = Field(default_factory=list)
#     content_requirements: List[str] = Field(default_factory=list)
#
#     # -------------------------
#     # Writing
#     # -------------------------
#     draft: Optional[str] = None
#
#     # -------------------------
#     # Fact Checking
#     # -------------------------
#     fact_check_results: List[FactCheckResult] = Field(default_factory=list)
#     factual_issues: List[str] = Field(default_factory=list)
#     fact_check_passed: bool = False
#
#     # -------------------------
#     # Editing
#     # -------------------------
#     edited_content: Optional[str] = None
#     editing_notes: List[str] = Field(default_factory=list)
#
#     # -------------------------
#     # Final Output
#     # -------------------------
#     final_content: Optional[str] = None
#     meta_title: Optional[str] = None
#     meta_description: Optional[str] = None
#     slug: Optional[str] = None
#
#     # -------------------------
#     # Orchestration
#     # -------------------------
#     current_step: Optional[str] = None
#     next_step: Optional[str] = None
#     retry_count: int = 0
#     errors: List[str] = Field(default_factory=list)