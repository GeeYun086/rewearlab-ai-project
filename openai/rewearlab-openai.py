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
