import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import os
import sys

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

client = OpenAI(api_key=OPENAI_API_KEY)
TARGET_URL = "https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    # 에러 원인이었던 parse_mode="Markdown" 부분을 제거하여 전송 안정성을 높였습니다.
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("✅ 텔레그램 전송 성공")
    except Exception as e:
        print(f"❌ 텔레그램 전송 실패: {e}")

def fetch_ppomppu_deals():
    # 사람처럼 보이도록 User-Agent 정보 강화
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": "https://www.ppomppu.co.kr/"
    }
    
    try:
        response = requests.get(TARGET_URL, headers=headers)
        response.raise_for_status()
        response.encoding = 'euc-kr' 
        soup = BeautifulSoup(response.text, 'html.parser')
        
        titles = []
        # 사이트 구조 변경을 대비하여 여러 태그 조합 시도
        items = soup.select('tr.list1, tr.list0, tr.baseList') 
        
        if not items:
            print("❌ 구조 변경됨: 게시글 목록 태그를 찾을 수 없습니다.")
            return None
            
        for item in items:
            title_element = item.select_one('font.list_title, a.baseList-title span')
            if title_element and title_element.text:
                title_text = title_element.text.strip()
                if title_text:
                     titles.append(title_text)
                     
        if not titles:
            print("❌ 제목 수집 실패: 게시글 목록은 찾았으나 제목 텍스트가 없습니다.")
            return None
            
        print(f"✅ 데이터 수집 완료: {len(titles)}개의 제목을 찾았습니다.")
        return "\n".join(titles[:20])
        
    except Exception as e:
        print(f"❌ 수집 오류 (네트워크/차단 등): {e}")
        return None

def analyze_and_summarize(data):
    if not data: 
        print("❌ LLM 분석 중단: 분석할 데이터가 없습니다.")
        return None
        
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
        print("✅ LLM 분석 성공")
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ LLM 분석 실패: {e}")
        return None

def run_agent
