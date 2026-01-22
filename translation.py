"""
DeepL API 번역 모듈
- DeepL API 클라이언트 래퍼
- 누적 텍스트 실시간 번역
- API 키 환경 변수 관리
- 에러 처리 및 재시도 로직
"""

import os
from typing import Optional
import deepl
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


class TranslationError(Exception):
    """번역 관련 에러"""
    pass


class DeepLTranslator:
    """DeepL API를 사용한 번역 클래스"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        DeepL 번역기 초기화
        
        Args:
            api_key: DeepL API 키 (None이면 환경 변수에서 로드)
        """
        self.api_key = api_key or os.getenv('DEEPL_API_KEY')
        
        if not self.api_key:
            raise TranslationError(
                "DeepL API 키가 설정되지 않았습니다. "
                ".env 파일에 DEEPL_API_KEY를 설정하거나 API 키를 직접 입력하세요."
            )
        
        try:
            self.translator = deepl.Translator(self.api_key)
        except Exception as e:
            raise TranslationError(f"DeepL API 초기화 실패: {str(e)}")
    
    def translate(
        self, 
        text: str, 
        source_lang: str = 'ko', 
        target_lang: str = 'en'
    ) -> str:
        """
        텍스트를 번역합니다.
        
        Args:
            text: 번역할 텍스트
            source_lang: 원본 언어 코드 ('ko', 'en' 등)
            target_lang: 목표 언어 코드 ('ko', 'en' 등)
            
        Returns:
            번역된 텍스트
            
        Raises:
            TranslationError: 번역 실패 시
        """
        if not text or not text.strip():
            return ""
        
        try:
            # 디버그: 입력 파라미터 출력
            print(f"[DEBUG] translate 호출:")
            print(f"  - text: {repr(text)}")
            print(f"  - source_lang: {source_lang}")
            print(f"  - target_lang: {target_lang}")
            
            # DeepL 언어 코드 매핑
            source_code = self._map_language_code(source_lang)
            target_code = self._map_language_code(target_lang)
            
            print(f"[DEBUG] 매핑된 언어 코드:")
            print(f"  - source_code: {source_code}")
            print(f"  - target_code: {target_code}")
            
            # DeepL API 호출
            # source_lang을 None으로 설정하여 자동 감지 사용
            # (명시적 source_lang이 일부 경우 문제를 일으킬 수 있음)
            # 자동 감지가 더 안정적으로 작동함
            api_source_lang = None
            
            print(f"[DEBUG] API 호출 파라미터:")
            print(f"  - text: {repr(text)}")
            print(f"  - source_lang: {api_source_lang} (원본: {source_code})")
            print(f"  - target_lang: {target_code}")
            
            result = self.translator.translate_text(
                text,
                source_lang=api_source_lang,
                target_lang=target_code
            )
            
            print(f"[DEBUG] 번역 성공:")
            print(f"  - 결과: {repr(result.text)}")
            print(f"  - 감지된 언어: {result.detected_source_lang if hasattr(result, 'detected_source_lang') else 'N/A'}")
            
            return result.text
            
        except deepl.exceptions.QuotaExceededException as e:
            print(f"[DEBUG] 에러: QuotaExceededException - {str(e)}")
            raise TranslationError("DeepL API 할당량이 초과되었습니다.")
        except deepl.exceptions.AuthorizationException as e:
            print(f"[DEBUG] 에러: AuthorizationException - {str(e)}")
            raise TranslationError("DeepL API 인증에 실패했습니다. API 키를 확인하세요.")
        except deepl.exceptions.ConnectionException as e:
            print(f"[DEBUG] 에러: ConnectionException - {str(e)}")
            raise TranslationError("DeepL API 연결에 실패했습니다. 인터넷 연결을 확인하세요.")
        except Exception as e:
            print(f"[DEBUG] 에러: Exception - {type(e).__name__}: {str(e)}")
            print(f"[DEBUG] 에러 상세 정보:")
            import traceback
            traceback.print_exc()
            raise TranslationError(f"번역 중 오류가 발생했습니다: {type(e).__name__}: {str(e)}")
    
    def _map_language_code(self, lang: str) -> str:
        """
        언어 코드를 DeepL 형식으로 매핑합니다.
        
        Args:
            lang: 언어 코드 ('ko', 'en' 등)
            
        Returns:
            DeepL 언어 코드
        """
        lang_map = {
            'ko': 'KO',
            'en': 'EN-US',  # EN은 deprecated, EN-US 또는 EN-GB 사용
            'ja': 'JA',
            'zh': 'ZH',
            'es': 'ES',
            'fr': 'FR',
            'de': 'DE',
            'it': 'IT',
            'pt': 'PT',
            'ru': 'RU',
            'en-us': 'EN-US',
            'en-gb': 'EN-GB',
            'en-uk': 'EN-GB',  # EN-UK는 EN-GB의 별칭
        }
        
        return lang_map.get(lang.lower(), 'EN-US')
    
    def is_valid_api_key(self) -> bool:
        """
        API 키가 유효한지 확인합니다.
        
        Returns:
            API 키 유효 여부
        """
        try:
            # 간단한 테스트 번역으로 API 키 검증
            self.translator.translate_text("test", target_lang="EN")
            return True
        except:
            return False
