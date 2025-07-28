import csv

class LeadManager:
    FIELDNAMES = ['name', 'email', 'first_email_date', 'last_sent_day', 'status']

    @staticmethod
    def load(path='leads.csv'):
        leads = []
        try:
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Fill missing fields with empty string
                    for field in LeadManager.FIELDNAMES:
                        if field not in row or row[field] is None:
                            row[field] = ''
                    leads.append(row)
        except FileNotFoundError:
            pass
        return leads

    @staticmethod
    def save(leads, path='leads.csv'):
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=LeadManager.FIELDNAMES)
            writer.writeheader()
            for lead in leads:
                writer.writerow(lead)