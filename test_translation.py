"""
번역 테스트 스크립트
영어->한국어 번역 테스트
"""

import os
from dotenv import load_dotenv
import translation

# 환경 변수 로드
load_dotenv()

def test_english_to_korean():
    """영어->한국어 번역 테스트"""
    print("=" * 50)
    print("영어->한국어 번역 테스트")
    print("=" * 50)
    
    # API 키 확인
    api_key = os.getenv('DEEPL_API_KEY')
    if not api_key:
        print("❌ DEEPL_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일에 DEEPL_API_KEY를 설정하세요.")
        return
    
    print(f"✅ API 키 확인됨: {api_key[:10]}...")
    print()
    
    try:
        # 번역기 초기화
        print("📝 번역기 초기화 중...")
        translator = translation.DeepLTranslator(api_key)
        print("✅ 번역기 초기화 완료")
        print()
        
        # 테스트 텍스트
        test_text = "hello."
        print(f"📄 테스트 텍스트: {repr(test_text)}")
        print()
        
        # 영어->한국어 번역 시도
        print("🔄 번역 시작 (영어 -> 한국어)...")
        print("-" * 50)
        
        result = translator.translate(
            text=test_text,
            source_lang='en',
            target_lang='ko'
        )
        
        print("-" * 50)
        print(f"✅ 번역 성공!")
        print(f"   원문: {test_text}")
        print(f"   번역: {result}")
        print()
        
    except translation.TranslationError as e:
        print(f"❌ 번역 에러: {str(e)}")
        print()
    except Exception as e:
        print(f"❌ 예상치 못한 에러: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        print()


def test_korean_to_english():
    """한국어->영어 번역 테스트"""
    print("=" * 50)
    print("한국어->영어 번역 테스트")
    print("=" * 50)
    
    # API 키 확인
    api_key = os.getenv('DEEPL_API_KEY')
    if not api_key:
        print("❌ DEEPL_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일에 DEEPL_API_KEY를 설정하세요.")
        return
    
    print(f"✅ API 키 확인됨: {api_key[:10]}...")
    print()
    
    try:
        # 번역기 초기화
        print("📝 번역기 초기화 중...")
        translator = translation.DeepLTranslator(api_key)
        print("✅ 번역기 초기화 완료")
        print()
        
        # 테스트 텍스트
        test_text = "안녕하세요."
        print(f"📄 테스트 텍스트: {repr(test_text)}")
        print()
        
        # 한국어->영어 번역 시도
        print("🔄 번역 시작 (한국어 -> 영어)...")
        print("-" * 50)
        
        result = translator.translate(
            text=test_text,
            source_lang='ko',
            target_lang='en'
        )
        
        print("-" * 50)
        print(f"✅ 번역 성공!")
        print(f"   원문: {test_text}")
        print(f"   번역: {result}")
        print()
        
    except translation.TranslationError as e:
        print(f"❌ 번역 에러: {str(e)}")
        print()
    except Exception as e:
        print(f"❌ 예상치 못한 에러: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        print()


if __name__ == "__main__":
    test_english_to_korean()
    print()
    test_korean_to_english()
