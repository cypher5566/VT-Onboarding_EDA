import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def load_data(uploaded_file):
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.write("數據列名:", df.columns.tolist())  # 顯示所有列名，幫助調試
            
            # 檢查必要的列是否存在
            required_columns = ['reason', 'heard_from', 'cefr_level', 'learning_duration']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                st.error(f"缺少以下必要的列: {', '.join(missing_columns)}")
                return None

            # 處理 NULL 值
            df = df.dropna()

            # 檢查 'clock' 列是否存在，如果存在則轉換
            if 'clock' in df.columns:
                df['clock'] = pd.to_datetime(df['clock'])
            else:
                st.warning("數據中沒有 'clock' 列，某些分析可能無法進行。")

            # 處理 learning_duration 的異常值
            Q1 = df['learning_duration'].quantile(0.25)
            Q3 = df['learning_duration'].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # 將異常值替換為上下界
            df['learning_duration'] = np.clip(df['learning_duration'], lower_bound, upper_bound)
            
            # 創建 reason 的簡短標籤
            reason_map = {
                'To converse with foreigners': '與外國人交談',
                'For academic purposes or further education': '課業, 升學需要',
                'For professional needs': '職場需要',
                'For travel': '旅遊',
                'To prepare for English exams': '考英文相關檢定',
                'To get ready for studying or working abroad': '準備出國讀書/工作',
                'To find teaching materials for students or children': '找學生/小孩的教材'
            }
            df['reason_short'] = df['reason'].map(reason_map)
            
            return df
        except Exception as e:
            st.error(f"讀取文件時發生錯誤: {str(e)}")
            return None
    return None

# 將 file_uploader 移到主程序中
uploaded_file = st.file_uploader("選擇 CSV 文件", type="csv")
df = load_data(uploaded_file)

