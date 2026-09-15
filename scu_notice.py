import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os

# =========配置区（从环境变量读取，不要硬写账号密码）========
URL = "https://jwc.scu.edu.cn/tzgg.htm"
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PWD = os.getenv("SMTP_PWD")
TO_EMAIL = os.getenv("TO_EMAIL")
# =========================================================

def get_last_week_range():
    """获取上周一到上周日时间范围"""
    today = datetime.now()
    offset = today.weekday() + 7
    last_sunday = today - timedelta(days=offset)
    last_monday = last_sunday - timedelta(days=6)
    return last_monday.date(), last_sunday.date()

def fetch_scu_notices():
    headers = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    resp = requests.get(URL, headers=headers, timeout=15)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.select("li")
    all_notices = []
    for li in items:
        text = li.get_text(strip=True, separator=" ")
        parts = text.split()
        if len(parts)>=3:
            try:
                mmdd = parts[0]
                year = parts[1]
                title = " ".join(parts[2:])
                date_str = f"{year}-{mmdd}"
                pub_date = datetime.strptime(date_str, "%Y-%m/%d").date()
                all_notices.append({"date":pub_date,"title":title})
            except Exception:
                continue
    return all_notices

def filter_last_week(notices):
    start,end = get_last_week_range()
    return [n for n in notices if start <= n["date"] <= end]

def send_mail(body_text):
    msg = MIMEText(body_text,"plain","utf-8")
    msg["Subject"] = "【川大教务处公告周报】上周通知汇总"
    msg["From"] = SMTP_USER
    msg["To"] = TO_EMAIL
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as s:
        s.login(SMTP_USER, SMTP_PWD)
        s.send_message(msg)

if __name__ == "__main__":
    notices = fetch_scu_notices()
    week_notices = filter_last_week(notices)
    if not week_notices:
        body = "上周教务处无新增公告。"
    else:
        body = "\n".join([f'{n["date"]}｜{n["title"]}' for n in week_notices])
    print(body)
    send_mail(body)
