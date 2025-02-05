from sqlalchemy.orm import Session
from models import Team, Result
import smtplib
from email.mime.text import MIMEText

def calculate_team_rating(db: Session, team_id: int):
    results = db.query(Result).filter(Result.team_id == team_id).all()
    total_score = sum(result.score for result in results)
    team = db.query(Team).filter(Team.id == team_id).first()
    team.rating = total_score
    db.commit()

def send_email(to_email: str, subject: str, message: str):
    sender_email = "your_email@example.com"
    sender_password = "your_password"

    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    with smtplib.SMTP("smtp.example.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())