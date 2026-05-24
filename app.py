import streamlit as st
import pandas as pd


def load_raw_text(uploaded_file):
    """
    업로드된 파일의 원본 내용을 텍스트로 읽어오는 함수
    다양한 인코딩을 시도하여 한글 깨짐을 방지함
    """
    uploaded_file.seek(0)
    bytes_data = uploaded_file.read()
    uploaded_file.seek(0)  # 이후 작업을 위해 포인터 초기화

    # 주요 한글 인코딩 순차적 시도
    for encoding in ['utf-8', 'cp949', 'euc-kr']:
        try:
            return bytes_data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return bytes_data.decode('utf-8', errors='replace'), 'utf-8'


def parse_csv_data(uploaded_file, start_row, encoding):
    """
    사용자가 지정한 시작 행을 기준으로 데이터를 읽어 DataFrame으로 반환하는 함수
    """
    uploaded_file.seek(0)
    # 시작 행이 16인 경우, 15번째 행(인덱스 14)이 헤더가 되도록 skiprows 계산
    skip_lines = max(0, start_row - 2)

    df = pd.read_csv(uploaded_file, skiprows=skip_lines, encoding=encoding)
    # Unnamed로 들어오는 빈 열 제거
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df


def filter_and_process_data(df):
    """
    I열(9번째 열, 인덱스 8)에서 '327'이 포함된 행을 필터링하는 함수
    """
    if df.shape[1] < 9:
        return pd.DataFrame()

    # I열(KDC) 데이터를 문자열로 안전하게 변환한 뒤 '327'이 포함된 행 필터링
    condition = df.iloc[:, 8].astype(str).str.contains('327')
    filtered_df = df[condition].copy()

    # 필요한 열 선택 및 이름 변경을 위한 이름 정제 (양끝 공백 제거)
    filtered_df.columns = [col.strip() for col in filtered_df.columns]

    return filtered_df


def main():
    st.title("도서 대출량 분석 프로그램")

    # 1. CSV 파일 업로드
    uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type=["csv"])

    if uploaded_file is not None:
        # 파일 인코딩 감지 및 텍스트 로드
        raw_text, encoding = load_raw_text(uploaded_file)

        # 2. 원본 파일 내용 확인 (접었다 펼 수 있는 expander 형태)
        with st.expander("원본 파일 내용 확인", expanded=False):
            st.text(raw_text)

        # 3. 데이터 시작 행 지정 (기본값 16)
        start_row = st.number_input("데이터 시작 행 번호 지정", min_value=1, value=16, step=1)

        try:
            # 데이터 로드 및 표시
            df = parse_csv_data(uploaded_file, start_row, encoding)
            st.subheader("원본 데이터 표 표시")
            st.dataframe(df)

            # 4. 필요한 열 선택 및 필터링
            filtered_df = filter_and_process_data(df)

            st.subheader("최종 필터링 데이터 (I 열에 327 포함)")
            st.dataframe(filtered_df)

            # 총 데이터 건수와 컬럼 목록 표시
            st.write(f"총 데이터 건수: {len(filtered_df)} 건")
            st.write("컬럼 목록:")
            st.write(list(filtered_df.columns))

        except Exception as e:
            st.error(f"데이터 처리 중 오류 발생: {str(e)}")


if __name__ == "__main__":
    main()
