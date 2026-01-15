#!/bin/bash
# Setup script for SSADAN meal notification bot

echo "🍽️  SSADAN 설치 스크립트"
echo "================================"

# Check Python version
echo ""
echo "1. Python 버전 확인..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ Python 3가 설치되어 있지 않습니다."
    echo "Python 3.8 이상을 설치해주세요."
    exit 1
fi

# Install Python dependencies
echo ""
echo "2. Python 패키지 설치..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ 패키지 설치 실패"
    exit 1
fi

# Check Tesseract
echo ""
echo "3. Tesseract OCR 확인..."
tesseract --version

if [ $? -ne 0 ]; then
    echo "⚠️  Tesseract OCR가 설치되어 있지 않습니다."
    echo ""
    echo "다음 명령어로 설치하세요:"
    echo ""
    echo "Ubuntu/Debian:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install tesseract-ocr tesseract-ocr-kor"
    echo ""
    echo "macOS:"
    echo "  brew install tesseract tesseract-lang"
    echo ""
else
    echo "✓ Tesseract OCR 설치됨"
    
    # Check Korean language support
    echo ""
    echo "4. 한국어 지원 확인..."
    tesseract --list-langs | grep kor
    
    if [ $? -ne 0 ]; then
        echo "⚠️  한국어 언어팩이 설치되어 있지 않습니다."
        echo "tesseract-ocr-kor 패키지를 설치해주세요."
    else
        echo "✓ 한국어 지원 가능"
    fi
fi

# Setup environment file
echo ""
echo "5. 환경 설정 파일 생성..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ .env 파일이 생성되었습니다."
    echo "⚠️  .env 파일을 편집하여 WEBHOOK_URL을 설정하세요!"
else
    echo "ℹ️  .env 파일이 이미 존재합니다."
fi

# Run tests
echo ""
echo "6. 테스트 실행..."
python -m unittest test_bot.py -v

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 설치 완료!"
    echo ""
    echo "다음 단계:"
    echo "1. .env 파일을 편집하여 설정을 변경하세요"
    echo "2. 식단표 이미지를 준비하세요"
    echo "3. python main.py test-ocr --image <이미지경로> 로 OCR을 테스트하세요"
    echo "4. python main.py test-webhook --url <webhook-url> 로 webhook을 테스트하세요"
    echo "5. python main.py run 으로 스케줄러를 실행하세요"
else
    echo ""
    echo "❌ 테스트 실패. 에러를 확인해주세요."
    exit 1
fi
