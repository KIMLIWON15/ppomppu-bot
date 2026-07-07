import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import os
import sys

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = "51555381" # 성환 님 실제 챗 ID

client = OpenAI(api_key=OPENAI_API_KEY)
TARGET_URL = "https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    # 하이퍼링크 작동을 위해 parse_mode를 HTML로 설정
    payload = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": text, 
        "parse_mode": "HTML",
        "disable_web_page_preview": False  # 링크 미리보기 켜기
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"❌ [텔레그램 에러]: {response.text}")
        response.raise_for_status()
        print("✅ 텔레그램 전송 성공")
    except Exception as e:
        print(f"❌ 텔레그램 전송 실패: {e}")

def fetch_ppomppu_deals():
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
        
        deals = []
        items = soup.select('tr.list1, tr.list0, tr.baseList') 
        
        if not items:
            return None
            
        for item in items:
            title_element = item.select_one('font.list_title, a.baseList-title span')
            if title_element and title_element.text:
                title_text = title_element.text.strip()
                
                # 링크 주소 추출
                link = ""
                parent_a = title_element.find_parent('a')
                if parent_a and parent_a.has_attr('href'):
                    link_href = parent_a['href']
                    link = "https://www.ppomppu.co.kr/zboard/" + link_href

                if title_text and link:
                    # AI가 제목과 링크를 매칭하기 쉽게 데이터 구성
                    deals.append(f"제목: {title_text} | 링크: {link}")
                     
        if not deals:
            return None
            
        return "\n".join(deals[:25]) # 넉넉하게 25개 전달
        
    except Exception as e:
        print(f"❌ 수집 오류: {e}")
        return None

def analyze_and_summarize(data):
    if not data: return None
        
    # AI에게 HTML 링크 태그를 직접 작성하도록 지시
    prompt = f"""다음 뽐뿌 핫딜 목록에서 베스트 핫딜 5개를 골라줘.

지시사항:
1. 각 항목은 반드시 HTML 하이퍼링크 형식인 <a href="링크">제목</a> 형식으로 작성해.
2. 제목에는 [쇼핑몰명]과 [가격] 정보가 포함되게 해.
3. 별도의 주소창(URL)은 텍스트로 노출하지 마.
4. 마크다운 기호(*, _, # 등)는 절대 사용하지 마.

출력 예시:
1. <a href="http://주소">쇼핑몰이름 / 상품명 / 가격</a>
2. <a href="http://주소">쇼핑몰이름 / 상품명 / 가격</a>

데이터:
{data}"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": "너는 핫딜 요약 전문가야. 오직 HTML <a> 태그를 이용해 링크를 연결한 제목만 출력해."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ LLM 분석 실패: {e}")
        return None

def run_agent():
    print("--- 핫딜 수집 및 요약 시작 ---")
    scraped_data = fetch_ppomppu_deals()
    if scraped_data:
        summary_msg = analyze_and_summarize(scraped_data)
        if summary_msg:
            send_telegram_message(summary_msg)
    print("--- 작업 완료 ---")

if __name__ == "__main__":
    run_agent()
    sys.stdout.flush()
