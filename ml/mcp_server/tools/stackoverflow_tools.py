"""
StackOverflow Integration Tool
Analyzes developer activity, reputation, and expertise on StackOverflow
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import httpx
from pydantic import BaseModel, Field

from ml.mcp_server.tools.registry import tool_registry

STACKOVERFLOW_API_URL = "https://api.stackexchange.com/2.3"


class StackOverflowBadge(BaseModel):
    name: str
    rank: str  # gold, silver, bronze
    award_count: int = 1


class StackOverflowTag(BaseModel):
    name: str
    count: int
    score: int = 0


class StackOverflowAnswer(BaseModel):
    question_id: int
    answer_id: int
    score: int
    is_accepted: bool
    tags: List[str] = Field(default_factory=list)


class StackOverflowQuestion(BaseModel):
    question_id: int
    title: str
    score: int
    view_count: int
    answer_count: int
    tags: List[str] = Field(default_factory=list)


class StackOverflowAnalysisRequest(BaseModel):
    user_id: Optional[int] = Field(None, description="StackOverflow user ID")
    username: Optional[str] = Field(None, description="StackOverflow username (for search)")
    include_posts: bool = Field(True, description="Include recent posts")
    include_tags: bool = Field(True, description="Include tag statistics")


class StackOverflowAnalysisResponse(BaseModel):
    user_id: int
    username: str
    display_name: str
    reputation: int
    reputation_level: str  # "beginner", "intermediate", "advanced", "expert", "legendary"

    # Activity metrics
    question_count: int = 0
    answer_count: int = 0
    accepted_answer_count: int = 0
    total_upvotes: int = 0
    total_downvotes: int = 0
    account_age_days: Optional[int] = None

    # Engagement scores
    answer_rate: float = Field(default=0.0, description="Answers per day")
    acceptance_rate: float = Field(default=0.0, description="% of answers accepted")
    avg_answer_score: float = Field(default=0.0)
    activity_score: int = Field(default=0, ge=0, le=100)

    # Skills and expertise
    top_tags: List[StackOverflowTag] = Field(default_factory=list)
    badges: List[StackOverflowBadge] = Field(default_factory=list)
    badge_counts: Dict[str, int] = Field(default_factory=dict)

    # Recent activity
    recent_answers: List[StackOverflowAnswer] = Field(default_factory=list)
    recent_questions: List[StackOverflowQuestion] = Field(default_factory=list)

    # Profile
    profile_url: str
    location: Optional[str] = None
    website_url: Optional[str] = None

    # Metadata
    data_source: str = "stackoverflow_api"
    last_active: Optional[str] = None


async def _fetch_user_by_username(username: str) -> Optional[Dict]:
    """Search for user by username"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "inname": username,
                "site": "stackoverflow",
                "key": ""  # Optional: add your API key
            }

            resp = await client.get(f"{STACKOVERFLOW_API_URL}/users", params=params)

            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                if items:
                    return items[0]  # Return first match
    except Exception:
        pass

    return None


async def _fetch_user_data(user_id: int) -> Optional[Dict]:
    """Fetch user profile data"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "site": "stackoverflow",
                "filter": "!*MZqR3Ep3ikx7Cq"  # Include all fields
            }

            resp = await client.get(f"{STACKOVERFLOW_API_URL}/users/{user_id}", params=params)

            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                if items:
                    return items[0]
    except Exception:
        pass

    return None


async def _fetch_user_tags(user_id: int, limit: int = 10) -> List[StackOverflowTag]:
    """Fetch user's top tags"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "site": "stackoverflow",
                "pagesize": limit,
                "sort": "popular"
            }

            resp = await client.get(f"{STACKOVERFLOW_API_URL}/users/{user_id}/top-answer-tags", params=params)

            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])

                tags = []
                for item in items:
                    tags.append(StackOverflowTag(
                        name=item.get("tag_name", "unknown"),
                        count=item.get("answer_count", 0),
                        score=item.get("answer_score", 0)
                    ))
                return tags
    except Exception:
        pass

    return []


