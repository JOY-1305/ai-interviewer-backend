from sqlalchemy.orm import Session
from typing import Optional, List, Dict

from .. import models
from ..schemas import InterviewStatus
from .llm_service import score_answer, summarise_interview


def get_next_question(job: models.Job, current_index: int) -> Optional[models.JobQuestion]:
    ordered = sorted(job.questions, key=lambda q: q.order_index)
    if current_index >= len(ordered):
        return None
    return ordered[current_index]


def start_interview(db: Session, interview: models.Interview) -> Optional[models.JobQuestion]:
    if interview.status == models.InterviewStatus.NOT_STARTED:
        interview.status = models.InterviewStatus.IN_PROGRESS
        interview.current_question_index = 0
        db.add(interview)
        db.commit()
        db.refresh(interview)

    return get_next_question(interview.job, interview.current_question_index)


def submit_answer_and_get_next(
    db: Session,
    interview: models.Interview,
    answer_text: str,
) -> Dict:
    job = interview.job
    question = get_next_question(job, interview.current_question_index)
    if not question:
        interview.status = models.InterviewStatus.COMPLETED
        db.add(interview)
        db.commit()
        return {
            "answer": None,
            "next_question": None,
            "interview_status": models.InterviewStatus.COMPLETED,
            "scoring": None,
        }

    db_answer = models.InterviewAnswer(
        interview_id=interview.id,
        question_id=question.id,
        answer_text=answer_text,
    )
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)

    comp_list: List[str] = job.competencies or []
    scoring = score_answer(question.text, answer_text, comp_list)

    db_answer.score = scoring.get("overall_score")
    db_answer.competency_scores = scoring.get("competency_scores")
    db_answer.ai_feedback = scoring.get("feedback")
    db.add(db_answer)

    interview.current_question_index += 1
    next_q = get_next_question(job, interview.current_question_index)
    if next_q is None:
        interview.status = models.InterviewStatus.COMPLETED

    db.add(interview)
    db.commit()
    db.refresh(interview)

    return {
        "answer": db_answer,
        "next_question": next_q,
        "interview_status": interview.status,
        "scoring": scoring,
    }


def generate_interview_summary(db: Session, interview: models.Interview) -> Dict:
    job = interview.job
    qa_list = []
    for ans in interview.answers:
        qa_list.append(
            {
                "question": ans.question.text,
                "answer": ans.answer_text,
                "score": ans.score,
                "competency_scores": ans.competency_scores or {},
            }
        )

    summary = summarise_interview(job.title, job.description, qa_list)
    return summary
