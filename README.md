# Penny 生活英文・邊走邊聽

快走、運動時用耳朵練生活英文的 iPhone 網頁 App。每個主題 30 句美國生活口語，做成一段約 30 分鐘的音檔，鎖螢幕也能繼續播。

## 每段 30 分鐘怎麼播

1. 第一輪・跟著唸：英文唸三次，每次後面留空白讓你跟著唸，再唸一次中文
2. 第二輪・聽中文說英文：先唸中文，留空白讓你自己說英文，再播英文對答案
3. 第三輪：再跟著唸一次
4. 第四輪：再聽中文說英文
5. 加強練習：順序打亂的回想練習，補到約 30 分鐘

App 畫面會同步顯示目前的句子，可以上一句／下一句、點句子直接跳過去，句子旁可勾「背熟」，進度存在手機裡。iPhone 鎖定畫面和耳機按鍵也能控制播放。

## 目前的主題

- 餐廳與咖啡店（點餐、外帶、結帳）
- 機場、飯店與問路（出國旅遊必備）
- 美劇日常反應（看劇最常聽到的口語）

## 新增或修改句子

編輯 `data/themes.json`，每句是 `["英文", "中文"]`，一個主題建議 30 句。推到 `main` 之後，GitHub Actions 會自動用語音合成（英文美國腔、中文台灣腔）產生音檔並更新網站。

## 發布設定（只要做一次）

GitHub repo → Settings → Pages → Build and deployment → Source 選 **GitHub Actions**。

注意：免費帳號的 GitHub Pages 只能用在公開 repo。

## 在 iPhone 上使用

用 Safari 打開 Pages 網址 → 分享按鈕 →「加入主畫面」，之後就像一般 App 一樣從主畫面打開。

## 在電腦上自己產生音檔

```bash
pip install edge-tts   # 另外需要 ffmpeg
python scripts/build_audio.py           # 產生 audio/*.mp3
python scripts/build_audio.py --fake    # 用嗶聲代替語音，測試流程用
python -m http.server                   # 然後打開 http://localhost:8000
```
