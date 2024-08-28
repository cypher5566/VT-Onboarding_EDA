# VoiceTube 用戶行為分析儀表板

## 專案簡介

這個專案是一個專門用來分析 VoiceTube 用戶行為的儀表板。我們運用 Python 和 Streamlit 來處理和視覺化用戶資料，提供關於用戶成長、學習習慣、來源分布和付費情況的深入見解。

## 主要功能

- 用戶成長和學習時間偏好分析
- 學習行為分析（包含 CEFR 等級和用戶來源的交叉分析）
- 用戶來源分析
- 學習動機分布和轉換率分析
- 付費情況分析

## 安裝步驟

1. Clone 此 repository：
   ```
   git clone https://github.com/cypher5566/VT-Onboarding_EDA.git
   ```

2. 進入專案資料夾：
   ```
   cd VT-Onboarding_EDA
   ```

3. 安裝必要的套件：
   ```
   pip install -r requirements.txt
   ```

## 使用說明

1. 執行 Streamlit 應用程式：
   ```
   streamlit run app.py
   ```

2. 在瀏覽器中開啟顯示的本地網址（通常是 http://localhost:8501）。

3. 使用側邊欄上傳 CSV 檔案，然後利用各種篩選器和選項來探索資料。

## 資料需求

此應用程式需要特定格式的 CSV 檔案。請確保您的資料包含以下欄位：

- user_id
- reason
- heard_from
- cefr_level
- learning_duration
- clock
- login_method
- order_item_actual_price_twd
- （其他相關欄位...）

## 參與貢獻

歡迎提出 issues 和 pull requests。如果您想進行重大更改，請先開啟一個 issue 來討論您想要更改的內容。

## 授權條款

[MIT](https://choosealicense.com/licenses/mit/)