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
    선택된 모드에 따라 B 열(2번째 컬럼)에서 키워드를 필터링하는 함수
    """
    if df is None or df.shape[1] < 2:
        return pd.DataFrame()

    if mode == "AI 도서 추출":
        keywords = ['인공지능', 'AI', '챗GPT', 'ChatGPT', 'GPT', '머신러닝', '딥러닝', '생성형 AI', '4차 산업혁명', 'LLM']
    elif mode == "주식 도서 추출":
        keywords = ['주식', '증권', '주가', '투자법', '재테크', '매매', '단타', '차트', '가치투자', '공매도', '배당주', '해외주식', '미국주식', 'ETF',
                    '공모주']
    elif mode == "정치 도서 추출":
        keywords = [
            '정치', '민주주의', '공화정', '선거', '투표', '정당', '국회', '대통령', '정부', '권력',
            '보수', '진보', '좌파', '우파', '자유주의', '사회주의', '공산주의', '포퓰리즘', '외교',
            '국제정세', '지정학', '정책', '시민사회', '행정', '탄핵', '국무', '여당', '야당', '총선',
            '대선', '지선', '국회의원', '정치인', '의회', '법안', '공약', '이데올로기', '국제정치', '외교관', '계엄령', '계엄'
        ]
    elif mode == "전쟁 도서 추출":
        keywords = [
            '전쟁', '전투', '전술', '전략', '군사', '국방', '밀리터리', '무기', '군대', '장군',
            '군인', '병법', '징집', '파병', '테러', '분쟁', '용병', '사령관', '장교', '병사',
            '세계대전', '한국전쟁', '6·25', '내전', '침공', '함락', '점령',
            '평화협정', '종전', '휴전', '정전',
            '핵무기', '미사일', '폭격', '공습', '함대', '전함', '전차', '방공', '화력', '지휘관', '작전', '참호', '선전포고', '종군', '포로', '학살', '전사자'
        ]
    else:
        keywords = []

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

# 모든 데이터를 공통으로 관리할 글로벌 파일 세션 캐시 초기화
if "shared_file_cache" not in st.session_state:
    st.session_state.shared_file_cache = {}

# 사이드바 설정 (라디오버튼, 시작행 설정 및 공통 파일 업로더 통합)
with st.sidebar:
    st.header("설정 및 옵션")
    program_mode = st.radio(
        "분석 모드 선택",
        ["AI 도서 추출", "주식 도서 추출", "정치 도서 추출", "전쟁 도서 추출"]
    )
    start_row = st.number_input("데이터 시작 행 지정", min_value=1, value=14, step=1)

    st.markdown("---")
    # 파일 업로더를 사이드바로 이동시켜 모든 라디오 버튼이 동일한 파일을 공유하도록 세팅
    uploaded_files = st.file_uploader(
        "📅 월별 CSV 파일들을 업로드하세요.",
        type=["csv"],
        accept_multiple_files=True,
        key="shared_uploader"
    )

# 업로드된 파일이 존재하면 공통 캐시에 파싱 후 저장 (라디오 버튼 이동 시에도 증발하지 않음)
if uploaded_files:
    # 현재 업로드된 파일의 이름 목록 만들기
    current_uploaded_names = [f.name for f in uploaded_files]

    # 1. 새로 추가된 파일이 있다면 캐시에 로드
    for uploaded_file in uploaded_files:
        if uploaded_file.name not in st.session_state.shared_file_cache:
            df = load_data(uploaded_file, start_row)
            if df is not None:
                st.session_state.shared_file_cache[uploaded_file.name] = df

    # 2. 업로더에서 유저가 X를 눌러 삭제한 파일이 있다면 캐시에서도 제거
    for cached_name in list(st.session_state.shared_file_cache.keys()):
        if cached_name not in current_uploaded_names:
            del st.session_state.shared_file_cache[cached_name]
else:
    # 업로드된 파일이 완전히 비었다면 캐시 초기화
    st.session_state.shared_file_cache = {}

# 그래프 및 통합 통계를 구성하기 위한 리스트
stats_data = []

# 공통 캐시에 데이터가 존재할 때 현재 선택된 모드에 맞춰 실시간 필터링 및 화면 렌더링
if st.session_state.shared_file_cache:
    st.header(f"📊 {program_mode} 분석 결과")

    for file_name, df in st.session_state.shared_file_cache.items():
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

    # Plotly 이중 축 그래프 (막대그래프 + 추출 건수 추세선) 동일 적용
    if stats_data:
        st.markdown("---")
        st.subheader(f"📈 {program_mode} 월별 통계 및 추세선 그래프")

        chart_df = pd.DataFrame(stats_data)
        fig = go.Figure()

        # 1. J열 합계 막대그래프 (왼쪽 기본 Y축)
        fig.add_trace(go.Bar(
            x=chart_df["파일명"],
            y=chart_df["J열 합계"],
            name="J열 합계 (막대)",
            marker_color="rgb(31, 119, 180)",
            yaxis="y1"
        ))

        # 2. 추출 행 수 기반 추세선 (오른쪽 보조 Y축)
        fig.add_trace(go.Scatter(
            x=chart_df["파일명"],
            y=chart_df["추출 건수"],
            name="추출 건수 (추세선)",
            mode="lines+markers",
            line=dict(color="rgb(255, 127, 14)", width=3),
            yaxis="y2"
        ))

        # 레이아웃 세팅
        fig.update_layout(
            xaxis=dict(title="파일명"),
            yaxis=dict(
                title=dict(text="J열 합계", font=dict(color="rgb(31, 119, 180)")),
                tickfont=dict(color="rgb(31, 119, 180)")
            ),
            yaxis2=dict(
                title=dict(text="추출 건수 (행의 수)", font=dict(color="rgb(255, 127, 14)")),
                tickfont=dict(color="rgb(255, 127, 14)"),
                overlaying="y",
                side="right"
            ),
            legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.5)"),
            margin=dict(l=40, r=40, t=40, b=40),
            hovermode="x unified"
        )

        st.plotly_chart(fig, use_container_width=True)
