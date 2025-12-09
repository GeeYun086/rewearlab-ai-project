import streamlit as st
import pandas as pd

# --- 사이드바 설정 ---
with st.sidebar:
    st.title("💡 프로젝트 개요")
    st.markdown("""### 👚중고 의류 재판매 가치 판별 서비스
이 서비스는 **중고 의류 판매자를 위한 AI 기반 보조 도구**로, 상품의 *재판매 가치 판별 → 트렌드 분석 → 상품 판매글 자동 생성*까지 판매 준비 과정을 빠르고 간편하게 도와줍니다.

---

### 🌟 제공 기능
**1) 오염·이염 탐지 (YOLO 모델 기반)**  
- 업로드한 이미지에서 오염/이염 여부를 감지하여  
  **재판매 가능 여부를 자동 판단**합니다.

**2) 트렌드 유사 상품 매칭 (FashionCLIP + ChromaDB)**  
- 현재 인기 있는 무신사 베스트 상품과의 유사도를 분석하여  
  **트렌드 적합성을 확인**할 수 있습니다.

**3) AI 기반 상품 제목·설명 자동 생성**  
- LLM(GPT-5.1)이 유사 상품 정보를 기반으로  
  **판매에 바로 사용할 수 있는 상품명과 설명을 생성**합니다.

---

### 💡 기대 효과
- 상품 등록 시간을 단축할 수 있습니다.  
- 판매 문구 작성에 어려움을 느끼는 판매자에게 도움을 줍니다.  
- 트렌드 기반 유사 상품 비교로 **경쟁력 있는 가격·문구 설정**이 가능합니다.  """)
    st.markdown("---")
    st.subheader("모델 정보")
    st.text("* 오염 탐지: AiHub/YOLO")
    st.text("* 임베딩/유사도: FashionCLIP + ChromaDB")
    st.text("* 정보 생성: LLM (GPT-5.1)")
    top_k = st.slider("유사 상품 Top-K 개수", 1, 10, 3)

# --- 메인 컬럼 설정 ---
st.title("👚 중고 의류 재판매 가치 판별 서비스")

# ====================
# 1. 이미지 업로드
# ====================
st.header("1. 의류 이미지 업로드")

# 포용성 - 촬영 가이드 제공
with st.expander("📷 중고 의류 촬영 가이드 (분석 정확도 향상을 위해 권장)", expanded=False):
    st.markdown(
        """
- **배경**: 가능하면 **단색 배경**에서 촬영해주세요. (침대시트/바닥 패턴 최소화)
- **구도**: 옷의 **전체 실루엣이 화면에 모두 나오도록** 촬영해주세요.
- **밝기**: 충분한 조명 아래에서 촬영하고, 너무 어둡거나 과도하게 밝지 않게 조정해주세요.
- **구김/접힘**: 옷은 최대한 **펼쳐진 상태**에서 촬영하면 오염·이염 탐지 정확도가 올라갑니다.
        """
    )

uploaded_file = st.file_uploader("판매할 중고 의류 이미지를 선택해주세요.", type=['jpg', 'jpeg', 'png'])

# 오류 대비 플래그
analysis_success = True  

if uploaded_file is not None:

    # 업로드 이미지 출력
    st.image(uploaded_file, caption='업로드된 의류 이미지', use_column_width=True)

    # 개인정보보호 문구
    st.caption("※ 업로드한 이미지는 분석 후 즉시 삭제되며, 서버에 저장되지 않습니다.")
    st.markdown("---")

    # 실제 모델 로직 try/except
    try:
        # 더미 예시
        is_repurpose_possible = True
        detection_results = {"status": "Clean", "confidence": 0.99}
    except:
        analysis_success = False

    # 분석 실패 fallback
    if not analysis_success:
        st.error("⚠️ 현재 분석이 불가합니다. 잠시 후 다시 시도해주세요.")
        st.stop()

    # ====================
    # 2. 재판매 가능 여부 판별
    # ====================
    st.header("2. 오염·이염 탐지 및 재판매 판별")

    col1, col2 = st.columns([1, 2])

    with col1:
        if is_repurpose_possible:
            st.success("🟢 재판매 가능")
            st.metric("판단 근거", "오염/이염 없음")
        else:
            st.error("🔴 재판매 불가")
            st.metric("판단 근거", f"오염 감지 (정확도 {detection_results['confidence'] * 100:.2f}%)")

        # 책임성 문구
        st.caption("※ 본 결과는 AI 분석 기준이며, 실제 상품 상태는 사용자가 반드시 직접 확인해야 합니다.")

    with col2:
        st.info("탐지 결과 이미지가 여기에 표시됩니다.")

    st.markdown("---")

    # ====================
    # 3. 유사 상품 Top-K 결과
    # ====================
    similar_items = {
        '상품명': [
            '무신사 베스트 1 - 오버핏 크롭 니트',
            '무신사 베스트 2 - 루즈핏 캐시미어 가디건',
            '무신사 베스트 3 - 미니멀 라운드 맨투맨'
        ],
        '유사도': [0.87, 0.79, 0.77],
    }

    top_k = 3
    df_similar = pd.DataFrame(similar_items).head(top_k)

    st.header(f"3. 트렌드 유사 상품 (Top-{top_k})")
    st.dataframe(df_similar, use_container_width=True)

    # 크롤링 출처 (투명성·책임성)
    st.caption("※ 유사 상품 정보는 무신사 베스트 상품 데이터를 기반으로 수집되었습니다.")
    st.markdown("---")

    # ====================
    # 4. AI 기반 문구 생성
    # ====================
    st.header("4. AI 기반 상품 판매 정보 생성")

    generated_title = "✨ [AI 추천] 트렌디한 크림 컬러 데일리 라운드넥 니트"
    generated_description = """
- **소재/컬러:** 부드러운 크림 컬러의 램스울 혼방 소재
- **트렌드:** 인기 베이직 캐주얼 스타일과 높은 유사도
- **추천 코디:** 데님·슬랙스와 매칭해 미니멀 룩 연출
"""

    st.subheader("📝 자동 생성된 상품 제목")
    st.text_area("제목:", generated_title, height=50)

    st.subheader("📄 자동 생성된 상세 설명")
    st.text_area("상세 설명:", generated_description, height=200)

    st.markdown("---")
    st.success("재판매 가능 판정 및 상품 정보 생성이 완료되었습니다. 판매 전 실제 상품 상태를 꼭 확인해주세요!")

st.markdown("---")
st.caption(
    "이 서비스는 중고 의류 판매를 돕기 위한 **AI 보조 도구**입니다.  \n"
    "AI의 판단 및 추천 문구는 참고용이며, 실제 거래에 대한 **법적·실질적 책임은 사용자에게 있습니다.**  \n"
)