async def _fetch_user_answers(user_id: int, limit: int = 10) -> List[StackOverflowAnswer]:
    """Fetch user's recent answers"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "site": "stackoverflow",
                "pagesize": limit,
                "sort": "activity",
                "filter": "!9_bDE)OY4"  # Include question tags
            }

            resp = await client.get(f"{STACKOVERFLOW_API_URL}/users/{user_id}/answers", params=params)

            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])

                answers = []
                for item in items:
                    answers.append(StackOverflowAnswer(
                        question_id=item.get("question_id", 0),
                        answer_id=item.get("answer_id", 0),
                        score=item.get("score", 0),
                        is_accepted=item.get("is_accepted", False),
                        tags=[]  # Would need separate question fetch
                    ))
                return answers
    except Exception:
        pass

    return []


async def _fetch_user_questions(user_id: int, limit: int = 10) -> List[StackOverflowQuestion]:
    """Fetch user's recent questions"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "site": "stackoverflow",
                "pagesize": limit,
                "sort": "activity",
                "filter": "withbody"
            }

            resp = await client.get(f"{STACKOVERFLOW_API_URL}/users/{user_id}/questions", params=params)

            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])

                questions = []
                for item in items:
                    questions.append(StackOverflowQuestion(
                        question_id=item.get("question_id", 0),
                        title=item.get("title", ""),
                        score=item.get("score", 0),
                        view_count=item.get("view_count", 0),
                        answer_count=item.get("answer_count", 0),
                        tags=item.get("tags", [])
                    ))
                return questions
    except Exception:
        pass

    return []


