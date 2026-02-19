@echo off
echo Creating/Activating Virtual Environment...
if not exist .venv (
    python -m venv .venv
)
call .venv\Scripts\activate

echo Installing dependencies...
pip install opencv-python pytesseract gTTS pyttsx3 numpy pillow

echo Setup Complete.
pause
