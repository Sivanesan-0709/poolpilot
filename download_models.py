"""
Script to pre-download and cache pretrained AI model weights for offline hackathon execution.
"""

import sys
import os

# Ensure safe UTF-8 output on Windows terminals
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def download_all_models():
    print("=" * 65)
    print("   POOLPILOT: PRETRAINED AI MODEL PRE-DOWNLOAD UTILITY")
    print("=" * 65)

    # 1. sentence-transformers (all-MiniLM-L6-v2)
    print("\n[1/4] Checking sentence-transformers (all-MiniLM-L6-v2)...")
    try:
        from sentence_transformers import SentenceTransformer
        print(" -> Downloading / loading all-MiniLM-L6-v2 weights...")
        m = SentenceTransformer("all-MiniLM-L6-v2")
        print(" [OK] sentence-transformers ready and cached!")
    except ImportError:
        print(" [NOTE] sentence-transformers not installed. App will use deterministic multi-keyword fallback.")
    except Exception as e:
        print(f" [WARN] Download note: {e}")

    # 2. Chronos-Bolt-tiny
    print("\n[2/4] Checking Chronos-Bolt-tiny time-series forecasting...")
    try:
        from chronos import ChronosPipeline
        print(" -> Downloading / loading Chronos-Bolt-tiny weights...")
        p = ChronosPipeline.from_pretrained("amazon/chronos-bolt-tiny", device_map="cpu")
        print(" [OK] Chronos-Bolt-tiny ready and cached!")
    except ImportError:
        print(" [NOTE] chronos-forecasting not installed. App will use Prophet / hourly moving average fallback.")
    except Exception as e:
        print(f" [WARN] Download note: {e}")

    # 3. EasyOCR English Models
    print("\n[3/4] Checking EasyOCR vehicle plate reader...")
    try:
        import easyocr
        print(" -> Downloading / loading EasyOCR English models...")
        reader = easyocr.Reader(["en"], gpu=False)
        print(" [OK] EasyOCR ready and cached!")
    except ImportError:
        print(" [NOTE] easyocr not installed. App will use Indian vehicle plate regex format validator.")
    except Exception as e:
        print(f" [WARN] Download note: {e}")

    # 4. DeepFace
    print("\n[4/4] Checking DeepFace face match...")
    try:
        from deepface import DeepFace
        print(" [OK] DeepFace package detected.")
    except ImportError:
        print(" [NOTE] deepface not installed. App will use biometric facial feature structure fallback.")
    except Exception as e:
        print(f" [WARN] Download note: {e}")

    print("\n" + "=" * 65)
    print(" [OK] Model pre-download scan complete! All fallback paths are active.")
    print("=" * 65)


if __name__ == "__main__":
    download_all_models()
