import requests
from bs4 import BeautifulSoup
import json, os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SEARCHES = [
    {"keywords": "marketing manager", "location": "Madrid"},
    {"keywords": "brand manager", "location": "Madrid"},
    {"keywords": "account manager marketing", "location": "Madrid"},
    {"keywords": "project manager marketing", "location": "Madrid"},
    {"keywords": "marketing director", "location": "Madrid"},
]

SEEN_FILE = "seen_jobs.json"

def load_seen():
    try:
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    except:
        return set()

def save_seen(seen):
    with open(SEEN_FILE, 'w') as f:
        json.dump(list(seen), f)

def get_jobs(keywords, location):
    kw = keywords.replace(' ', '%20')
    url = f"https://www.linkedin.com/jobs/search/?keywords={kw}&location={location}&f_TPR=r1800"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'es-ES,es;q=0.9',
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        jobs = []
        for card in soup.find_all('div', class_='base-card'):
            job_id = card.get('data-entity-urn', '').split(':')[-1]
            title = card.find('h3', class_='base-search-card__title')
            company = card.find('h4', class_='base-search-card__subtitle')
            link = card.find('a', class_='base-card__full-link')
            if job_id and title:
                jobs.append({
                    'id': job_id,
                    'title': title.text.strip(),
                    'company': company.text.strip() if company else 'N/A',
                    'url': link['href'] if link else '',
                    'search': keywords
                })
        return jobs
    except Exception as e:
        print(f"Error en {keywords}: {e}")
        return []

def send_email(jobs):
    to = os.environ['EMAIL_TO']
    frm = os.environ['EMAIL_FROM']
    pwd = os.environ['EMAIL_PASSWORD']
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Nueva vacante en LinkedIn Madrid"
    msg['From'] = frm
    msg['To'] = to
    body = "<h2 style='font-family:sans-serif'>Nuevas vacantes en LinkedIn</h2>"
    for j in jobs:
        body += f"<div style='border:1px solid #ddd;border-radius:8px;padding:16px;margin:12px 0;font-family:sans-serif'><h3><a href='{j["url"]}'>{j["title"]}</a></h3><p>{j["company"]} | {j["search"]}</p><a href='{j["url"]}' style='background:#0077b5;color:white;padding:8px 16px;text-decoration:none;border-radius:6px;display:inline-block'>Ver vacante</a></div>"
    msg.attach(MIMEText(body, 'html'))
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
        s.login(frm, pwd)
        s.sendmail(frm, to, msg.as_string())

def main():
    seen = load_seen()
    new_jobs = []
    for s in SEARCHES:
        for job in get_jobs(s['keywords'], s['location']):
            if job['id'] not in seen:
                new_jobs.append(job)
                seen.add(job['id'])
    if new_jobs:
        send_email(new_jobs)
    save_seen(seen)

if __name__ == "__main__":
    main()
