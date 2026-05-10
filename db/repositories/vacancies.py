import json
from db.connection import get_connection

def save_vacancy(vacancy: dict):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO vacancies (
            job_id, company, country, salary_amount, salary_currency,
            remote, language, visa_sponsorship, date_published,
            url, extracted_json, raw_json, embedding
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        vacancy.get("job_id"),
        vacancy.get("company"),
        vacancy.get("country"),
        vacancy.get("salary_amount"),
        vacancy.get("salary_currency"),
        vacancy.get("remote"),
        vacancy.get("language"),
        vacancy.get("visa_sponsorship"),
        vacancy.get("date_published"),
        vacancy.get("url"),
        json.dumps(vacancy.get("extracted_json", {})),
        json.dumps(vacancy.get("raw_json", {})),
        vacancy.get("embedding")
    ))

    conn.commit()
    cur.close()
    conn.close()

def vacancy_exists(job_id: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM vacancies WHERE job_id = %s", (job_id,))
    exists = cur.fetchone() is not None

    cur.close()
    conn.close()
    return exists

def get_vacancies_by_role(role_id: int) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM vacancies WHERE role_id = %s
    """, (role_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows