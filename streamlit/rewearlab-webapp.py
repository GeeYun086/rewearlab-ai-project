import streamlit as st
import pandas as pd

# --- 사이드바 설정 ---
with st.sidebar:
    st.title("💡 프로젝트 개요")
    st.markdown("**중고 의류 재판매 가치 판별 서비스**")
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
uploaded_file = st.file_uploader("판매할 중고 의류 이미지를 선택해주세요.", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    st.image(uploaded_file, caption='업로드된 의류 이미지', use_column_width=True)
    st.markdown("---")

    is_repurpose_possible = True
    detection_results = {"status": "Clean", "confidence": 0.99, "detection_image": "path/to/result_image.jpg"}
    
    # ====================
    # 2. 재판매 가능 여부 판별
    # ====================
    st.header("2. 오염·이염 탐지 및 재판매 판별")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if is_repurpose_possible:
            st.success("🟢 **재판매 가능**")
            st.metric("판단 근거", "오염/이염 없음")
        else:
            st.error("🔴 **재판매 불가**")
            st.metric("판단 근거", f"오염 감지 (정확도 {detection_results['confidence'] * 100:.2f}%)")

    with col2:
        st.info("탐지 결과 이미지를 이 위치에 출력합니다.")
    
    st.markdown("---")

    # ====================
    # 재판매 불가 시 후속 단계 비활성화
    # ====================
    if not is_repurpose_possible:
        st.warning("⚠️ 오염이 감지되어 이후 **트렌드 분석 및 상품 정보 자동 생성 기능**은 비활성화됩니다.")
    else:
        similar_items = {
            '상품명': [
                '무신사 베스트 1 - 오버핏 크롭 니트', 
                '무신사 베스트 2 - 루즈핏 캐시미어 가디건', 
                '무신사 베스트 3 - 미니멀 라운드 맨투맨'
            ],
            '유사도': [0.87, 0.79, 0.77],
        }
        
        generated_title = "✨ [AI 추천] 트렌디한 크림 컬러 데일리 라운드넥 니트"
        generated_description = """
- **소재/컬러:** 부드러운 크림 컬러의 램스울 혼방 소재
- **트렌드:** 현재 무신사에서 가장 인기 있는 베이직 캐주얼 스타일과 높은 유사도 (0.87)
- **추천 코디:** 데님 팬츠나 슬랙스와 매치하여 미니멀/캐주얼 룩 연출에 최적
"""
        
        # ====================
        # 3. 유사 상품 Top-K 결과
        # ====================
        st.header(f"3. 트렌드 유사 상품 (Top-{top_k})")
        df_similar = pd.DataFrame(similar_items).head(top_k)
        st.dataframe(df_similar, use_container_width=True)
        st.markdown("---")
        
        # ====================
        # 4. 자동 생성된 상품 제목 + 설명
        # ====================
        st.header("4. AI 기반 상품 판매 정보 자동 생성")
        
        # 상품 제목
        st.subheader("📝 자동 생성된 상품 제목")
        st.text_area("제목:", generated_title, height=50, key="title_output")
        
        # 상세 설명
        st.subheader("📄 자동 생성된 상세 설명")
        st.text_area("상세 설명:", generated_description, height=200, key="desc_output")
        
        st.markdown("---")
        st.success("✅ **축하합니다!** 재판매 가능하며 트렌드를 반영한 상품 정보가 성공적으로 생성되었습니다. 바로 판매 플랫폼에 복사하여 활용해보세요.")