if df is not None:
    st.title('VoiceTube 用戶 Onboarding 數據分析')

    # 1. 使用組合圖表
    st.header('1. 學習原因與時長分析')
    fig = go.Figure()
    reasons = df['reason_short'].value_counts().sort_values(ascending=True)
    avg_duration = df.groupby('reason_short')['learning_duration'].mean().loc[reasons.index]
    
    fig.add_trace(go.Bar(y=reasons.index, x=reasons.values, name='數量', orientation='h'))
    fig.add_trace(go.Scatter(y=avg_duration.index, x=avg_duration.values, name='平均學習時長', xaxis='x2'))
    
    fig.update_layout(
        xaxis=dict(title='數量'),
        xaxis2=dict(title='平均學習時長', overlaying='x', side='top'),
        yaxis=dict(title='學習原因'),
        barmode='group',
        height=500
    )
    st.plotly_chart(fig)

    # 2. 來源分析比較
    st.header('2. 來源分析比較')

    # 創建 CEFR 級別的映射
    cefr_map = {
        1: '初級',
        3: '中級', 
        5: '中高級',
        7: '高級'
    }

    # 將 CEFR 級別映射到新的分類
    df['cefr_category'] = df['cefr_level'].astype(int).map(cefr_map)

    # 創分組直方圖
    fig = px.histogram(df, x='cefr_category', color='heard_from', barmode='group',
                       title='不同來源用戶的 CEFR 級別分佈',
                       labels={'cefr_category': 'CEFR 級別', 'count': '用戶數量', 'heard_from': '來源'},
                       category_orders={'cefr_category': ['初級', '中級', '中高級', '高級']},
                       height=600)

    fig.update_layout(
        legend_title_text='來源',
        xaxis_title='CEFR 級別',
        yaxis_title='用戶數量',
        bargap=0.2,  # 增加組間距
        bargroupgap=0.1  # 增加組內距
    )

    # 確保 y 軸從 0 開始,並自動調整範圍
    fig.update_yaxes(rangemode='tozero', autorange=True)

    st.plotly_chart(fig)

    # 添加來源分佈餅圖
    st.subheader('用戶來源分佈')
    fig_pie = px.pie(df, names='heard_from', title='用戶來源分佈')
    st.plotly_chart(fig_pie)

    # 3. 根據目標選擇圖表
    st.header('3. 學習時長分佈')
    fig = px.box(df, y='reason_short', x='learning_duration', title='不同學習原因的學習時長分佈')
    fig.update_layout(yaxis_title='學習原因', xaxis_title='學習時長')
    st.plotly_chart(fig)

    # 4. 數據清理（已在 load_data 函數中處理）

    # 5. 儀表板
    st.header('5. 綜合儀表板')
    col1, col2 = st.columns(2)

    with col1:
        fig = px.pie(df, names='heard_from', title='用戶來源分佈')
        st.plotly_chart(fig)

    with col2:
        df['hour'] = df['clock'].dt.hour
        fig = px.histogram(df, x='hour', title='學習時間分佈')
        st.plotly_chart(fig)

    # 額外的洞見
    st.header('額外洞見')
    st.write('CEFR 級別與學習時長的關係')

    # 創建 CEFR 級別的映射
    cefr_map = {
        1: '初級 (A2)',
        3: '中級 (B1)',
        5: '中高級 (B2)',
        7: '高級 (C1)'
    }

    # 將 CEFR 級別映射到新的分類
    df['cefr_category'] = df['cefr_level'].map(cefr_map)

    # 計算每個 CEFR 級別的平均學習時長
    avg_duration = df.groupby('cefr_category')['learning_duration'].mean().reset_index()

    # 創建箱型圖
    fig = px.box(df, x='cefr_category', y='learning_duration', color='reason_short',
                 category_orders={'cefr_category': ['初級 (A1-A2)', '中級 (B1-B2)', '中高級 (C1)', '高級 (C2)']},
                 labels={'cefr_category': 'CEFR 級別', 'learning_duration': '學習時長 (分鐘)', 'reason_short': '學習原因'},
                 title='CEFR 級別 vs 學習時長')

    # 添加平均值的標記
    for idx, row in avg_duration.iterrows():
        fig.add_annotation(x=row['cefr_category'], y=row['learning_duration'],
                           text=f"平均: {row['learning_duration']:.2f}",
                           showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2,
                           arrowcolor="#636363", ax=20, ay=-30)

    fig.update_layout(height=600, boxmode='group')
    st.plotly_chart(fig)

    # 添加一些統計信息
    st.write("各 CEFR 級別的學習時長統計:")
    st.write(df.groupby('cefr_category')['learning_duration'].describe())

    # 新增的分析部分

    # 1. 學習時間與 CEFR 級別的關係
    st.header('學習時間與 CEFR 級別的關係')
    df['hour'] = pd.to_datetime(df['clock']).dt.hour
    fig = px.histogram(df, x='hour', color='cefr_category', barmode='group',
                       labels={'hour': '學習時間 (小時)', 'count': '用戶數量', 'cefr_category': 'CEFR 級別'},
                       title='不同 CEFR 級別用戶的學習時間分佈')
    st.plotly_chart(fig)

    # 2. 學習原因與來源的關聯
    st.header('學習原因與來源的關聯')
    fig = px.sunburst(df, path=['reason_short', 'heard_from'], values='id',
                      title='學習原因與來源的關係')
    st.plotly_chart(fig)

    # 3. 學習時長與學習時間的關係
    st.header('學習時長與學習時間的關係')
    df['time_period'] = pd.cut(df['hour'], bins=[0, 6, 12, 18, 24], 
                               labels=['凌晨 (0-6)', '上午 (6-12)', '下午 (12-18)', '晚上 (18-24)'])
    fig = px.box(df, x='time_period', y='learning_duration',
                 labels={'time_period': '時間段', 'learning_duration': '學習時長 (分鐘)'},
                 title='不同時間段的學習時長分佈')
    st.plotly_chart(fig)

    # 4. CEFR 級別與學習原因的分佈
    st.header('CEFR 級別與學習原因的分佈')
    cefr_reason = df.groupby(['cefr_category', 'reason_short']).size().unstack(fill_value=0)
    cefr_reason_pct = cefr_reason.div(cefr_reason.sum(axis=1), axis=0)
    fig = px.imshow(cefr_reason_pct.T, text_auto=True, aspect="auto",
                    labels=dict(x="CEFR 級別", y="學習原因", color="比例"),
                    title="CEFR 級別與學習原因的熱力圖")
    st.plotly_chart(fig)

    # 登錄方式分析
    st.header('登錄方式分析')
    login_method_counts = df['login_method'].value_counts()
    fig = px.pie(values=login_method_counts.values, names=login_method_counts.index, title='用戶登錄方式分佈')
    st.plotly_chart(fig)

    # 登錄方式與學習時長的關係
    fig = px.box(df, x='login_method', y='learning_duration', title='不同登錄方式的學習時長分佈')
    st.plotly_chart(fig)

    # 學習原因與 CEFR 級別的關係
    st.header('學習原因與 CEFR 級別的關係')
    reason_cefr = pd.crosstab(df['reason_short'], df['cefr_category'], normalize='index')
    fig = px.imshow(reason_cefr, text_auto=True, aspect="auto",
                    labels=dict(x="CEFR 級別", y="學習原因", color="比例"),
                    title="學習原因與 CEFR 級別的關係熱力圖")
    st.plotly_chart(fig)

    # 用戶來源與學習時長的關係
    st.header('用戶來源與學習時長的關係')
    fig = px.box(df, x='heard_from', y='learning_duration', color='cefr_category',
                 title='不同來源用戶的學習時長分佈')
    st.plotly_chart(fig)

    # 學習持續時間分析
    st.header('學習持續時間分析')

    # 確保 learning_duration 沒有負值
    df['learning_duration'] = df['learning_duration'].clip(lower=0)

    # 動態設置分組邊界
    max_duration = df['learning_duration'].max()
    bins = [0, 5, 15, 30, 60, max(61, max_duration)]
    labels = ['0-5分鐘', '6-15分鐘', '16-30分鐘', '31-60分鐘', '60分鐘以上']

    df['duration_category'] = pd.cut(df['learning_duration'], 
                                     bins=bins,
                                     labels=labels,
                                     include_lowest=True)

    fig = px.histogram(df, x='duration_category', color='reason_short', barmode='group',
                       category_orders={'duration_category': labels},
                       title='不同學習原因的學習持續時間分佈')
    st.plotly_chart(fig)

    # 添加一些統計信息
    st.write("各學習持續時間類別的統計:")
    duration_stats = df.groupby('duration_category').agg({
        'id': 'count',
        'learning_duration': ['mean', 'median', 'min', 'max']
    }).reset_index()
    duration_stats.columns = ['持續時間類別', '用戶數', '平均時長', '中位數時長', '最短時長', '最長時長']
    st.write(duration_stats)

else:
    st.warning("請上傳 CSV 文件")