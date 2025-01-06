from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import httpx
import pytesseract
from PIL import Image
import io

app = FastAPI()

# 設置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載靜態文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jisho API 查詢函數
async def query_jisho(keyword: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://jisho.org/api/v1/search/words?keyword={keyword}")
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Jisho API 查詢失敗")
        return response.json()

# OCR 處理函數
def process_image(image_data: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(image_data))
        image = image.convert('L')  # 轉為灰階
        
        # 嘗試進行二值化處理
        image = image.point(lambda p: p > 128 and 255)  # 二值化處理

        # Tesseract 配置設置
        custom_config = r'--oem 3 --psm 6'  # 使用 LSTM 模型與較高的頁面分段模式
        text = pytesseract.image_to_string(image, lang='jpn', config=custom_config)

        print(f"識別的文字: {text}")
        return text.strip()
    except Exception as e:
        print(f"OCR 錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OCR 處理失敗: {str(e)}")

# API 路由 - OCR
@app.post("/api/ocr")
async def ocr_endpoint(file: UploadFile = File(...)):
    try:
        image_data = await file.read()
        if not image_data:
            raise HTTPException(status_code=400, detail="無效的圖片檔案")
        
        text = process_image(image_data)
        
        if not text:
            raise HTTPException(status_code=400, detail="無法識別文字")
        
        return {"text": text.strip(), "keyword": text.strip()}  # 傳回辨識文字並且用作 keyword 查詢
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OCR 處理失敗: {str(e)}")

# API 路由 - 查詢漢字
@app.get("/api/kanji/{keyword}")
async def kanji_info(keyword: str):
    return await query_jisho(keyword)

# HTML 頁面
@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html") as f:
        return f.read()
