import streamlit as st
import pandas as pd
import datetime

# 1. 페이지 기본 설정 (와이드 레이아웃 적용)
st.set_page_config(
    page_title="제조 품질 현황 대시보드",
    page_icon="🏭",
    layout="wide"
)

# 2. 제목 및 부제
st.title("제조 품질 현황 대시보드")
st.markdown("**AI 비전검사 PoC 준비를 위한 품질 데이터 모니터링**")
st.markdown("---")

# 3. 기본 샘플 데이터 생성 함수 (CSV가 없을 경우 사용)
@st.cache_data
def load_sample_data():
    data = {
        "inspection_date": [
            "2026-10-01", "2026-10-01", "2026-10-02", "2026-10-02",
            "2026-10-03", "2026-10-03", "2026-10-04", "2026-10-04",
            "2026-10-05", "2026-10-05", "2026-10-06", "2026-10-06"
        ],
        "product_id": [
            "P001", "P002", "P003", "P004", 
            "P005", "P006", "P007", "P008", 
            "P009", "P010", "P011", "P012"
        ],
        "result": [
            "OK", "NG", "OK", "NG", 
            "OK", "OK", "NG", "OK", 
            "OK", "NG", "OK", "OK"
        ],
        "defect_type": [
            "None", "Scratch", "None", "Crack", 
            "None", "None", "Dent", "None", 
            "None", "Scratch", "None", "None"
        ],
        "confidence": [
            0.98, 0.91, 0.96, 0.88, 
            0.99, 0.95, 0.82, 0.97, 
            0.94, 0.89, 0.98, 0.96
        ]
    }
    return pd.DataFrame(data)

# 4. 사이드바 구성 (파일 업로드 및 필터)
st.sidebar.header("🔧 데이터 및 필터 설정")

uploaded_file = st.sidebar.file_uploader("CSV 파일 업로드", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.sidebar.success("성공적으로 파일을 업로드했습니다!")
    except Exception as e:
        st.sidebar.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        df = load_sample_data()
else:
    st.sidebar.info("업로드된 파일이 없어 기본 샘플 데이터를 사용합니다.")
    df = load_sample_data()

# 날짜 형식 변환
df['inspection_date'] = pd.to_datetime(df['inspection_date']).dt.date

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 데이터 필터")

# 날짜 필터
min_date = df['inspection_date'].min()
max_date = df['inspection_date'].max()
date_range = st.sidebar.date_input("검사일자 선택", [min_date, max_date])

# 제품 필터
products = ["전체"] + list(df['product_id'].unique())
selected_product = st.sidebar.selectbox("제품 선택", products)

# 검사 결과 필터
results = ["전체"] + list(df['result'].unique())
selected_result = st.sidebar.selectbox("검사 결과 선택", results)

# 5. 필터 적용 로직
filtered_df = df.copy()

if isinstance(date_range, list) and len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df['inspection_date'] >= date_range[0]) & 
        (filtered_df['inspection_date'] <= date_range[1])
    ]

if selected_product != "전체":
    filtered_df = filtered_df[filtered_df['product_id'] == selected_product]

if selected_result != "전체":
    filtered_df = filtered_df[filtered_df['result'] == selected_result]


# 6. 상단 KPI 카드 영역
total_count = len(filtered_df)
ok_count = len(filtered_df[filtered_df['result'] == 'OK'])
ng_count = len(filtered_df[filtered_df['result'] == 'NG'])
defect_rate = (ng_count / total_count * 100) if total_count > 0 else 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("전체 검사 건수", f"{total_count} 건")
col2.metric("정상 (OK)", f"{ok_count} 건", delta=f"{ok_count/total_count*100:.1f}%" if total_count > 0 else "0%")
col3.metric("불량 (NG)", f"{ng_count} 건", delta=f"-{ng_count/total_count*100:.1f}%" if total_count > 0 else "0%", delta_color="inverse")
col4.metric("불량률", f"{defect_rate:.2f} %")

st.markdown("---")


# 7. 중단 그래프 영역 (2열 레이아웃)
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("📅 날짜별 검사 현황 (OK / NG)")
    if not filtered_df.empty:
        # 날짜별, 결과별 집계 데이터 생성
        date_trend = filtered_df.groupby(['inspection_date', 'result']).size().unstack(fill_value=0)
        st.line_chart(date_trend)
    else:
        st.warning("표시할 데이터가 없습니다.")

with chart_col2:
    st.subheader("📊 불량 유형별 건수")
    # NG 데이터 중 불량 유형 집계 (None 제외)
    ng_df = filtered_df[filtered_df['result'] == 'NG']
    if not ng_df.empty:
        defect_counts = ng_df['defect_type'].value_counts()
        st.bar_chart(defect_counts)
    else:
        st.info("선택된 조건 내에 불량(NG) 데이터가 없습니다.")

st.markdown("---")


# 8. 하단 최근 검사 데이터 테이블 영역
st.subheader("📋 최근 검사 결과 (최대 10건)")
if not filtered_df.empty:
    # 최신 날짜 순으로 정렬 후 상단 10건 표시
    display_df = filtered_df.sort_values(by='inspection_date', ascending=False).head(10)
    st.dataframe(display_df, use_container_width=True)
else:
    st.info("표시할 데이터가 없습니다.")