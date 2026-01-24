from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import re

from sqlalchemy.orm import Session

from .. import models


def _has_number(text: str) -> bool:
    return bool(re.search(r"\b\d+(\.\d+)?\b", text))


def _is_too_short(text: str) -> bool:
    t = text.strip()
    return len(t) < 60 or len(t.split()) < 15


def _missing_ownership(text: str) -> bool:
    lowered = text.lower()
    return (" i " not in f" {lowered} ") and (" my " not in f" {lowered} ")


def _score_answer(answer: str) -> int:
    a = answer.strip()
    if len(a) < 40:
        return 1

    score = 2
    if len(a.split()) >= 30:
        score += 1
    if _has_number(a):
        score += 1
    if any(k in a.lower() for k in ["result", "impact", "improved", "reduced", "increased", "optimized"]):
        score += 1
    return max(1, min(5, score))


def decide_followup(
    *,
    competency: Optional[str],
    answer_text: str,
    followup_round: int,
    max_followups: int,
) -> Dict[str, Any]:
    """
    Deterministic MVP decision engine.
    Later you replace this body with an LLM call returning same keys.
    """
    score = _score_answer(answer_text)

    comp_scores: Dict[str, int] = {}
    if competency:
        comp_scores[competency] = score

    # If good enough OR reached follow-up cap → move on
    if score >= 4 or followup_round >= max_followups:
        return {
            "needs_followup": False,
            "followup_question": None,
            "score": score,
            "competency_scores": comp_scores,
            "feedback": "Strong enough — moving on." if score >= 4 else "Follow-up cap reached — moving on.",
        }

    # Follow-up probes
    if _is_too_short(answer_text):
        return {
            "needs_followup": True,
            "followup_question": "Can you add more detail? Walk me through what you did step-by-step and what the outcome was.",
            "score": score,
            "competency_scores": comp_scores,
            "feedback": "Answer is too brief; needs more detail.",
        }

    if _missing_ownership(answer_text):
        return {
            "needs_followup": True,
            "followup_question": "What was your specific role in this? What did you personally do vs what the team did?",
            "score": score,
            "competency_scores": comp_scores,
            "feedback": "Ownership is unclear.",
        }

    if not _has_number(answer_text):
        return {
            "needs_followup": True,
            "followup_question": "What was the measurable impact? For example: time saved, errors reduced, performance improved, or cost impact.",
            "score": score,
            "competency_scores": comp_scores,
            "feedback": "Missing measurable impact.",
        }

    return {
        "needs_followup": True,
        "followup_question": "That makes sense — what would you do differently next time, and why?",
        "score": score,
        "competency_scores": comp_scores,
        "feedback": "Needs deeper clarity/reflection.",
    }


def _get_spine_question_by_index(db: Session, job_id: int, idx: int) -> Optional[models.JobQuestion]:
    questions = (
        db.query(models.JobQuestion)
        .filter(models.JobQuestion.job_id == job_id)
        .order_by(models.JobQuestion.order_index.asc(), models.JobQuestion.id.asc())
        .all()
    )
    if idx < 0 or idx >= len(questions):
        return None
    return questions[idx]


def start_interview(db: Session, interview: models.Interview) -> Optional[models.JobQuestion]:
    if interview.status == models.InterviewStatus.NOT_STARTED:
        interview.status = models.InterviewStatus.IN_PROGRESS
        interview.started_at = interview.started_at or datetime.now(timezone.utc)

    q = _get_spine_question_by_index(db, interview.job_id, interview.current_question_index)

    interview.active_question_id = q.id if q else None
    interview.followup_round = 0
    interview.followup_question_text = None

    db.add(interview)
    db.commit()
    db.refresh(interview)
    return q


def submit_answer_and_get_next(db: Session, interview: models.Interview, answer_text: str) -> Dict[str, Any]:
    if interview.status != models.InterviewStatus.IN_PROGRESS:
        interview.status = models.InterviewStatus.IN_PROGRESS

    # Determine if the last asked question was a follow-up
    is_followup = bool(interview.followup_question_text)

    # Get spine question
    spine_q = None
    if interview.active_question_id:
        spine_q = db.query(models.JobQuestion).filter(models.JobQuestion.id == interview.active_question_id).first()

    if spine_q is None:
        spine_q = _get_spine_question_by_index(db, interview.job_id, interview.current_question_index)
        interview.active_question_id = spine_q.id if spine_q else None

    if spine_q is None:
        interview.status = models.InterviewStatus.COMPLETED
        interview.completed_at = datetime.now(timezone.utc)
        db.add(interview)
        db.commit()
        return {
            "asked_question_text": "",
            "is_followup": False,
            "followup_round": 0,
            "answer": None,
            "next_question": None,
            "interview_status": interview.status,
        }

    asked_question_text = interview.followup_question_text if is_followup else spine_q.text
    current_round = interview.followup_round if is_followup else 0

    decision = decide_followup(
        competency=spine_q.competency,
        answer_text=answer_text,
        followup_round=current_round,
        max_followups=interview.max_followups_per_question,
    )

    # Store answer record
    ans = models.InterviewAnswer(
        interview_id=interview.id,
        question_id=None if is_followup else spine_q.id,
        question_text=asked_question_text,
        is_followup=1 if is_followup else 0,
        parent_question_id=spine_q.id if is_followup else None,
        followup_round=current_round,
        answer_text=answer_text,
        score=decision["score"],
        competency_scores=decision["competency_scores"],
        ai_feedback=decision["feedback"],
    )
    db.add(ans)

    # Next step
    next_question = None

    if decision["needs_followup"]:
        # set follow-up state
        interview.followup_round = (current_round + 1) if is_followup else 1
        interview.followup_question_text = decision["followup_question"]
        next_question = {"type": "FOLLOWUP", "text": decision["followup_question"], "round": interview.followup_round}
    else:
        # clear follow-up state and move on spine
        interview.followup_round = 0
        interview.followup_question_text = None
        interview.current_question_index += 1

        nq = _get_spine_question_by_index(db, interview.job_id, interview.current_question_index)
        interview.active_question_id = nq.id if nq else None
        next_question = nq

        if nq is None:
            interview.status = models.InterviewStatus.COMPLETED
            interview.completed_at = datetime.now(timezone.utc)

    db.add(interview)
    db.commit()
    db.refresh(interview)
    db.refresh(ans)

    return {
        "asked_question_text": asked_question_text,
        "is_followup": is_followup,
        "followup_round": current_round,
        "answer": ans,
        "decision": decision,
        "next_question": next_question,
        "interview_status": interview.status,
    }
