from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from .. import models
from .llm_service import score_answer, summarise_interview, generate_followup_question


def get_next_question(job: models.Job, current_index: int) -> Optional[models.JobQuestion]:
    ordered = sorted(job.questions, key=lambda q: (q.order_index, q.id))
    if current_index >= len(ordered):
        return None
    return ordered[current_index]


def _too_short(answer_text: str) -> bool:
    a = (answer_text or "").strip()
    return (len(a) < 60) or (len(a.split()) < 15)


def _should_followup(
    scoring: Dict[str, Any],
    answer_text: str,
    followup_round: int,
    max_followups: int,
) -> bool:
    if followup_round >= max_followups:
        return False

    overall = scoring.get("overall_score")
    if overall is None:
        overall = 3

    # You can tune this threshold:
    # <=3 triggers follow-up; 4/5 moves on
    if overall <= 3:
        return True

    # Even if score OK, still follow up if answer is extremely short
    if _too_short(answer_text):
        return True

    return False


def start_interview(db: Session, interview: models.Interview) -> Optional[models.JobQuestion]:
    if interview.status == models.InterviewStatus.NOT_STARTED:
        interview.status = models.InterviewStatus.IN_PROGRESS
        interview.current_question_index = 0
        interview.started_at = interview.started_at or datetime.now(timezone.utc)

        first_q = get_next_question(interview.job, interview.current_question_index)
        interview.active_question_id = first_q.id if first_q else None
        interview.followup_round = 0
        interview.followup_question_text = None

        db.add(interview)
        db.commit()
        db.refresh(interview)

    return get_next_question(interview.job, interview.current_question_index)


def submit_answer_and_get_next(
    db: Session,
    interview: models.Interview,
    answer_text: str,
) -> Dict[str, Any]:
    job = interview.job
    comp_list: List[str] = job.competencies or []

    # Are we answering a follow-up right now?
    is_followup = bool(interview.followup_question_text)
    current_followup_round = interview.followup_round if is_followup else 0

    spine_q = get_next_question(job, interview.current_question_index)

    # If spine_q doesn't exist AND we aren't in follow-up mode => done
    if not spine_q and not is_followup:
        interview.status = models.InterviewStatus.COMPLETED
        interview.completed_at = interview.completed_at or datetime.now(timezone.utc)
        db.add(interview)
        db.commit()
        return {
            "answer": None,
            "next_question": None,
            "interview_status": interview.status,
            "scoring": None,
            "asked_question_text": "",
            "is_followup": False,
            "followup_round": 0,
        }

    base_question_text = spine_q.text if spine_q else ""
    asked_question_text = interview.followup_question_text if is_followup else base_question_text

    # Store the answer row
    db_answer = models.InterviewAnswer(
        interview_id=interview.id,
        question_id=None if is_followup else (spine_q.id if spine_q else None),
        question_text=asked_question_text,
        is_followup=1 if is_followup else 0,
        parent_question_id=(spine_q.id if (is_followup and spine_q) else None),
        followup_round=current_followup_round,
        answer_text=answer_text,
    )
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)

    # Score against BASE question (even if user answered follow-up)
    scoring = score_answer(base_question_text, answer_text, comp_list)

    db_answer.score = scoring.get("overall_score")
    db_answer.competency_scores = scoring.get("competency_scores")
    db_answer.ai_feedback = scoring.get("feedback")
    db.add(db_answer)

    # Decide: follow-up or move to next spine question
    needs_followup = _should_followup(
        scoring=scoring,
        answer_text=answer_text,
        followup_round=current_followup_round,
        max_followups=interview.max_followups_per_question,
    )

    next_q: Any = None

    if needs_followup:
        # Ask LLM to generate one follow-up question
        followup_payload = generate_followup_question(
            base_question=base_question_text,
            answer=answer_text,
            competencies=comp_list,
            scoring=scoring,
            followup_round=current_followup_round,
        )
        followup_text = (followup_payload.get("followup_question") or "").strip()
        if not followup_text:
            # fallback (shouldn't happen, but safe)
            followup_text = "Can you clarify that further with a specific example and the outcome?"

        interview.followup_round = current_followup_round + 1 if is_followup else 1
        interview.followup_question_text = followup_text

        next_q = {"type": "FOLLOWUP", "text": followup_text, "round": interview.followup_round}

    else:
        # Clear follow-up state and advance spine
        interview.followup_round = 0
        interview.followup_question_text = None

        interview.current_question_index += 1
        next_spine = get_next_question(job, interview.current_question_index)
        interview.active_question_id = next_spine.id if next_spine else None
        next_q = next_spine

        if next_spine is None:
            interview.status = models.InterviewStatus.COMPLETED
            interview.completed_at = interview.completed_at or datetime.now(timezone.utc)

    db.add(interview)
    db.commit()
    db.refresh(interview)

    return {
        "answer": db_answer,
        "next_question": next_q,
        "interview_status": interview.status,
        "scoring": scoring,
        "asked_question_text": asked_question_text,
        "is_followup": is_followup,
        "followup_round": current_followup_round,
    }


def generate_interview_summary(db: Session, interview: models.Interview) -> Dict:
    job = interview.job
    qa_list = []

    for ans in interview.answers:
        qa_list.append(
            {
                "question": ans.question_text or (ans.question.text if ans.question else ""),
                "answer": ans.answer_text,
                "score": ans.score,
                "competency_scores": ans.competency_scores or {},
                "is_followup": bool(ans.is_followup),
                "followup_round": ans.followup_round,
            }
        )

    summary = summarise_interview(job.title, job.description, qa_list)
    return summary
