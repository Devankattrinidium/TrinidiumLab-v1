import argparse
import datetime
from emailer import EmailManager
from leads import LeadManager
from logger import Logger
from ai_helper import generate_email_subject_and_body
from followup_templates import followup_1, followup_2, followup_3, followup_4

followup_map = {2: followup_1, 4: followup_2, 5: followup_3, 6: followup_4}

def validate_lead(lead):
    return lead.get("email") and "@" in lead["email"]

def main(csv_path='leads.csv', daily_limit=200, delay=60, dry_run=False):
    leads = LeadManager.load(csv_path)
    email_manager = EmailManager()
    logger = Logger()
    sent_today = 0

    today = datetime.date.today()
    for lead in leads:
        if not validate_lead(lead):
            continue
        if lead.get("status") in ["replied", "completed"]:
            continue

        # Calculate days since first email
        try:
            first_email_date = datetime.datetime.strptime(lead["first_email_date"], "%Y-%m-%d").date()
        except Exception:
            first_email_date = None

        last_day = int(lead.get("last_sent_day", 0) or 0)
        days_since = (today - first_email_date).days if first_email_date else 0

        # Check for reply
        if email_manager.has_replied(lead["email"]):
            lead["status"] = "replied"
            continue

        # Main email logic
        if not lead.get("first_email_date"):
            if email_manager.already_sent(lead):
                continue
            # Generate and send main email
            try:
                ai_result = generate_email_subject_and_body(lead["name"], "")
                subject = ai_result["subject"]
                html = ai_result["body"]
                if not dry_run:
                    email_manager.send_email(lead, subject, html)
                    logger.log_sent(lead["email"], "Main Email")
                lead["first_email_date"] = today.strftime("%Y-%m-%d")
                lead["last_sent_day"] = "0"
                sent_today += 1
            except Exception as e:
                logger.log_error(lead["email"], str(e))
            continue

        # Follow-up logic (NO already_sent check here!)
        if days_since in followup_map and last_day < days_since:
            try:
                followup_html = followup_map[days_since](lead["name"])
                subject = f"{lead['name']}, still curious?"
                if not dry_run:
                    email_manager.send_email(lead, subject, followup_html)
                    logger.log_sent(lead["email"], f"Followup Day {days_since}")
                lead["last_sent_day"] = str(days_since)
                sent_today += 1
            except Exception as e:
                logger.log_error(lead["email"], str(e))

        if sent_today >= daily_limit:
            break

    LeadManager.save(leads, csv_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="leads.csv")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--delay", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(csv_path=args.csv, daily_limit=args.limit, delay=args.delay, dry_run=args.dry_run)