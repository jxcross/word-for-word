"""
텍스트 입력 및 처리 모듈
- 파일 업로드 지원
- 텍스트 붙여넣기 지원
- 문장 단위 분할
- 어절 단위 분할
- 언어 감지
"""

import re
from typing import List, Tuple, Optional


def split_into_sentences(text: str) -> List[str]:
    """
    텍스트를 문장 단위로 분할합니다.
    마침표, 느낌표, 물음표 기준으로 분할합니다.
    
    Args:
        text: 분할할 텍스트
        
    Returns:
        문장 리스트
    """
    if not text or not text.strip():
        return []
    
    # 문장 종결 기호로 분할 (마침표, 느낌표, 물음표)
    # 공백 제거 및 빈 문장 필터링
    sentences = re.split(r'([.!?]+[\s]*)', text)
    
    # 분할된 문장들을 재조합
    result = []
    current_sentence = ""
    
    for i, part in enumerate(sentences):
        current_sentence += part
        # 문장 종결 기호가 포함된 경우 문장 완성
        if re.search(r'[.!?]+', part):
            sentence = current_sentence.strip()
            if sentence:
                result.append(sentence)
            current_sentence = ""
    
    # 마지막 남은 부분 처리
    if current_sentence.strip():
        result.append(current_sentence.strip())
    
    return result


def split_into_words(sentence: str) -> List[str]:
    """
    문장을 어절 단위로 분할합니다.
    띄어쓰기와 탭을 기준으로 분할합니다.
    
    Args:
        sentence: 분할할 문장
        
    Returns:
        어절 리스트
    """
    if not sentence or not sentence.strip():
        return []
    
    # 띄어쓰기와 탭으로 분할
    words = re.split(r'[\s\t]+', sentence.strip())
    
    # 빈 문자열 제거
    words = [word for word in words if word]
    
    return words


def detect_language(text: str) -> str:
    """
    텍스트의 언어를 감지합니다.
    간단한 휴리스틱 기반 감지 (한국어/영어)
    
    Args:
        text: 언어를 감지할 텍스트
        
    Returns:
        'ko' (한국어) 또는 'en' (영어)
    """
    if not text:
        return 'en'
    
    # 한글 유니코드 범위: AC00-D7AF (완성형 한글)
    # 한글 자모 범위: 1100-11FF, 3130-318F
    korean_pattern = re.compile(r'[가-힣ㄱ-ㅎㅏ-ㅣ]')
    
    korean_chars = len(korean_pattern.findall(text))
    total_chars = len(re.findall(r'[가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z]', text))
    
    if total_chars == 0:
        return 'en'
    
    # 한글이 30% 이상이면 한국어로 판단
    if korean_chars / total_chars > 0.3:
        return 'ko'
    else:
        return 'en'


def process_text(text: str, source_lang: Optional[str] = None) -> Tuple[List[str], str]:
    """
    텍스트를 처리하여 문장 리스트와 감지된 언어를 반환합니다.
    
    Args:
        text: 처리할 텍스트
        source_lang: 원본 언어 (None이면 자동 감지)
        
    Returns:
        (문장 리스트, 감지된 언어)
    """
    if not text or not text.strip():
        return [], 'en'
    
    # 언어 감지
    if source_lang is None:
        detected_lang = detect_language(text)
    else:
        detected_lang = source_lang
    
    # 문장 분할
    sentences = split_into_sentences(text)
    
    return sentences, detected_lang


def get_current_sentence_words(sentences: List[str], sentence_idx: int) -> List[str]:
    """
    현재 문장의 어절 리스트를 반환합니다.
    
    Args:
        sentences: 전체 문장 리스트
        sentence_idx: 현재 문장 인덱스
        
    Returns:
        현재 문장의 어절 리스트
    """
    if not sentences or sentence_idx < 0 or sentence_idx >= len(sentences):
        return []
    
    return split_into_words(sentences[sentence_idx])
