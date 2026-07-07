import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import os
import sys

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = "51555381" 

client = OpenAI(api_key=OPENAI_API_KEY)
TARGET_URL = "https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": text, 
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"❌ [텔레그램 상세 에러]: {response.text}")
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
                
                link = ""
                parent_a = title_element.find_parent('a')
                if parent_a and parent_a.has_attr('href'):
                    link_href = parent_a['href']
                    link = "https://www.ppomppu.co.kr/zboard/" + link_href

                if title_text and link:
                    deals.append(f"제목: {title_text}\n링크: {link}")
                     
        if not deals:
            return None
            
        return "\n\n".join(deals[:50])
        
    except Exception as e:
        print(f"❌ 수집 오류: {e}")
        return None

def analyze_and_summarize(data):
    if not data: return None
        
    # 각 항목 사이에 빈 줄을 넣으라는 5번 조건과 예시가 추가되었습니다.
    prompt = f"""다음 뽐뿌 핫딜 목록에서 가장 추천할 만한 베스트 핫딜 10개를 골라줘.

조건:
1. 원본 데이터의 제목 형태([쇼핑몰] 상품명 및 가격 정보)를 임의로 바꾸거나 요약하지 말고 100% 그대로 유지해.
2. 제목 텍스트 전체에 HTML 하이퍼링크(<a href="링크">제목</a>)를 걸어줘.
3. 별도의 주소창(URL) 텍스트는 아래에 노출하지 마.
4. 마크다운 기호(*, _, # 등)는 절대 사용하지 마.
5. 가독성을 위해 각 번호 항목 사이에는 반드시 한 줄(빈 줄)을 띄워줘.

출력 예시:
1. <a href="https://www.ppomppu.co.kr/...">[G마켓]남여공용 네파 경량 아쿠아 워터슈즈 (14,010원/3,000원)</a>

2. <a href="https://www.ppomppu.co.kr/...">[네이버]SRC 스위트 망고스틱 60g 50개 (36,900원/3,500원)</a>

데이터:
{data}"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": "너는 쇼핑 핫딜 비서야. 지시한 양식을 반드시 지켜."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ LLM 분석 실패: {e}")
        return None

def run_agent():
    scraped_data = fetch_ppomppu_deals()
    if scraped_data:
        summary_msg = analyze_and_summarize(scraped_data)
        if summary_msg:
            send_telegram_message(summary_msg)

if __name__ == "__main__":
    run_agent()
    sys.stdout.flush()
