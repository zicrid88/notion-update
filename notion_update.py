import requests
from datetime import datetime

# 🔹 Notion API 설정 (API 키 & 데이터베이스 ID 입력)
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")

# 🔹 Notion API 요청 헤더
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# 🔹 Notion 데이터베이스에서 모든 항목 가져오기
def get_database_items():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=HEADERS)
    
    if response.status_code == 200:
        return response.json().get("results", [])
    else:
        print(f"❌ 데이터 가져오기 실패: {response.status_code}, {response.text}")
        return []

# 🔹 날짜 추출을 안전하게 처리하는 함수
def extract_date_value(properties, property_name):
    """Notion properties에서 특정 date 타입 속성을 꺼내와 'YYYY-MM-DD' 문자열을 반환.
       값이 없거나 유형이 맞지 않으면 None 반환."""
    prop = properties.get(property_name)
    if not isinstance(prop, dict):
        return None  # 속성이 없거나 구조가 dict가 아니면 None

    date_info = prop.get("date")  # "date"라는 키를 가진 dict여야 함
    if not isinstance(date_info, dict):
        return None

    return date_info.get("start")  # 여기서도 None일 수 있으므로 .get 사용

# 🔹 진행률 계산 함수 + 이모지 변환
def calculate_progress(start_date, end_date):
    if not start_date or not end_date:
        return "🚨 날짜 없음"

    today_date_str = datetime.today().strftime("%Y-%m-%d")
    
    # 날짜 문자열을 datetime 객체로 변환
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        today_dt = datetime.strptime(today_date_str, "%Y-%m-%d")
    except ValueError:
        # 만약 형식이 맞지 않는다면 오류 표기
        return "🚨 날짜 형식 오류"

    total_days = (end_dt - start_dt).days
    passed_days = (today_dt - start_dt).days

    if total_days <= 0:
        return "🚨 오류"  # 시작일과 완료일이 잘못된 경우

    # 진행률 계산
    progress = round((passed_days / total_days) * 100, 1)

    # 10 이하인 경우 -> 10, 100 초과인 경우 -> 100
    if progress < 10:
        progress = 10
    elif progress > 100:
        progress = 100

    # 이모지 변환 (10단계)
    full_hearts = int(progress // 10)  # 예: 88.9%일 경우 8
    empty_hearts = 10 - full_hearts
    heart_emoji = "❤️" * full_hearts + "💛" * empty_hearts
    
    return f"{heart_emoji} {progress}%"

# 🔹 Notion 데이터 업데이트 함수
def update_progress():
    items = get_database_items()

    for item in items:
        page_id = item["id"]
        properties = item.get("properties", {})

        # 🔹 "제작 시작일" 값 추출
        start_date = extract_date_value(properties, "제작 시작일")
        # 🔹 "제작 완료" 값 추출
        end_date = extract_date_value(properties, "제작 완료")

        # 🔹 진행률 계산
        progress_display = calculate_progress(start_date, end_date)

        update_url = f"https://api.notion.com/v1/pages/{page_id}"
        update_data = {
            "properties": {
                "상품 제작 현황": {
                    "rich_text": [{"text": {"content": progress_display}}]
                }
            }
        }

        response = requests.patch(update_url, headers=HEADERS, json=update_data)
        if response.status_code == 200:
            print(f"✅ {page_id}: 상품 제작 현황 업데이트 완료 → {progress_display}")
        else:
            print(f"❌ 업데이트 실패: {response.status_code}, {response.text}")

# 🔹 실행
if __name__ == "__main__":
    update_progress()
