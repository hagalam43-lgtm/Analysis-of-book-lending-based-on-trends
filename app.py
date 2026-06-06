import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def load_data(uploaded_file, start_row):
    """
    업로드된 CSV 파일을 지정된 시작 행부터 읽어오는 함수 (인코딩: UTF-8)
    """
    skip_lines = max(0, start_row - 1)
    try:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, skiprows=skip_lines, encoding='utf-8')
        return df
    except Exception as e:
        st.error(f"{uploaded_file.name} 파일을 읽는 중 오류가 발생했습니다: {e}")
        return None


def filter_books(df, mode):
    """
    선택된 모드(AI 또는 주식)에 따라 B 열(2번째 컬럼)에서 키워드를 필터링하는 함수
    """
    if df is None or df.shape[1] < 2:
        return pd.DataFrame()

    if mode == "AI 도서 추출":
        keywords = [
            '인공지능', 'AI', '챗GPT', 'ChatGPT', 'GPT',
            '머신러닝', '딥러닝', '생성형 AI', '4차 산업혁명', 'LLM'
        ]
    else:
        keywords = [
            '주식', '증권', '주가', '투자법', '재테크',
            '매매', '단타', '차트', '가치투자', '공매도',
            '배당주', '해외주식', '미국주식', 'ETF', '공모주'
        ]

    b_col = df.columns[1]
    pattern = '|'.join(keywords)
    filtered_df = df[df[b_col].astype(str).str.contains(pattern, case=False, na=False)]

    return filtered_df


def calculate_sum(df):
    """
    J 열(10번째 컬럼)의 합계를 계산하는 함수
    """
    if df is None or df.empty or df.shape[1] < 10:
        return 0

    j_col = df.columns[9]
    numeric_values = pd.to_numeric(df[j_col], errors='coerce').fillna(0)
    return float(numeric_values.sum())


# 메인 UI 설정
st.title("도서 데이터 다중 추출 및 통계 프로그램")

# 사이드바 설정 (라디오 버튼 및 시작 행)
with st.sidebar:
    st.header("설정 및 옵션")
    program_mode = st.radio("분석 모드 선택", ["AI 도서 추출", "주식 도서 추출"])
    start_row = st.number_input("데이터 시작 행 지정", min_value=1, value=14, step=1)

# 메인 화면 파일 업로드 (다중 파일)
uploaded_files = st.file_uploader("월별 CSV 파일들을 업로드하세요.", type=["csv"], accept_multiple_files=True)

# 세션 상태 초기화 (라디오 버튼 이동 시 데이터 유지)
if "file_data_cache" not in st.session_state:
    st.session_state.file_data_cache = {}

if uploaded_files:
    for uploaded_file in uploaded_files:
        if uploaded_file.name not in st.session_state.file_data_cache:
            df = load_data(uploaded_file, start_row)
            if df is not None:
                st.session_state.file_data_cache[uploaded_file.name] = df
else:
    st.session_state.file_data_cache = {}

# 그래프 및 통계를 위한 리스트
stats_data = []

if st.session_state.file_data_cache:
    st.header(f"📊 {program_mode} 분석 결과")

    for file_name, df in st.session_state.file_data_cache.items():
        filtered_df = filter_books(df, program_mode)
        total_sum = calculate_sum(filtered_df)
        row_count = len(filtered_df)

        stats_data.append({
            "파일명": file_name,
            "J열 합계": total_sum,
            "추출 건수": row_count
        })

        st.markdown(f"---")
        st.subheader(f"파일: {file_name}")
        st.write(f"추출된 데이터 건수: {row_count} 건")
        st.dataframe(filtered_df)
        st.write(f"해당 파일 J열 합계: {total_sum}")

    # Plotly를 이용한 다중 축 복합 차트 생성 (막대그래프 + 추세선)
    if stats_data:
        st.markdown("---")
        st.subheader(f"📈 {program_mode} 월별 통계 및 추세선 그래프")

        chart_df = pd.DataFrame(stats_data)

        fig = go.Figure()

        # 1. J열 합계 막대그래프 추가 (기본 왼쪽 y축)
        fig.add_trace(go.Bar(
            x=chart_df["파일명"],
            y=chart_df["J열 합계"],
            name="J열 합계 (막대)",
            marker_color="rgb(31, 119, 180)",
            yaxis="y1"
        ))

        # 2. 추출 건수 추세선 추가 (우측 보조 y축 사용)
        fig.add_trace(go.Scatter(
            x=chart_df["파일명"],
            y=chart_df["추출 건수"],
            name="추출 건수 (추세선)",
            mode="lines+markers",
            line=dict(color="rgb(255, 127, 14)", width=3),
            yaxis="y2"
        ))

        # 레이아웃 설정 (최신 Plotly title 표준 가이드 반영)
        fig.update_layout(
            xaxis=dict(title="파일명"),
            yaxis=dict(
                title=dict(
                    text="J열 합계",
                    font=dict(color="rgb(31, 119, 180)")
                ),
                tickfont=dict(color="rgb(31, 119, 180)")
            ),
            yaxis2=dict(
                title=dict(
                    text="추출 건수 (행의 수)",
                    font=dict(color="rgb(255, 127, 14)")
                ),
                tickfont=dict(color="rgb(255, 127, 14)"),
                overlaying="y",
                side="right"
            ),
            legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.5)"),
            margin=dict(l=40, r=40, t=40, b=40),
            hovermode="x unified"
        )

        # Streamlit 화면에 Plotly 차트 출력
        st.plotly_chart(fig, use_container_width=True)
