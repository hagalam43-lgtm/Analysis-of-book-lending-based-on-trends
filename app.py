import streamlit as st
import pandas as pd


def load_raw_text_preview(uploaded_file):
    """대용량 파일 먹통 방지를 위해 처음 2000바이트만 잘라서 UTF-8 텍스트로 읽어오는 함수"""
    # 파일의 앞부분 일부만 읽어옴 (메모리 보호)
    chunk = uploaded_file.read(2000)
    # 읽은 후 파일 포인터를 다시 맨 앞으로 이동
    uploaded_file.seek(0)

    # UTF-8 인코딩으로 변환 후 안전하게 상위 50줄만 선택
    raw_text = chunk.decode("utf-8", errors="ignore")
    lines = raw_text.splitlines()[:50]
    return "\n".join(lines)


def parse_csv_data(uploaded_file, start_row):
    """지정된 시작 행부터 UTF-8 형식의 CSV 데이터를 DataFrame으로 읽어오는 함수"""
    uploaded_file.seek(0)
    # 사용자가 입력한 직관적인 행 번호(1부터 시작)를 Pandas의 0-index로 변환
    skip_rows = max(0, start_row - 1)

    # 로딩 속도를 높이기 위해 low_memory=False 옵션 적용
    df = pd.read_csv(
        uploaded_file,
        encoding="utf-8",
        skiprows=skip_rows,
        header=0,
        low_memory=False
    )
    return df


def filter_data(df):
    """I열(9번째 열)의 값이 327인 행만 필터링하는 함수"""
    if len(df.columns) >= 9:
        # 0부터 시작하므로 9번째 열이 I열에 해당
        col_i = df.columns[8]
        # 숫자형과 문자형 데이터 모두 대응할 수 있도록 문자열로 전환 후 검사
        filtered_df = df[df[col_i].astype(str).str.contains("327", na=False)]
        return filtered_df
    else:
        return pd.DataFrame()


def main():
    """Streamlit 앱의 메인 로직을 실행하는 함수"""
    st.title("도서 대출량 분석 프로그램")

    # 1. CSV 파일 업로드
    uploaded_file = st.file_uploader("CSV 파일을 업로드하세요.", type=["csv"])

    if uploaded_file is not None:
        # 2. 원본 파일 내용 확인 (앞부분만 안전하게 로드)
        preview_text = load_raw_text_preview(uploaded_file)
        with st.expander("원본 파일 내용 확인 (상위 일부 표시)"):
            st.text(preview_text)

        # 3. 데이터 시작 행 지정 (기본값 16)
        start_row = st.number_input("데이터 시작 행 지정", min_value=1, value=16, step=1)

        # 지정된 행부터 데이터 읽기 및 표시
        df = parse_csv_data(uploaded_file, start_row)
        st.subheader("시작 행 기준 전체 데이터")
        st.dataframe(df)

        # 4. 필요한 행 필터링 및 최종 데이터 표시
        filtered_df = filter_data(df)

        st.subheader("최종 분석 데이터 (I열 327 필터링)")
        if not filtered_df.empty:
            st.dataframe(filtered_df)

            # 총 데이터 건수 및 컬럼 목록 출력
            st.write(f"총 데이터 건수: {len(filtered_df)} 건")
            st.write("컬럼 목록:")
            st.write(list(filtered_df.columns))
        else:
            st.warning("I열을 찾을 수 없거나 조건에 맞는 데이터가 없습니다.")


if __name__ == "__main__":
    main()