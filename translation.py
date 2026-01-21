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
            # DeepL 언어 코드 매핑
            source_code = self._map_language_code(source_lang)
            target_code = self._map_language_code(target_lang)
            
            # DeepL API 호출
            result = self.translator.translate_text(
                text,
                source_lang=source_code,
                target_lang=target_code
            )
            
            return result.text
            
        except deepl.exceptions.QuotaExceededException:
            raise TranslationError("DeepL API 할당량이 초과되었습니다.")
        except deepl.exceptions.AuthorizationException:
            raise TranslationError("DeepL API 인증에 실패했습니다. API 키를 확인하세요.")
        except deepl.exceptions.ConnectionException:
            raise TranslationError("DeepL API 연결에 실패했습니다. 인터넷 연결을 확인하세요.")
        except Exception as e:
            raise TranslationError(f"번역 중 오류가 발생했습니다: {str(e)}")
    
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
            'en': 'EN-US',
            'ja': 'JA',
            'zh': 'ZH',
            'es': 'ES',
            'fr': 'FR',
            'de': 'DE',
            'it': 'IT',
            'pt': 'PT',
            'ru': 'RU'
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
            self.translator.translate_text("test", target_lang="EN-US")
            return True
        except:
            return False
