"""
무신사 패션 이미지 유사도 검색 앱
카테고리별 컬렉션에서 유사 아이템 검색
"""

import streamlit as st
import torch
from PIL import Image
import numpy as np
from transformers import AutoImageProcessor, AutoModelForObjectDetection
import chromadb
import logging
import json
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('musinsa_search.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 컬렉션 이름 리스트
COLLECTION_NAMES = ['pants', 'top', 'outer', 'dress_skirts']

# 세션 상태 초기화
if 'image' not in st.session_state:
    st.session_state.image = None
if 'detected_boxes' not in st.session_state:
    st.session_state.detected_boxes = None
if 'selected_box_index' not in st.session_state:
    st.session_state.selected_box_index = None

@st.cache_resource
def load_detection_model():
    """객체 탐지 모델 로드"""
    try:
        logger.info("객체 탐지 모델 로딩 중...")
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        ckpt = 'yainage90/fashion-object-detection'
        image_processor = AutoImageProcessor.from_pretrained(ckpt)
        model = AutoModelForObjectDetection.from_pretrained(ckpt).to(device)
        logger.info(f"객체 탐지 모델이 {device}에 로드되었습니다.")
        return image_processor, model, device
    except Exception as e:
        logger.error(f"객체 탐지 모델 로드 중 오류 발생: {str(e)}")
        raise

def crop_image(image, box):
    """바운딩 박스에 맞게 이미지 크롭"""
    width, height = image.size
    x1, y1, x2, y2 = [int(coord) for coord in box]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(width, x2), min(height, y2)
    return image.crop((x1, y1, x2, y2))

def detect_fashion_items(image, min_size=100, threshold=0.4):
    """
    패션 아이템 탐지 및 바운딩 박스 추출
    
    Args:
        image: PIL Image
        min_size: 최소 크기 (픽셀)
        threshold: 탐지 신뢰도 임계값
    
    Returns:
        탐지된 아이템 리스트 (bbox, label, score 포함)
    """
    try:
        image_processor, detection_model, device = load_detection_model()
        
        with torch.no_grad():
            inputs = image_processor(images=[image], return_tensors="pt")
            outputs = detection_model(**inputs.to(device))
            target_sizes = torch.tensor([[image.size[1], image.size[0]]])
            results = image_processor.post_process_object_detection(
                outputs, 
                threshold=threshold, 
                target_sizes=target_sizes
            )[0]
            
            detected_items = []
            
            for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
                label_name = detection_model.config.id2label[label.item()].lower()
                score_value = score.item()
                
                x1, y1, x2, y2 = [int(coord) for coord in box]
                
                # 크기 필터링
                area = (x2 - x1) * (y2 - y1)
                if area < min_size:
                    continue
                
                detected_items.append({
                    'bbox': [x1, y1, x2, y2],
                    'label': label_name,
                    'score': score_value,
                    'area': area
                })
            
            # 면적 기준 내림차순 정렬
            detected_items.sort(key=lambda x: x['area'], reverse=True)
            
            logger.info(f"총 {len(detected_items)}개 아이템 탐지됨")
            return detected_items
            
    except Exception as e:
        logger.error(f"패션 아이템 탐지 중 오류: {str(e)}")
        return []

def search_similar_items(image, top_k=10, selected_collections=None):
    """
    여러 컬렉션에서 유사 아이템 검색
    
    Args:
        image: PIL Image (크롭된 이미지)
        top_k: 반환할 결과 수
        selected_collections: 검색할 컬렉션 리스트 (None이면 모든 컬렉션)
    
    Returns:
        유사 아이템 리스트
    """
    try:
        # 환경 변수로 ChromaDB 서버 설정 (Azure 배포용)
        import os
        chromadb_host = os.getenv("CHROMADB_HOST", None)
        chromadb_port = int(os.getenv("CHROMADB_PORT", 8000))
        
        if chromadb_host:
            # 원격 ChromaDB 서버 사용 (Azure 배포)
            client = chromadb.HttpClient(host=chromadb_host, port=chromadb_port)
            logger.info(f"ChromaDB 원격 서버 연결: {chromadb_host}:{chromadb_port}")
        else:
            # 로컬 파일 기반 ChromaDB 사용 (로컬 테스트)
            client = chromadb.PersistentClient(path="./musinsa_fashion_db_crop")
            logger.info("ChromaDB 로컬 파일 사용: ./musinsa_fashion_db_crop")
        # 임베딩할 때와 동일한 모델 사용
        embedding_function = OpenCLIPEmbeddingFunction(
            model_name="hf-hub:Marqo/marqo-fashionSigLIP"
        )
        
        # 검색할 컬렉션 결정
        if selected_collections is None:
            selected_collections = COLLECTION_NAMES
        
        logger.info(f"검색 대상 컬렉션: {selected_collections}")
        
        # 각 컬렉션에서 검색 수행
        all_results = []
        
        for collection_name in selected_collections:
            try:
                collection = client.get_collection(
                    name=collection_name,
                    embedding_function=embedding_function
                )
                
                logger.info(f"컬렉션 '{collection_name}'에서 검색 중... (총 {collection.count()}개 아이템)")
                
                results = collection.query(
                    query_images=[np.array(image)],
                    n_results=top_k,
                    include=['metadatas', 'distances']
                )
                
                if results and 'metadatas' in results and results['metadatas']:
                    for metadata, distance in zip(results['metadatas'][0], results['distances'][0]):
                        # 유사도 점수 계산 (거리의 역수)
                        similarity_score = 1 / (1 + distance)
                        
                        item_data = metadata.copy()
                        item_data['similarity_score'] = similarity_score * 100
                        item_data['distance'] = float(distance)
                        item_data['collection'] = collection_name
                        all_results.append(item_data)
                
            except Exception as e:
                logger.error(f"컬렉션 '{collection_name}' 검색 중 오류: {e}")
                continue
        
        # 결과 정렬 및 중복 제거
        seen_ids = set()
        unique_results = []
        
        for item in sorted(all_results, key=lambda x: x['similarity_score'], reverse=True):
            item_id = item.get('id', '') or item.get('product_id', '')
            if item_id not in seen_ids:
                seen_ids.add(item_id)
                unique_results.append(item)
                
                if len(unique_results) >= top_k:
                    break
        
        # 로그에 검색 결과 JSON 형태로 출력
        logger.info("=" * 80)
        logger.info("검색 결과 (JSON)")
        logger.info("=" * 80)
        logger.info(json.dumps(unique_results, ensure_ascii=False, indent=2))
        logger.info("=" * 80)
        
        return unique_results
        
    except Exception as e:
        logger.error(f"검색 중 오류 발생: {e}")
        return []

def show_similar_items(similar_items):
    """유사 아이템 표시"""
    if not similar_items:
        st.warning("유사한 아이템을 찾지 못했습니다.")
        return
    
    st.subheader(f"🔍 유사한 아이템 ({len(similar_items)}개)")
    
    items_per_row = 3
    for i in range(0, len(similar_items), items_per_row):
        cols = st.columns(items_per_row)
        for j, col in enumerate(cols):
            if i + j < len(similar_items):
                item = similar_items[i + j]
                with col:
                    try:
                        # 이미지 표시
                        if 'image_url' in item:
                            st.image(item['image_url'], width="stretch")
                        elif 'uri' in item:
                            st.image(item['uri'], width="stretch")
                        
                        # 유사도 점수
                        st.markdown(f"**유사도: {item['similarity_score']:.1f}%**")
                        
                        # 상품 정보
                        st.write(f"**브랜드**: {item.get('brand', '알 수 없음')}")
                        
                        name = item.get('name', '알 수 없음')
                        if len(name) > 40:
                            name = name[:37] + "..."
                        st.write(f"**제품명**: {name}")
                        
                        st.write(f"**카테고리**: {item.get('category', '알 수 없음')}")
                        st.write(f"**컬렉션**: {item.get('collection', '알 수 없음')}")
                        st.write(f"**가격**: {item.get('price', '알 수 없음')}원")
                        
                        # 탐지 라벨
                        detected_label = item.get('detected_label', 'original')
                        if detected_label != 'original':
                            st.write(f"**탐지 라벨**: {detected_label}")
                        
                        # 상품 URL
                        if 'product_url' in item and item['product_url']:
                            st.markdown(f"[무신사에서 보기]({item['product_url']})")
                        
                        st.divider()
                        
                    except Exception as e:
                        logger.error(f"아이템 표시 중 오류: {e}")
                        st.error("이 아이템을 표시하는 중 오류가 발생했습니다")

def main():
    st.set_page_config(layout="wide")
    st.title("🛍️ 무신사 패션 이미지 검색")
    
    st.markdown("""
    ### 사용 방법
    1. 패션 이미지를 업로드하세요
    2. 자동으로 의류 아이템을 감지합니다
    3. 검색할 아이템을 선택하세요
    4. 검색할 카테고리를 선택하세요
    5. 유사한 아이템을 찾습니다
    """)
    
    # 사이드바 옵션
    with st.sidebar:
        st.header("검색 옵션")
        
        # 검색할 컬렉션 선택
        st.subheader("검색 카테고리")
        selected_collections = []
        
        if st.checkbox("바지 (pants)", value=True):
            selected_collections.append('pants')
        if st.checkbox("상의 (top)", value=True):
            selected_collections.append('top')
        if st.checkbox("아우터 (outer)", value=True):
            selected_collections.append('outer')
        if st.checkbox("원피스/스커트 (dress_skirts)", value=True):
            selected_collections.append('dress_skirts')
        
        if not selected_collections:
            st.warning("최소 1개 이상의 카테고리를 선택하세요")
        
        # 결과 수
        num_results = st.slider(
            "검색 결과 수",
            min_value=1,
            max_value=20,
            value=9,
            help="표시할 유사 아이템 개수"
        )
        
        # 탐지 옵션
        st.subheader("탐지 옵션")
        detection_threshold = st.slider(
            "탐지 신뢰도 임계값",
            min_value=0.1,
            max_value=0.9,
            value=0.4,
            step=0.1,
            help="낮을수록 더 많은 객체 탐지"
        )
    
    # 파일 업로더
    uploaded_file = st.file_uploader(
        "패션 이미지 업로드",
        type=['png', 'jpg', 'jpeg'],
        help="의류가 포함된 이미지를 업로드하세요"
    )
    
    if uploaded_file is not None:
        # 이미지 로드
        image = Image.open(uploaded_file).convert('RGB')
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("업로드된 이미지")
            st.image(image, width="stretch")
        
        # 의류 감지
        with st.spinner("의류 영역 감지 중..."):
            detected_items = detect_fashion_items(
                image, 
                threshold=detection_threshold
            )
        
        if not detected_items:
            st.warning("⚠️ 의류 아이템을 찾지 못했습니다. 원본 이미지로 검색합니다.")
            detected_items = [{
                'bbox': [0, 0, image.size[0], image.size[1]],
                'label': 'original',
                'score': 0.0,
                'area': image.size[0] * image.size[1]
            }]
        
        with col2:
            st.subheader(f"감지된 의류 아이템 ({len(detected_items)}개)")
            
            # 감지된 영역 미리보기
            preview_cols = st.columns(min(len(detected_items), 3))
            for idx, (item, preview_col) in enumerate(zip(detected_items[:3], preview_cols)):
                bbox = item['bbox']
                cropped = crop_image(image, bbox)
                with preview_col:
                    st.image(cropped, width="stretch")
                    st.caption(f"{item['label']} ({item['score']:.2f})")
        
        # 아이템 선택
        st.write("---")
        
        col_select, col_search = st.columns([2, 1])
        
        with col_select:
            selected_idx = st.selectbox(
                "검색할 아이템 선택:",
                range(len(detected_items)),
                format_func=lambda x: f"아이템 {x + 1} - {detected_items[x]['label']} (신뢰도: {detected_items[x]['score']:.2f})"
            )
        
        with col_search:
            st.write("")  # 공간 맞추기
            st.write("")
            search_button = st.button(
                "🔍 유사 아이템 검색",
                type="primary",
                use_container_width=True
            )
        
        # 선택된 아이템 표시
        selected_item = detected_items[selected_idx]
        selected_bbox = selected_item['bbox']
        cropped_image = crop_image(image, selected_bbox)
        
        st.subheader("선택된 아이템")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(cropped_image, width="stretch")
            st.caption(f"{selected_item['label']} (신뢰도: {selected_item['score']:.2f})")
        
        # 검색 실행
        if search_button:
            if not selected_collections:
                st.error("⚠️ 검색할 카테고리를 최소 1개 이상 선택하세요")
            else:
                with st.spinner("유사한 아이템 검색 중..."):
                    similar_items = search_similar_items(
                        cropped_image,
                        top_k=num_results,
                        selected_collections=selected_collections
                    )
                
                st.write("---")
                
                if similar_items:
                    show_similar_items(similar_items)
                    
                    # 통계 표시
                    st.write("---")
                    st.write("### 📊 검색 통계")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("검색된 아이템", len(similar_items))
                    with col2:
                        avg_similarity = sum(item['similarity_score'] for item in similar_items) / len(similar_items)
                        st.metric("평균 유사도", f"{avg_similarity:.1f}%")
                    with col3:
                        max_similarity = max(item['similarity_score'] for item in similar_items)
                        st.metric("최고 유사도", f"{max_similarity:.1f}%")
                else:
                    st.warning("유사한 아이템을 찾지 못했습니다.")
    
    else:
        st.info("👆 이미지를 업로드하여 검색을 시작하세요")
    
    # 하단 정보
    st.write("---")
    st.markdown("""
    **💡 팁:**
    - 의류가 명확하게 보이는 이미지를 사용하세요
    - 여러 의류가 있는 경우 원하는 아이템을 선택할 수 있습니다
    - 검색 결과는 유사도 순으로 정렬됩니다
    - 로그 파일(`musinsa_search.log`)에서 상세한 검색 결과를 확인할 수 있습니다
    """)

if __name__ == "__main__":
    main()