async def _fetch_user_badges(user_id: int) -> Tuple[List[StackOverflowBadge], Dict[str, int]]:
    """Fetch user's badges"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "site": "stackoverflow",
                "pagesize": 100
            }

            resp = await client.get(f"{STACKOVERFLOW_API_URL}/users/{user_id}/badges", params=params)

            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])

                badge_map = {}
                badge_counts = {"gold": 0, "silver": 0, "bronze": 0}

                for item in items:
                    name = item.get("name", "")
                    rank = item.get("rank", "bronze")
                    award_count = item.get("award_count", 1)

                    if name in badge_map:
                        badge_map[name].award_count += award_count
                    else:
                        badge_map[name] = StackOverflowBadge(
                            name=name,
                            rank=rank,
                            award_count=award_count
                        )

                    badge_counts[rank] = badge_counts.get(rank, 0) + award_count

                badges = list(badge_map.values())[:20]  # Top 20
                return badges, badge_counts
    except Exception:
        pass

    return [], {}


def _calculate_reputation_level(reputation: int) -> str:
    """Determine reputation level"""
    if reputation >= 25000:
        return "legendary"
    elif reputation >= 10000:
        return "expert"
    elif reputation >= 3000:
        return "advanced"
    elif reputation >= 500:
        return "intermediate"
    else:
        return "beginner"


def _calculate_activity_score(
    reputation: int,
    answer_count: int,
    accepted_count: int,
    question_count: int,
    account_age_days: int
) -> int:
    """Calculate overall activity score (0-100)"""

    score = 0

    # Reputation contribution (max 40 points)
    if reputation >= 10000:
        score += 40
    elif reputation >= 5000:
        score += 30
    elif reputation >= 1000:
        score += 20
    elif reputation >= 100:
        score += 10

    # Answer activity (max 30 points)
    if answer_count >= 100:
        score += 30
    elif answer_count >= 50:
        score += 20
    elif answer_count >= 10:
        score += 10
    elif answer_count >= 1:
        score += 5

    # Acceptance rate (max 20 points)
    if answer_count > 0:
        acceptance_rate = accepted_count / answer_count
        score += int(acceptance_rate * 20)

    # Activity frequency (max 10 points)
    if account_age_days > 0:
        answers_per_month = (answer_count / account_age_days) * 30
        if answers_per_month >= 5:
            score += 10
        elif answers_per_month >= 2:
            score += 5
        elif answers_per_month >= 0.5:
            score += 2

    return min(100, score)


@tool_registry.register(
    name="analyze_stackoverflow",
    description="Analyze StackOverflow profile for developer activity and expertise",
    parameters=StackOverflowAnalysisRequest.model_json_schema(),
)
async def analyze_stackoverflow(**parameters) -> dict:
    """
    Analyze StackOverflow profile to assess:
    - Reputation and activity level
    - Expertise areas (tags)
    - Answer quality and acceptance rate
    - Community engagement
    """

    payload = StackOverflowAnalysisRequest(**parameters)

    # Get user data
    user_data = None

    if payload.user_id:
        user_data = await _fetch_user_data(payload.user_id)
    elif payload.username:
        user_data = await _fetch_user_by_username(payload.username)
    else:
        return {"error": "Either user_id or username must be provided"}

    if not user_data:
        return {"error": "User not found on StackOverflow"}

    user_id = user_data.get("user_id")
    display_name = user_data.get("display_name", "Unknown")
    reputation = user_data.get("reputation", 0)

    # Calculate account age
    creation_date = user_data.get("creation_date")
    account_age_days = None
    if creation_date:
        created_at = datetime.fromtimestamp(creation_date)
        account_age_days = (datetime.now() - created_at).days

    # Get last active time
    last_access_date = user_data.get("last_access_date")
    last_active = None
    if last_access_date:
        last_active = datetime.fromtimestamp(last_access_date).isoformat()

    # Fetch additional data in parallel
    tasks = [
        _fetch_user_tags(user_id, 15) if payload.include_tags else asyncio.sleep(0),
        _fetch_user_answers(user_id, 20) if payload.include_posts else asyncio.sleep(0),
        _fetch_user_questions(user_id, 10) if payload.include_posts else asyncio.sleep(0),
        _fetch_user_badges(user_id),
    ]

    results = await asyncio.gather(*tasks)

    top_tags = results[0] if isinstance(results[0], list) else []
    recent_answers = results[1] if isinstance(results[1], list) else []
    recent_questions = results[2] if isinstance(results[2], list) else []
    badges, badge_counts = results[3] if isinstance(results[3], tuple) else ([], {})

    # Calculate metrics
    answer_count = user_data.get("answer_count", 0)
    question_count = user_data.get("question_count", 0)
    accepted_answer_count = user_data.get("accept_rate", 0)  # Approximate

    # Count accepted answers from recent data
    if recent_answers:
        accepted_from_recent = sum(1 for a in recent_answers if a.is_accepted)
        if accepted_from_recent > 0:
            accepted_answer_count = max(accepted_answer_count, accepted_from_recent)

    # Calculate rates
    answer_rate = 0.0
    if account_age_days and account_age_days > 0:
        answer_rate = round(answer_count / account_age_days, 2)

    acceptance_rate = 0.0
    if answer_count > 0:
        acceptance_rate = round((accepted_answer_count / answer_count) * 100, 1)

    avg_answer_score = 0.0
    if recent_answers:
        avg_answer_score = round(
            sum(a.score for a in recent_answers) / len(recent_answers), 1
        )

    # Calculate activity score
    activity_score = _calculate_activity_score(
        reputation, answer_count, accepted_answer_count, question_count, account_age_days or 1
    )

    # Determine reputation level
    reputation_level = _calculate_reputation_level(reputation)

    # Build profile URL
    profile_url = f"https://stackoverflow.com/users/{user_id}"

    response = StackOverflowAnalysisResponse(
        user_id=user_id,
        username=user_data.get("link", "").split("/")[-1] if user_data.get("link") else str(user_id),
        display_name=display_name,
        reputation=reputation,
        reputation_level=reputation_level,
        question_count=question_count,
        answer_count=answer_count,
        accepted_answer_count=accepted_answer_count,
        total_upvotes=user_data.get("up_vote_count", 0),
        total_downvotes=user_data.get("down_vote_count", 0),
        account_age_days=account_age_days,
        answer_rate=answer_rate,
        acceptance_rate=acceptance_rate,
        avg_answer_score=avg_answer_score,
        activity_score=activity_score,
        top_tags=top_tags,
        badges=badges,
        badge_counts=badge_counts,
        recent_answers=recent_answers,
        recent_questions=recent_questions,
        profile_url=profile_url,
        location=user_data.get("location"),
        website_url=user_data.get("website_url"),
        last_active=last_active,
    )

    return response.model_dump()


@tool_registry.register(
    name="batch_analyze_stackoverflow",
    description="Analyze multiple StackOverflow profiles in parallel",
    parameters={
        "type": "object",
        "properties": {
            "user_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "List of StackOverflow user IDs"
            },
            "include_posts": {
                "type": "boolean",
                "default": False,
                "description": "Include recent posts (slower)"
            }
        },
        "required": ["user_ids"]
    }
)
async def batch_analyze_stackoverflow(**parameters) -> dict:
    """Analyze multiple StackOverflow profiles in parallel"""

    user_ids = parameters.get("user_ids", [])
    include_posts = parameters.get("include_posts", False)

    if not user_ids:
        return {"error": "No user_ids provided"}

    if len(user_ids) > 20:
        return {"error": "Maximum 20 users allowed per batch"}

    # Analyze in parallel
    tasks = [
        analyze_stackoverflow(user_id=uid, include_posts=include_posts)
        for uid in user_ids
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Format results
    profiles = []
    errors = []

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            errors.append({
                "user_id": user_ids[i],
                "error": str(result)
            })
        elif isinstance(result, dict) and "error" in result:
            errors.append({
                "user_id": user_ids[i],
                "error": result["error"]
            })
        else:
            profiles.append(result)

    return {
        "total": len(user_ids),
        "successful": len(profiles),
        "failed": len(errors),
        "profiles": profiles,
        "errors": errors
    }
