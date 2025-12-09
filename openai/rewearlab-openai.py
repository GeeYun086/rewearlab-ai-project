import os
import json
from dotenv import load_dotenv
from openai import AzureOpenAI

def main():
    try:
        load_dotenv()
        azure_oai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_oai_key = os.getenv("AZURE_OPENAI_KEY")
        azure_oai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

        client = AzureOpenAI(
            azure_endpoint=azure_oai_endpoint,
            api_key=azure_oai_key,
            api_version="2025-03-01-preview",
        )

        system_message = """
당신은 중고 의류 판매글을 자동으로 생성하는 AI입니다.
입력은 JSON 배열(list)이며, 규칙은 다음과 같습니다.

- 배열의 1번째 요소(인덱스 0): 판매자가 올릴 '대상 상품'
- 배열의 1번째 요소(인덱스 0)를 제외한 나머지 요소들: 유사 상품(관련성 높은 상품) 목록

작업:
1) 대상 상품의 brand, name, category, price, discount_rate 정보를 파악합니다.
2) 유사 상품들의 price/brand/name/category와 similarity_score를 참고하여
   - 시장 가격 범위(유사 상품 가격대)
   - 적절한 중고 판매가(추천가 1개 + 협의 가능 범위)
를 제안합니다.
3) 허위 사실은 쓰지 말고, 입력에 없는 상태/사이즈/착용횟수 등은 '확실하지 않음'으로 처리하거나 언급하지 마세요.
4) 최종 출력은 반드시 아래 JSON만 출력하세요.

{
  "title": "...",
  "content": "..."
}

제약:
- JSON 외 다른 텍스트 금지.
- title, content 필드만 포함.

반드시 지켜야 할 책임 원칙:
- 입력에 없는 정보(사이즈, 사용감, 착용감, 손상 정도, 구성품)는 임의로 생성하지 말고,
  필요 시 '확실하지 않음'으로 처리합니다.

- 성별, 연령, 체형 등을 단정하거나 암시하는 문구는 작성하지 않습니다
  (예: 여성용일 것 같다는 추측 금지).

- 특정 브랜드 혹은 특정 스타일에 대한 편향적·우월적 표현은 사용하지 않습니다.
  (예: '이 브랜드는 무조건 고급' 등 단정 금지)

- 사실과 다르거나 과장된 표현은 금지합니다.
  (예: “새상품급!”, “사용감 전혀 없음!” 등 입력 없이 사용 금지)

- 설명은 구매자가 오해하지 않도록 중립적이고 객관적으로 작성합니다.
"""

        while True:
            input_text = input("Enter (1=read input.json / 2=paste JSON / quit=exit): ").strip().lower()
            if input_text == "quit":
                break

            if input_text == "1":
                with open("input.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                user_message = json.dumps(data, ensure_ascii=False)

            elif input_text == "2":
                raw = input("Paste JSON in one line: ").strip()
                data = json.loads(raw)
                user_message = json.dumps(data, ensure_ascii=False)

            else:
                print("Please enter 1 or 2 (or quit).")
                continue

            print("\nSending request to Azure OpenAI endpoint...\n")

            response = client.responses.create(
                model=azure_oai_deployment,
                input=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                max_output_tokens=2000
            )

            generated_text = getattr(response, "output_text", "") or ""

            if not generated_text:
                try:
                    generated_text = response.output[0].content[0].text
                except Exception:
                    try:
                        generated_text = response.model_dump_json(indent=2)
                    except Exception:
                        generated_text = str(response)

            print("Answer: " + generated_text + "\n")
    except Exception as ex: print(ex)        
if __name__ == '__main__':
    main()
