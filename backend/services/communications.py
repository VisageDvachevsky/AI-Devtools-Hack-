from typing import Dict, List


def generate_outreach_template(
    candidate_username: str,
    role: str,
    matched_skills: List[str],
    company_name: str = "Our Company",
    recruiter_name: str = "HR Team"
) -> Dict[str, str]:
    """Generate personalized outreach message"""

    skills_str = ", ".join(matched_skills[:3]) if matched_skills else "your technical skills"

    subject = f"Opportunity: {role} position at {company_name}"

    body = f"""Hello {candidate_username},

I came across your GitHub profile and was impressed by your work, particularly your skills in {skills_str}.

We're currently looking for a {role} at {company_name}, and I believe your background could be a great fit for our team.

Would you be interested in a brief conversation to learn more about this opportunity?

Best regards,
{recruiter_name}
{company_name}"""

    return {
        "subject": subject,
        "body": body,
        "channel": "email"
    }


def generate_followup_template(
    candidate_username: str,
    days_since_outreach: int = 7,
    original_role: str = ""
) -> Dict[str, str]:
    """Generate follow-up message"""

    subject = f"Following up: {original_role} opportunity" if original_role else "Following up on our opportunity"

    body = f"""Hello {candidate_username},

I wanted to follow up on my previous message about the {original_role} position.

Are you still interested in exploring this opportunity? I'd be happy to answer any questions you might have.

Looking forward to hearing from you.

Best regards"""

    return {
        "subject": subject,
        "body": body,
        "channel": "email",
        "days_since_outreach": days_since_outreach
    }


def generate_interview_invitation(
    candidate_username: str,
    role: str,
    interview_type: str = "technical",
    duration_minutes: int = 60
) -> Dict[str, str]:
    """Generate interview invitation"""

    subject = f"Interview Invitation: {role} position"

    interview_types = {
        "technical": "technical interview",
        "hr": "initial HR interview",
        "final": "final interview"
    }

    interview_desc = interview_types.get(interview_type, "interview")

    body = f"""Hello {candidate_username},

Thank you for your interest in the {role} position!

We'd like to invite you for a {interview_desc} (approximately {duration_minutes} minutes).

Please let me know your availability for the upcoming week, and we'll schedule a time that works for both of us.

Best regards"""

    return {
        "subject": subject,
        "body": body,
        "channel": "email",
        "interview_type": interview_type,
        "duration_minutes": duration_minutes
    }


def generate_rejection_template(
    candidate_username: str,
    role: str,
    reason: str = "general"
) -> Dict[str, str]:
    """Generate rejection message"""

    subject = f"Update on your {role} application"

    reasons_map = {
        "skill_gap": "we've decided to move forward with candidates whose skills more closely match our current requirements",
        "experience": "we're looking for candidates with more experience in this particular area",
        "general": "we've decided to move forward with other candidates"
    }

    reason_text = reasons_map.get(reason, reasons_map["general"])

    body = f"""Hello {candidate_username},

Thank you for your interest in the {role} position.

After careful consideration, {reason_text}.

We appreciate the time you took to apply and wish you the best in your job search.

Best regards"""

    return {
        "subject": subject,
        "body": body,
        "channel": "email"
    }


def generate_offer_template(
    candidate_username: str,
    role: str,
    salary_range: Dict[str, float] = None
) -> Dict[str, str]:
    """Generate offer message"""

    subject = f"Job Offer: {role} position"

    salary_text = ""
    if salary_range:
        salary_text = f"\n\nThe position offers a competitive salary range of {int(salary_range.get('min', 0)):,} - {int(salary_range.get('max', 0)):,} RUB per month."

    body = f"""Hello {candidate_username},

We're excited to offer you the {role} position at our company!{salary_text}

We believe you'll be a great addition to our team. Please review the attached offer details and let us know if you have any questions.

We look forward to working with you!

Best regards"""

    return {
        "subject": subject,
        "body": body,
        "channel": "email"
    }


def generate_status_update(
    candidate_username: str,
    current_stage: str,
    next_steps: str = ""
) -> Dict[str, str]:
    """Generate status update message"""

    subject = "Update on your application"

    next_steps_text = f"\n\nNext steps: {next_steps}" if next_steps else ""

    body = f"""Hello {candidate_username},

I wanted to give you a quick update on your application.

Current status: {current_stage}{next_steps_text}

Please let me know if you have any questions.

Best regards"""

    return {
        "subject": subject,
        "body": body,
        "channel": "email"
    }
