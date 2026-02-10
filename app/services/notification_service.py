from app.services.email_service import email_service
from app.config import settings


def send_candidate_invite(candidate_email: str, invite_token: str, job_title: str):
    link = f"{settings.FRONTEND_BASE_URL}/start?token={invite_token}"

    subject = f"Interview Invitation – {job_title}"

    html = f"""
    <h2>Interview Invitation</h2>
    <p>You have been invited to an interview for <b>{job_title}</b>.</p>
    <p>Click the button below to start your interview:</p>
    <p>
        <a href="{link}" style="padding:12px 20px;background:#2563eb;color:white;text-decoration:none;border-radius:6px;">
            Start Interview
        </a>
    </p>
    <p>If the button doesn't work, copy this link:</p>
    <p>{link}</p>
    """

    email_service.send_email(candidate_email, subject, html)


def notify_admin_interview_completed(candidate_email: str, job_title: str):
    if not settings.ADMIN_NOTIFY_EMAILS:
        print("No ADMIN_NOTIFY_EMAILS configured")
        return

    subject = "Interview Completed"

    html = f"""
    <h2>Interview Completed</h2>
    <p>Candidate <b>{candidate_email}</b> has completed the interview for:</p>
    <p><b>{job_title}</b></p>
    """

    admin_list = [
        e.strip()
        for e in settings.ADMIN_NOTIFY_EMAILS.split(",")
        if e.strip()
    ]

    for admin_email in admin_list:
        email_service.send_email(admin_email, subject, html)
