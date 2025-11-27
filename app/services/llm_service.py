from typing import Dict, List
from openai import OpenAI
from ..config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def build_scoring_prompt(question: str, answer: str, competencies: List[str]) -> str:
    comp_str = ", ".join(competencies) if competencies else "overall quality"
    return f"""
You are an expert recruiter. Score the candidate's answer to the interview question.

Question:
\"\"\"{question}\"\"\"

Candidate answer:
\"\"\"{answer}\"\"\"

You should:
- Evaluate from 1 to 5 (5 = excellent, 1 = very poor).
- Evaluate the following competencies: {comp_str}.
- Provide short, constructive feedback.

Return ONLY valid JSON with this structure:
{{
  "overall_score": <int 1-5>,
  "competency_scores": {{
    "<competency_name>": <int 1-5>,
    ...
  }},
  "feedback": "<short textual feedback>"
}}
"""


def score_answer(question: str, answer: str, competencies: List[str]) -> Dict:
    prompt = build_scoring_prompt(question, answer, competencies)

    # Use Chat Completions API instead of Responses API
    resp = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )

    content = resp.choices[0].message.content
    import json

    data = json.loads(content)
    return data


def build_summary_prompt(job_title: str, job_description: str, qa_list: List[Dict]) -> str:
    """
    qa_list: [{"question": "...", "answer": "...", "score": int, "competency_scores": {...}}]
    """
    qa_str = ""
    for i, qa in enumerate(qa_list, start=1):
        qa_str += f"""
Q{i}: {qa['question']}
A{i}: {qa['answer']}
Score: {qa.get('score')}
Competency scores: {qa.get('competency_scores')}
"""

    return f"""
You are an expert recruiter summarising a structured interview.

Job title: {job_title}

Job description:
{job_description}

Interview transcript:
{qa_str}

Task:
- Provide an overall recommendation from this set: ["Strong Hire","Hire","Leaning Hire","Neutral","Leaning No","No Hire"].
- Provide a short overall commentary (3-6 sentences).
- Provide average numeric score across questions.
- Provide average score per competency.

Return ONLY valid JSON:
{{
  "recommendation": "<one of the allowed values>",
  "overall_commentary": "<text>",
  "average_score": <float>,
  "competency_summary": {{
    "<competency>": <float>,
    ...
  }}
}}
"""


def summarise_interview(job_title: str, job_description: str, qa_list: List[Dict]) -> Dict:
    prompt = build_summary_prompt(job_title, job_description, qa_list)

    resp = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )

    content = resp.choices[0].message.content
    import json

    return json.loads(content)
