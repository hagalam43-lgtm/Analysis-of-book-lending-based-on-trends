import pandas as pd
import streamlit as st


def init_session_state():
    """라디오 버튼 변경 시 파일 업로드 상태를 독립적으로 관리하기 위한 세션 초기화"""
    if "current_mode" not in st.session_state:
        st.session_state.current_mode = "주식/경제 분석 (327.8 | 321.91)"

    # 사이드바에서 선택한 모드가 바뀌면 이전 업로드 파일 키를 변경하여 캐시를 초기화
    if st.session_state.current_mode != st.session_state.selected_mode:
        st.session_state.current_mode = st.session_state.selected_mode
        # 각 모드별 고유한 파일 업로더 키를 제공하여 배타적 적용


def upload_files(uploader_key):
    """각 모드별 고유 키를 받아 여러 개의 CSV 파일을 업로드받는 함수"""
    uploaded_files = st.file_uploader(
        "CSV 파일들을 선택하세요",
        type=["csv"],
        accept_multiple_files=True,
        key=uploader_key,
    )
    return uploaded_files


def show_raw_text(file):
    """업로드된 파일의 원본 내용을 텍스트로 접었다 펼 수 있게 보여주는 함수"""
    try:
        file.seek(0)
        raw_text = file.read().decode("utf-8-sig")
        with st.expander(f"📄 {file.name} 원본 파일 내용 확인 (텍스트)"):
            st.text(raw_text)
    except Exception as e:
        st.error(f"원시 텍스트를 읽는 중 오류가 발생했습니다: {e}")


def load_data(file, skip_rows):
    """지정된 행부터 데이터를 읽어와 DataFrame으로 반환하는 함수"""
    try:
        file.seek(0)
        df = pd.read_csv(file, encoding="utf-8-sig", skiprows=int(skip_rows) - 1)
        return df
    except Exception as e:
        st.error(f"{file.name} 파일을 읽는 중 오류가 발생했습니다: {e}")
        return None


def filter_data(df, file_name, mode):
    """선택한 모드의 조건에 따라 I열 데이터를 필터링하는 함수"""
    if df.shape[1] < 10:
        st.error(f"{file_name} 데이터에 필요한 열(I열 또는 J열)이 존재하지 않습니다.")
        return None

    i_col = df.columns[8]

    # 모드별 배타적 조건 필터링
    if mode == "주식/경제 분석 (327.8 | 321.91)":
        filtered_df = df[
            df[i_col].astype(str).str.contains("327.8|321.91", na=False)
        ]
    else:  # 컴퓨터과학 분석
        filtered_df = df[df[i_col].astype(str).str.contains("004.73", na=False)]

    return filtered_df


# 메인 앱 로직
def main():
    st.title("도서 대출량 통합 분석 프로그램")

    # 사이드바 라디오 버튼 세션 관리
    st.sidebar.radio(
        "분석 기능을 선택하세요",
        ["주식/경제 분석 (327.8 | 321.91)", "컴퓨터과학 분석 (004.73)"],
        key="selected_mode",
    )
    init_session_state()

    current_mode = st.session_state.current_mode

    # 1. 데이터 시작 행 지정 (모드별 기본값 분기)
    default_row = 14 if current_mode == "주식/경제 분석 (327.8 | 321.91)" else 13
    start_row = st.number_input(
        "데이터 시작 행 번호를 입력하세요",
        min_value=1,
        value=default_row,
        step=1,
    )

    # 2. 다중 파일 업로드 (모드 이름별로 키를 분리하여 배타적 파일 업로드 구현)
    files = upload_files(uploader_key=f"uploader_{current_mode}")

    if files:
        total_sum = 0.0
        chart_data_dict = {"파일명": [], "J열 합계": []}

        st.markdown("---")
        st.subheader("파일별 상세 분석 및 선택된 행")

        for file in files:
            # 기능 요구사항 2: 원본 파일 내용 확인 (텍스트 표기)
            show_raw_text(file)

            # 기능 요구사항 3: 지정행부터 데이터 로드
            df = load_data(file, start_row)
            if df is not None:
                # 시작 행 정렬 데이터 표로 표시
                with st.expander(f"📋 {file.name} 시작 행 기준 전체 데이터 보기"):
                    st.dataframe(df)

                # 기능 요구사항 4: 조건에 맞는 행 선택
                filtered_df = filter_data(df, file.name, current_mode)

                if filtered_df is not None:
                    st.write(f"📂 **{file.name}** (선택된 행: {len(filtered_df)}개)")

                    # 요약 정보 출력 (건수 및 컬럼 목록)
                    st.write(f"- 총 데이터 건수: **{len(filtered_df)}** 건")
                    st.write(f"- 컬럼 목록: `{list(filtered_df.columns)}`")

                    # 선택된 행 표시 칸
                    if not filtered_df.empty:
                        st.write("선정된 최종 데이터")
                        st.dataframe(filtered_df)

                        # J열(10번째) 데이터 추출 및 숫자형 변환 후 합산
                        j_col = df.columns[9]
                        j_values = pd.to_numeric(
                            filtered_df[j_col], errors="coerce"
                        ).fillna(0)
                        file_sum = float(j_values.sum())
                    else:
                        st.info("조건에 일치하는 행이 없습니다.")
                        file_sum = 0.0

                    st.write(f"- 해당 파일 J열 합계: {file_sum:,.2f}")
                    st.markdown("---")

                    # 그래프 및 최종 합산용 데이터 축적
                    total_sum += file_sum
                    chart_data_dict["파일명"].append(file.name)
                    chart_data_dict["J열 합계"].append(file_sum)

        # 3. 전체 파일의 최종 총합 표시
        st.subheader("전체 분석 결과")
        st.write(
            f"모든 파일에서 조건에 맞는 행의 J열 최종 총합: **{total_sum:,.2f}**"
        )

        # 4. 동일한 UI 스타일의 막대그래프 출력
        if chart_data_dict["파일명"]:
            st.subheader("파일별 합계 비교 시각화")
            chart_df = pd.DataFrame(chart_data_dict)
            st.bar_chart(data=chart_df, x="파일명", y="J열 합계")


if __name__ == "__main__":
    main()
