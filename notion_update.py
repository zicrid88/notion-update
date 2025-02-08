import os
import requests
from datetime import datetime

# 🔹 Notion API 설정 (API 키 & 데이터베이스 ID 환경 변수에서 가져오기)
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
    """Notion properties에서 특정 date 타입 속성을 꺼내와 'YYYY-MM-DD' 혹은 'YYYY-MM-DDTHH:MM:SS' 문자열을 반환.
       값이 없거나 유형이 맞지 않으면 None 반환."""
    prop = properties.get(property_name)
    if not isinstance(prop, dict):
        return None  # 속성이 없거나 구조가 dict가 아니면 None

    date_info = prop.get("date")  # "date"라는 키를 가진 dict여야 함
    if not isinstance(date_info, dict):
        return None

    return date_info.get("start")  # 여기서도 None일 수 있으므로 .get 사용

# 🔹 진행률 계산 함수 (시간 단위)
def calculate_progress(start_date, end_date):
    """start_date, end_date가 'YYYY-MM-DD' 또는 'YYYY-MM-DDTHH:MM:SS' 형태라고 가정하고,
       시간 단위로 진행률을 계산합니다."""
    if not start_date or not end_date:
        return "    "

    # 지금 시각(오늘 날짜+시간)
    now_dt = datetime.now()

    # 1) 먼저 ISO 8601(YYYY-MM-DDTHH:MM:SS) 형태로 파싱 시도
    # 2) 안 되면 'YYYY-MM-DD' 형태로도 파싱해본다.
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
    except ValueError:
        # 만약 'YYYY-MM-DDTHH:MM:SS'가 아니라면 'YYYY-MM-DD'로 다시 시도
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return "🚨 날짜 형식 오류"

    # 전체 기간(시간)과 지난 기간(시간) 계산
    total_hours = (end_dt - start_dt).total_seconds() / 3600
    passed_hours = (now_dt - start_dt).total_seconds() / 3600

    if total_hours <= 0:
        return "🚨 오류"  # 시작일과 완료일이 잘못된 경우 (종료가 시작보다 빠름 등)

    # 진행률 계산 (시간 단위)
    progress = round((passed_hours / total_hours) * 100, 0)

    # 최소 10%, 최대 100%로 고정
    if progress < 10:
        progress = 10
    elif progress > 100:
        progress = 100

    # 이모지 변환 (10단계)
    full_hearts = int(progress // 10)
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
