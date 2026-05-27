import requests
from bs4 import BeautifulSoup
import json, os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# URLs exactas de LinkedIn con Madrid (geoId=100994331), full-time, presencial+hibrido
SEARCHES = [
    {
        "label": "Account Manager Marketing",
        "url": "https://www.linkedin.com/jobs/search/?keywords=account%20manager%20marketing&geoId=100994331&f_TPR=r1800&f_WT=1%2C3&f_JT=F"
    },
    {
        "label": "Ejecutivo de Cuentas",
        "url": "https://www.linkedin.com/jobs/search/?keywords=ejecutivo%20de%20cuentas&geoId=100994331&f_TPR=r1800&f_WT=1%2C3&f_JT=F"
    },
    {
        "label": "Account Executive",
        "url": "https://www.linkedin.com/jobs/search/?keywords=account%20executive&geoId=100994331&f_TPR=r1800&f_WT=1%2C3&f_JT=F"
    },
    {
        "label": "Marketing Manager",
        "url": "https://www.linkedin.com/jobs/search/?keywords=marketing%20manager&geoId=100994331&f_TPR=r1800&f_WT=1%2C3&f_JT=F"
    },
    {
        "label": "Responsable de Marketing",
        "url": "https://www.linkedin.com/jobs/search/?keywords=responsable%20de%20marketing&geoId=100994331&f_TPR=r1800&f_WT=1%2C3&f_JT=F"
    },
    {
        "label": "Brand Manager",
        "url": "https://www.linkedin.com/jobs/search/?keywords=brand%20manager&geoId=100994331&f_TPR=r1800&f_WT=1%2C3&f_JT=F"
    },
    {
        "label": "Traffic Manager",
        "url": "https://www.linkedin.com/jobs/search/?keywords=traffic%20manager&geoId=100994331&f_TPR=r1800&f_WT=1%2C3&f_JT=F"
    },
    {
        "label": "Director de Cuentas",
        "url": "https://www.linkedin.com/jobs/search/?keywords=director%20de%20cuentas&geoId=100994331&f_TPR=r1800&f_WT=1%2C3&f_JT=F"
    },
    {
        "label": "Marketing Project Manager",
        "url": "https://www.linkedin.com/jobs/search/?keywords=marketing%20project%20manager&geoId=100994331&f_TPR=r1800&f_WT=1%2C3&f_JT=F"
    },
    {
        "label": "Marketing Account Executive",
        "url": "https://www.linkedin.com/jobs/search/?keywords=marketing%20account%20executive&geoId=100994331&f_TPR=r1800&f_WT=1%2C3&f_JT=F"
    },
]

# Palabras que si aparecen en el titulo = descartar
EXCLUDE_WORDS = [
    'comercial', 'sales representative', 'sdr', 'bdr',
    'software', 'developer', 'engineer', 'data analyst',
    'cloud', 'devops', 'it project', 'technical project',
    'salesforce', 'sap', 'erp', 'pricing', 'cos department',
    'electricidad', 'telecomunicaciones', 'seguridad',
    'accountant', 'contable', 'room division', 'jefe de centro',
    'postventa', 'intralogistica', 'intralogística',
    'junior accountant', 'finance', 'legal',
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

def is_relevant(title):
    t = title.lower()
    for word in EXCLUDE_WORDS:
        if word in t:
            return False
    return True

def get_jobs(search):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'es-ES,es;q=0.9',
    }
    try:
        r = requests.get(search['url'], headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        jobs = []
        for card in soup.find_all('div', class_='base-card'):
            job_id = card.get('data-entity-urn', '').split(':')[-1]
            title_el = card.find('h3', class_='base-search-card__title')
            company_el = card.find('h4', class_='base-search-card__subtitle')
            link_el = card.find('a', class_='base-card__full-link')
            if job_id and title_el:
                title = title_el.text.strip()
                if is_relevant(title):
                    jobs.append({
                        'id': job_id,
                        'title': title,
                        'company': company_el.text.strip() if company_el else 'N/A',
                        'url': link_el['href'] if link_el else '',
                        'label': search['label']
                    })
        return jobs
    except Exception as e:
        print(f"Error en {search['label']}: {e}")
        return []

def send_email_single(job):
    to = os.environ['EMAIL_TO']
    frm = os.environ['EMAIL_FROM']
    pwd = os.environ['EMAIL_PASSWORD']
    title = job['title']
    company = job['company']
    url = job['url']
    label = job['label']
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Nueva vacante: ' + title + ' - ' + company
    msg['From'] = frm
    msg['To'] = to
    body = (
        "<div style='font-family:sans-serif;max-width:600px;margin:0 auto'>"
        "<h2 style='color:#0077b5'>Nueva vacante en LinkedIn</h2>"
        "<div style='border:1px solid #ddd;border-radius:8px;padding:20px'>"
        "<h3 style='margin:0 0 8px'>" + title + "</h3>"
        "<p style='margin:4px 0;color:#555'>🏢 " + company + "</p>"
        "<p style='margin:4px 0;color:#888;font-size:13px'>🔍 " + label + "</p>"
        "<a href='" + url + "' style='display:inline-block;margin-top:16px;"
        "background:#0077b5;color:white;padding:10px 20px;"
        "text-decoration:none;border-radius:6px;font-weight:bold'>"
        "Ver vacante →</a>"
        "</div></div>"
    )
    msg.attach(MIMEText(body, 'html'))
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
        s.login(frm, pwd)
        s.sendmail(frm, to, msg.as_string())

def main():
    seen = load_seen()
    new_jobs = []
    for search in SEARCHES:
        for job in get_jobs(search):
            if job['id'] not in seen:
                new_jobs.append(job)
                seen.add(job['id'])
    print(f"Encontradas: {len(new_jobs)} vacantes nuevas")
    for job in new_jobs:
        try:
            send_email_single(job)
            print(f"Email enviado: {job['title']}")
        except Exception as e:
            print(f"Error enviando email: {e}")
    save_seen(seen)

if __name__ == "__main__":
    main()
