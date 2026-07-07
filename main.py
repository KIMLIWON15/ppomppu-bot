import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import os

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

client = OpenAI(api_key=OPENAI_API_KEY)
TARGET_URL = "https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"텔레그램 전송 실패: {e}")

def fetch_ppomppu_deals():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(TARGET_URL, headers=headers)
        response.encoding = 'euc-kr' 
        soup = BeautifulSoup(response.text, 'html.parser')

        titles = []
        for item in soup.select('tr.list1, tr.list0'):
            title_element = item.select_one('font.list_title')
            if title_element and title_element.text:
                titles.append(title_element.text.strip())
        return "\n".join(titles[:20])
    except Exception as e:
        print(f"수집 오류: {e}")
        return None

def analyze_and_summarize(data):
    if not data: return None
    prompt = f"다음 뽐뿌 게시판 제목 중 베스트 핫딜 3개를 골라 텔레그램 메시지용으로 예쁘게 요약해.\n\n{data}"
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": "너는 쇼핑 핫딜 비서야."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM 분석 실패: {e}")
        return None

def run_agent():
    scraped_data = fetch_ppomppu_deals()
    if scraped_data:
        summary_msg = analyze_and_summarize(scraped_data)
        if summary_msg:
            send_telegram_message(summary_msg)
            print("작업 완료 및 메시지 전송 성공")

if __name__ == "__main__":
    run_agent()
