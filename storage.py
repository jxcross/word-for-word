"""
번역 결과 저장 기능
- 문장별 원문-번역문 쌍 저장
- 텍스트 파일 형식: 원문 | 번역문
- 파일명에 타임스탬프 포함
"""

import os
from datetime import datetime
from typing import List, Tuple, Optional


def save_translation(
    translations: List[Tuple[str, str]], 
    filename: Optional[str] = None,
    output_dir: str = "translations"
) -> str:
    """
    번역 결과를 텍스트 파일로 저장합니다.
    
    Args:
        translations: (원문, 번역문) 튜플 리스트
        filename: 저장할 파일명 (None이면 타임스탬프로 생성)
        output_dir: 저장할 디렉토리
        
    Returns:
        저장된 파일 경로
    """
    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # 파일명 생성
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"translation_{timestamp}.txt"
    
    # 파일 경로
    filepath = os.path.join(output_dir, filename)
    
    # 파일 쓰기
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            for original, translated in translations:
                # 원문 | 번역문 형식으로 저장
                f.write(f"{original} | {translated}\n")
        
        return filepath
    except Exception as e:
        raise IOError(f"파일 저장 중 오류가 발생했습니다: {str(e)}")


def load_translation_history(filepath: str) -> List[Tuple[str, str]]:
    """
    저장된 번역 결과를 로드합니다.
    
    Args:
        filepath: 번역 파일 경로
        
    Returns:
        (원문, 번역문) 튜플 리스트
    """
    translations = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # 원문 | 번역문 형식 파싱
                if ' | ' in line:
                    parts = line.split(' | ', 1)
                    if len(parts) == 2:
                        translations.append((parts[0].strip(), parts[1].strip()))
        
        return translations
    except FileNotFoundError:
        return []
    except Exception as e:
        raise IOError(f"파일 로드 중 오류가 발생했습니다: {str(e)}")


def get_translation_files(output_dir: str = "translations") -> List[str]:
    """
    저장된 번역 파일 목록을 반환합니다.
    
    Args:
        output_dir: 번역 파일 디렉토리
        
    Returns:
        파일 경로 리스트
    """
    if not os.path.exists(output_dir):
        return []
    
    files = []
    for filename in os.listdir(output_dir):
        if filename.endswith('.txt'):
            files.append(os.path.join(output_dir, filename))
    
    # 최신 파일부터 정렬
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    return files
