import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import plotly.graph_objects as go

# 載入數據
@st.cache_data
def load_data(uploaded_file):
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            # 處理 'clock' 列
            df['clock'] = pd.to_datetime(df['clock'], format='%H:%M:%S').dt.time
            
            # 處理 'cefr_level' 列
            df['cefr_level'] = df['cefr_level'].fillna(0).astype(int)
            
            # 處理 'learning_duration' 列
            df['learning_duration'] = pd.to_numeric(df['learning_duration'], errors='coerce')
            
            # 處理 'order_item_actual_price_twd' 列
            df['order_item_actual_price_twd'] = pd.to_numeric(df['order_item_actual_price_twd'], errors='coerce')
            
            return df
        except Exception as e:
            st.error(f"讀取文件時發生錯誤: {str(e)}")
            return None
    return None

# CEFR 級別映射
def map_cefr_level(level):
    mapping = {1: '初級 (A2)', 3: '中級 (B1)', 5: '中高級 (B2)', 7: '高級 (C1)'}
    return mapping.get(level, '未知')

# Reason 映射
reason_map = {
    'To converse with foreigners': '與外國人交談',
    'For academic purposes or further education': '課業, 升學需要',
    'For professional needs': '職場需要',
    'For travel': '旅遊',
    'To prepare for English exams': '考英文相關檢定',
    'To get ready for studying or working abroad': '準備出國讀書/工作',
    'To find teaching materials for students or children': '找學生/小孩的教材'
}

# 處理離群值 
def remove_outliers(df, column, lower_percentile=1, upper_percentile=99):
    lower = np.percentile(df[column].dropna(), lower_percentile)
    upper = np.percentile(df[column].dropna(), upper_percentile)
    return df[(df[column] >= lower) & (df[column] <= upper)]

# 用戶增長和學習時間偏好分析
def user_growth_time_preference(df):
    st.header('用戶增長和學習時間偏好分析')
    
    # 用戶偏好的學習時間分佈
    preferred_time = df['clock'].dropna().apply(lambda x: x.strftime('%H:%M')).value_counts().sort_index()
    preferred_time = preferred_time.reindex(pd.date_range(start='00:00', end='23:59', freq='h').strftime('%H:%M'), fill_value=0)
    
    fig = px.bar(x=preferred_time.index, y=preferred_time.values, 
                 labels={'x': '時間', 'y': '用戶數'}, 
                 title='用戶偏好的學習時間分佈')
    fig.update_layout(xaxis_title='時間', yaxis_title='用戶數')
    fig.update_xaxes(tickangle=45, tickmode='array', tickvals=preferred_time.index[::2])
    st.plotly_chart(fig)

# 學習行為分析
def learning_behavior(df):
    st.header('學習行為分析')
    
    # CEFR 級別和用戶來源的交叉分析
    df['cefr_category'] = df['cefr_level'].apply(map_cefr_level)
    cefr_order = ['初級 (A2)', '中級 (B1)', '中高級 (B2)', '高級 (C1)']
    
    # 過濾掉 '未知' 級別
    df_filtered = df[df['cefr_category'].isin(cefr_order)]
    
    # 計算每個 CEFR 級別和來源的用戶數量
    cross_analysis = df_filtered.groupby(['cefr_category', 'heard_from']).size().unstack(fill_value=0)
    
    # 選擇前 7 個最常見的來源
    top_sources = cross_analysis.sum().nlargest(7).index
    cross_analysis = cross_analysis[top_sources]
    
    # 重新排序 CEFR 級別
    cross_analysis = cross_analysis.reindex(cefr_order)
    
    # 創建分組柱狀圖
    fig = go.Figure()
    
    for source in top_sources:
        fig.add_trace(go.Bar(
            x=cross_analysis.index,
            y=cross_analysis[source],
            name=source
        ))
    
    fig.update_layout(
        title='CEFR 級別和用戶來源的交叉分析',
        xaxis_title='CEFR 級別',
        yaxis_title='用戶數量',
        barmode='group'
    )
    
    st.plotly_chart(fig)

    # 處理離群值
    df_filtered = remove_outliers(df, 'learning_duration')
    
    # 學習時長分佈
    fig = px.histogram(df_filtered, x='learning_duration', nbins=50, 
                       title='學習時長分佈 (排除離群值)')
    fig.update_layout(xaxis_title='學習時長 (分鐘)', yaxis_title='頻率')
    st.plotly_chart(fig)

