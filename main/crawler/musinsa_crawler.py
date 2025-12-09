"""
무신사 크롤러 - 다중 카테고리 버전 (2024년 12월 최신)
상의, 아우터, 바지, 가방, 원피스/스커트 카테고리 크롤링
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import json
from typing import List, Dict


class MusinsaCrawler:
    """무신사 상품 크롤러 - 다중 카테고리 지원"""
    
    # 카테고리 정의
    CATEGORIES = {
        '상의': '001',
        '아우터': '002',
        '바지': '003',
        '가방': '004',
        '원피스/스커트': '100'
    }
    
    def __init__(self, headless: bool = False):
        """
        Args:
            headless: True면 브라우저 창을 띄우지 않음
        """
        print("🚀 Selenium 드라이버 초기화 중...")
        self.driver = self._setup_driver(headless)
        self.all_products = []  # 전체 상품
        self.products_by_category = {}  # 카테고리별 상품
        print("✅ 드라이버 준비 완료!\n")
        
    def _setup_driver(self, headless: bool) -> webdriver.Chrome:
        """Chrome 드라이버 설정"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
        
        # 봇 탐지 우회
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def scroll_page(self, scroll_count: int = 5):
        """페이지 스크롤하여 상품 더 로드"""
        for i in range(scroll_count):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            if (i + 1) % 2 == 0:
                print(f"  ↓ 스크롤 {i+1}/{scroll_count}")
    
    def extract_product_info(self, link_element, category_name: str) -> Dict:
        """링크 요소에서 상품 정보 추출"""
        product = {}
        
        try:
            # data 속성에서 정보 추출
            product['상품ID'] = link_element.get_attribute('data-item-id') or ''
            product['브랜드'] = link_element.get_attribute('data-item-brand') or ''
            product['가격'] = link_element.get_attribute('data-price') or ''
            product['할인율'] = link_element.get_attribute('data-discount-rate') or '0'
            product['상품URL'] = link_element.get_attribute('href') or ''
            
            # 이미지에서 제품명 추출
            try:
                img = link_element.find_element(By.TAG_NAME, 'img')
                product['제품명'] = img.get_attribute('alt') or ''
                product['이미지URL'] = img.get_attribute('src') or ''
            except:
                product['제품명'] = link_element.text.strip() or ''
                product['이미지URL'] = ''
            
            # 카테고리
            product['카테고리'] = category_name
            product['카테고리코드'] = self.CATEGORIES[category_name]
            
            # 빈 ID는 제외
            if not product['상품ID']:
                return None
                
        except Exception as e:
            return None
        
        return product
    
    def crawl_category(self, category_name: str, max_products: int = 100, 
                      scroll_count: int = 5) -> List[Dict]:
        """
        특정 카테고리 크롤링
        
        Args:
            category_name: 카테고리 이름 (예: '상의', '아우터')
            max_products: 수집할 최대 상품 수
            scroll_count: 스크롤 횟수
        
        Returns:
            수집된 상품 리스트
        """
        category_code = self.CATEGORIES.get(category_name)
        if not category_code:
            print(f"❌ 잘못된 카테고리: {category_name}")
            return []
        
        print("="*80)
        print(f"🛒 [{category_name}] 크롤링 시작")
        print("="*80)
        
        url = f"https://www.musinsa.com/category/{category_code}?gf=A"
        print(f"📍 URL: {url}")
        print(f"🎯 목표: {max_products}개 상품\n")
        
        self.driver.get(url)
        
        # 초기 로딩 대기
        print("⏳ 페이지 로딩 중...")
        time.sleep(5)
        
        # 스크롤하여 더 많은 상품 로드
        self.scroll_page(scroll_count)
        
        print("\n🔍 상품 수집 중...\n")
        
        # 상품 링크 찾기
        selectors = [
            "a[data-item-id][href*='/products/']",
            "a[href*='/products/']",
        ]
        
        products = []
        processed_ids = set()
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                if not elements:
                    continue
                
                print(f"  ✓ {len(elements)}개 상품 링크 발견\n")
                
                for element in elements:
                    if len(products) >= max_products:
                        break
                    
                    try:
                        product = self.extract_product_info(element, category_name)
                        
                        if product and product['상품ID']:
                            if product['상품ID'] not in processed_ids:
                                products.append(product)
                                processed_ids.add(product['상품ID'])
                                
                                if len(products) % 20 == 0:
                                    print(f"  📦 {len(products)}개 수집 완료...")
                    except:
                        continue
                
                if products:
                    break
                    
            except Exception as e:
                continue
        
        print(f"\n✅ [{category_name}] {len(products)}개 수집 완료!\n")
        
        return products
    
    def crawl_all_categories(self, max_products_per_category: int = 100, 
                           scroll_count: int = 5,
                           categories: List[str] = None):
        """
        모든 카테고리 또는 지정된 카테고리 크롤링
        
        Args:
            max_products_per_category: 카테고리당 최대 상품 수
            scroll_count: 스크롤 횟수
            categories: 크롤링할 카테고리 리스트 (None이면 전체)
        """
        print("\n" + "="*80)
        print("🎨 무신사 다중 카테고리 크롤링 시작")
        print("="*80)
        print()
        
        # 크롤링할 카테고리 결정
        target_categories = categories if categories else list(self.CATEGORIES.keys())
        
        print(f"📋 크롤링 카테고리: {', '.join(target_categories)}")
        print(f"🎯 카테고리당 {max_products_per_category}개씩 수집\n")
        
        self.all_products = []
        self.products_by_category = {}
        
        # 각 카테고리별 크롤링
        for i, category in enumerate(target_categories, 1):
            print(f"\n{'='*80}")
            print(f"진행: {i}/{len(target_categories)} - {category}")
            print(f"{'='*80}\n")
            
            try:
                products = self.crawl_category(
                    category_name=category,
                    max_products=max_products_per_category,
                    scroll_count=scroll_count
                )
                
                self.products_by_category[category] = products
                self.all_products.extend(products)
                
                # 카테고리 간 대기
                if i < len(target_categories):
                    print("⏸️  다음 카테고리까지 3초 대기...\n")
                    time.sleep(3)
                    
            except Exception as e:
                print(f"❌ [{category}] 크롤링 실패: {e}\n")
                continue
        
        self._print_final_summary()
    
    def _print_final_summary(self):
        """최종 수집 결과 요약"""
        print("\n" + "="*80)
        print("🎉 전체 크롤링 완료!")
        print("="*80)
        print(f"\n총 수집 상품: {len(self.all_products)}개\n")
        print("카테고리별 수집 결과:")
        for category, products in self.products_by_category.items():
            print(f"  • {category}: {len(products)}개")
    
    def save_to_json(self, filename: str = "musinsa_products_all.json", 
                    by_category: bool = False):
        """JSON 파일로 저장"""
        if not self.all_products:
            print("⚠️  저장할 상품이 없습니다.")
            return
        
        if by_category:
            # 카테고리별로 개별 파일 저장
            for category, products in self.products_by_category.items():
                # 파일명에서 슬래시 제거
                safe_category = category.replace('/', '_')
                category_filename = f"musinsa_{safe_category}.json"
                with open(category_filename, 'w', encoding='utf-8') as f:
                    json.dump(products, f, ensure_ascii=False, indent=2)
                print(f"💾 [{category}] {len(products)}개 → '{category_filename}'")
        else:
            # 전체를 하나의 파일로 저장
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.all_products, f, ensure_ascii=False, indent=2)
            print(f"💾 전체 {len(self.all_products)}개 → '{filename}'")
    
    def save_to_csv(self, filename: str = "musinsa_products_all.csv",
                   by_category: bool = False):
        """CSV 파일로 저장"""
        if not self.all_products:
            print("⚠️  저장할 상품이 없습니다.")
            return
        
        if by_category:
            # 카테고리별로 개별 파일 저장
            for category, products in self.products_by_category.items():
                # 파일명에서 슬래시 제거
                safe_category = category.replace('/', '_')
                category_filename = f"musinsa_{safe_category}.csv"
                df = pd.DataFrame(products)
                df.to_csv(category_filename, index=False, encoding='utf-8-sig')
                print(f"💾 [{category}] {len(products)}개 → '{category_filename}'")
        else:
            # 전체를 하나의 파일로 저장
            df = pd.DataFrame(self.all_products)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"💾 전체 {len(self.all_products)}개 → '{filename}'")
    
    def get_statistics(self):
        """수집 통계 출력"""
        if not self.all_products:
            print("⚠️  통계를 계산할 상품이 없습니다.")
            return
        
        print("\n" + "="*80)
        print("📊 크롤링 통계")
        print("="*80)
        
        print(f"\n총 상품 수: {len(self.all_products)}개")
        
        # 카테고리별 통계
        print("\n📁 카테고리별 상품 수:")
        for category, products in self.products_by_category.items():
            print(f"  • {category}: {len(products)}개")
        
        # 브랜드 통계
        brands = {}
        for product in self.all_products:
            brand = product.get('브랜드', 'Unknown')
            brands[brand] = brands.get(brand, 0) + 1
        
        print(f"\n총 브랜드 수: {len(brands)}개")
        print("\nTOP 10 브랜드:")
        for brand, count in sorted(brands.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  • {brand}: {count}개")
        
        # 가격 통계
        prices = [int(p.get('가격', 0)) for p in self.all_products if p.get('가격', '').isdigit()]
        if prices:
            print(f"\n💰 가격 통계:")
            print(f"  최저가: {min(prices):,}원")
            print(f"  최고가: {max(prices):,}원")
            print(f"  평균가: {sum(prices)//len(prices):,}원")
        
        # 할인 통계
        discounts = [int(p.get('할인율', 0)) for p in self.all_products if p.get('할인율', '').isdigit()]
        if discounts:
            discount_count = len([d for d in discounts if d > 0])
            print(f"\n🏷️  할인 상품: {discount_count}개 ({discount_count*100//len(self.all_products)}%)")
    
    def print_sample(self, count: int = 3):
        """각 카테고리별 샘플 출력"""
        print("\n" + "="*80)
        print("📋 카테고리별 샘플 상품")
        print("="*80)
        
        for category, products in self.products_by_category.items():
            print(f"\n[{category}] - {len(products)}개 중 {min(count, len(products))}개")
            print("-" * 80)
            
            for i, product in enumerate(products[:count], 1):
                print(f"{i}. {product.get('브랜드', 'N/A')} - {product.get('제품명', 'N/A')[:50]}")
                print(f"   가격: {product.get('가격', 'N/A')}원 (할인 {product.get('할인율', '0')}%)")
    
    def close(self):
        """브라우저 종료"""
        self.driver.quit()
        print("\n🔚 브라우저 종료")


def main():
    """메인 실행 함수"""
    
    print("\n" + "="*80)
    print("🎨 무신사 다중 카테고리 크롤러 v4.0")
    print("="*80)
    print()
    
    # 크롤러 초기화
    crawler = MusinsaCrawler(headless=False)
    
    try:
        # 옵션 1: 모든 카테고리 크롤링
        crawler.crawl_all_categories(
            max_products_per_category=100,  # 카테고리당 100개
            scroll_count=5
        )
        
        # 옵션 2: 특정 카테고리만 크롤링하고 싶다면
        # crawler.crawl_all_categories(
        #     max_products_per_category=100,
        #     scroll_count=5,
        #     categories=['상의', '바지']  # 원하는 카테고리만 지정
        # )
        
        # 결과 출력
        if crawler.all_products:
            crawler.print_sample(count=3)
            crawler.get_statistics()
            
            # 파일 저장
            print("\n" + "="*80)
            print("💾 파일 저장 중...")
            print("="*80)
            
            # 전체 파일 저장
            crawler.save_to_json("musinsa_all_products.json")
            crawler.save_to_csv("musinsa_all_products.csv")
            
            print()
            
            # 카테고리별 파일 저장
            crawler.save_to_json(by_category=True)
            crawler.save_to_csv(by_category=True)
            
            print("="*80)
        else:
            print("\n❌ 상품을 수집하지 못했습니다.")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        crawler.close()


if __name__ == "__main__":
    main()