# 用戶來源分析
def user_source_analysis(df):
    st.header('用戶來源分析')

    # 用戶來源分佈
    source_counts = df['heard_from'].value_counts()
    fig_source = px.pie(values=source_counts.values, names=source_counts.index, title='用戶來源分佈')
    st.plotly_chart(fig_source)

    # 登入方式分佈
    login_counts = df['login_method'].value_counts()
    fig_login = px.pie(values=login_counts.values, names=login_counts.index, title='登入方式分佈')
    st.plotly_chart(fig_login)

    # 計算 iOS 和 Android 的比例
    ios_count = login_counts.get('iOS VoiceTube', 0) + login_counts.get('iOS Dictionary', 0) + login_counts.get('iOS Dori', 0)
    android_count = login_counts.get('Android VoiceTube', 0) + login_counts.get('Android Dictionary', 0) + login_counts.get('Android Dori', 0)
    total_count = ios_count + android_count
    ios_percentage = ios_count / total_count * 100
    android_percentage = android_count / total_count * 100

    st.write(f"iOS 用戶比例: {ios_percentage:.2f}%")
    st.write(f"Android 用戶比例: {android_percentage:.2f}%")

# 學習原因分佈和轉換率
def reason_distribution_and_conversion(df):
    st.header('學習原因分佈和轉換率')
    
    # 計算學習原因分佈
    df['reason_short'] = df['reason'].map(reason_map)
    reason_counts = df['reason_short'].value_counts().reset_index()
    reason_counts.columns = ['reason', 'count']
    
    # 計算轉換率
    reason_conversion = df.groupby('reason_short').agg({
        'user_id': 'count',
        'order_item_actual_price_twd': lambda x: (x > 0).sum()
    }).reset_index()
    reason_conversion['conversion_rate'] = reason_conversion['order_item_actual_price_twd'] / reason_conversion['user_id']
    
    # 合併數據
    merged_data = pd.merge(reason_counts, reason_conversion[['reason_short', 'conversion_rate']], 
                           left_on='reason', right_on='reason_short')
    
    # 排序數據
    merged_data = merged_data.sort_values('count', ascending=False)
    
    # 創建雙軸圖表
    fig = go.Figure()
    
    # 添加柱狀圖（學習原因分佈）
    fig.add_trace(go.Bar(
        x=merged_data['reason'],
        y=merged_data['count'],
        name='用戶數量',
        yaxis='y',
        offsetgroup=0
    ))
    
    # 添加折線圖（轉換率）
    fig.add_trace(go.Scatter(
        x=merged_data['reason'],
        y=merged_data['conversion_rate'],
        name='轉換率',
        yaxis='y2',
        mode='lines+markers'
    ))
    
    # 更新布局
    fig.update_layout(
        title='學習原因分佈和付費轉換率',
        xaxis=dict(title='學習原因'),
        yaxis=dict(title='用戶數量', side='left'),
        yaxis2=dict(title='付費轉換率', side='right', overlaying='y', tickformat='.1%'),
        legend=dict(x=1.1, y=1),
        barmode='group'
    )
    
    # 調整 x 軸標籤角度
    fig.update_xaxes(tickangle=45)
    
    st.plotly_chart(fig)

# 付費分析
def payment_analysis(df):
    st.header('付費分析')
    
    # 付費用戶比例
    paid_users = df[df['order_item_actual_price_twd'] > 0]['user_id'].nunique()
    total_users = df['user_id'].nunique()
    paid_ratio = paid_users / total_users

    fig = px.pie(values=[paid_users, total_users - paid_users], 
                 names=['付費用戶', '免費用戶'], 
                 title='付費用戶比例')
    st.plotly_chart(fig)

    # 付費金額分佈
    paid_df = df[df['order_item_actual_price_twd'] > 0]
    fig = px.histogram(paid_df, x='order_item_actual_price_twd', 
                       title='付費金額分佈')
    fig.update_layout(xaxis_title='付費金額 (TWD)', yaxis_title='頻率')
    st.plotly_chart(fig)


# 主程序
def main():
    st.title('VoiceTube 用戶行為分析儀表板')

    uploaded_file = st.sidebar.file_uploader("選擇 CSV 文件", type="csv")
    df = load_data(uploaded_file)

    if df is not None:
        # 將平台選擇移到側邊欄
        platform = st.sidebar.selectbox('選擇平台', ['全部', 'iOS', 'Android'])

        # 根據選擇過濾數據
        if platform == 'iOS':
            df_filtered = df[df['login_method'].str.contains('iOS', na=False)]
        elif platform == 'Android':
            df_filtered = df[df['login_method'].str.contains('Android', na=False)]
        else:
            df_filtered = df

        # 添加一個重置按鈕
        if st.sidebar.button('重置過濾器'):
            platform = '全部'
            df_filtered = df

        # 顯示當前選擇的平台
        st.sidebar.write(f"當前選擇的平台: {platform}")

        # 顯示過濾後的數據量
        st.sidebar.write(f"過濾後的數據量: {len(df_filtered)}")

        user_growth_time_preference(df_filtered)
        learning_behavior(df_filtered)
        user_source_analysis(df_filtered)
        reason_distribution_and_conversion(df_filtered)
        payment_analysis(df_filtered)
    else:
        st.warning("請上傳 CSV 文件")

if __name__ == "__main__":
    main()