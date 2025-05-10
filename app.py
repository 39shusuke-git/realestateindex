import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import os

# アプリの設定
st.set_page_config(
    page_title="不動産インデックスデータベース",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSSスタイルを適用
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .stButton button {
        background-color: #3498db;
        color: white;
    }
    .stDataFrame {
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# サンプルデータの作成 (実際の実装では外部ソースからデータを取得)
@st.cache_data
def load_sample_data():
    # インデックスのリスト
    indices = [
        "東京オフィス賃料指数",
        "住宅価格指数（全国）",
        "商業施設売上高指数",
        "Jリート指数",
        "マンション価格指数（首都圏）"
    ]
    
    # サンプルデータフレームの作成
    dates = pd.date_range(start='2018-01-01', end='2023-12-31', freq='M')
    data = {}
    
    for idx in indices:
        # ランダムな時系列データを生成（実際はAPIや外部ソースから取得）
        if "賃料" in idx or "価格" in idx:
            base = 100
            trend = np.linspace(0, 30, len(dates))  # 上昇トレンド
        elif "売上高" in idx:
            base = 100
            trend = np.linspace(0, 20, len(dates))  # 緩やかな上昇
        else:
            base = 100
            trend = np.linspace(0, 15, len(dates))  # より緩やかな上昇
            
        seasonal = 5 * np.sin(np.linspace(0, 12*np.pi, len(dates)))  # 季節変動
        noise = np.random.normal(0, 3, len(dates))  # ランダムノイズ
        
        values = base + trend + seasonal + noise
        data[idx] = values
    
    # データフレームの作成
    df = pd.DataFrame(data, index=dates)
    return df

# アプリのメイン関数
def main():
    # サイドバー
    st.sidebar.title("不動産インデックスデータベース")
    st.sidebar.image("https://via.placeholder.com/150?text=RE+Index", width=150)
    
    # インデックス選択
    st.sidebar.header("インデックス選択")
    df = load_sample_data()
    available_indices = df.columns.tolist()
    selected_indices = st.sidebar.multiselect(
        "表示するインデックスを選択",
        available_indices,
        default=available_indices[:2]
    )
    
    # 日付範囲フィルター
    st.sidebar.header("期間選択")
    date_range = st.sidebar.date_input(
        "期間を選択",
        value=(df.index.min().date(), df.index.max().date()),
        min_value=df.index.min().date(),
        max_value=df.index.max().date()
    )
    
    # 日付フィルタリング
    if len(date_range) == 2:
        start_date, end_date = date_range
        mask = (df.index >= pd.Timestamp(start_date)) & (df.index <= pd.Timestamp(end_date))
        filtered_df = df.loc[mask]
    else:
        filtered_df = df
    
    # メイン画面
    st.title("不動産インデックスデータベース")
    
    # タブの作成
    tab1, tab2, tab3 = st.tabs(["グラフ表示", "データ表示", "比較分析"])
    
    with tab1:
        st.header("インデックスの時系列推移")
        
        if not selected_indices:
            st.warning("サイドバーからインデックスを選択してください")
        else:
            # グラフ表示
            fig = go.Figure()
            
            for idx in selected_indices:
                fig.add_trace(
                    go.Scatter(
                        x=filtered_df.index,
                        y=filtered_df[idx],
                        mode='lines',
                        name=idx
                    )
                )
            
            fig.update_layout(
                title="選択したインデックスの推移",
                xaxis_title="日付",
                yaxis_title="指数値",
                legend_title="インデックス",
                height=500,
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 変化率の計算と表示
            if len(selected_indices) > 0:
                st.subheader("期間内の変化率")
                
                change_data = []
                for idx in selected_indices:
                    start_value = filtered_df[idx].iloc[0]
                    end_value = filtered_df[idx].iloc[-1]
                    percent_change = ((end_value - start_value) / start_value) * 100
                    
                    change_data.append({
                        "インデックス": idx,
                        "開始値": round(start_value, 2),
                        "終了値": round(end_value, 2),
                        "変化率 (%)": round(percent_change, 2)
                    })
                
                change_df = pd.DataFrame(change_data)
                st.dataframe(change_df, use_container_width=True)
    
    with tab2:
        st.header("インデックスデータ")
        
        if not selected_indices:
            st.warning("サイドバーからインデックスを選択してください")
        else:
            # データ表示
            display_df = filtered_df[selected_indices].copy()
            display_df.index = display_df.index.strftime('%Y-%m-%d')
            
            st.dataframe(display_df.reset_index().rename(columns={"index": "日付"}), use_container_width=True)
            
            # ダウンロードボタン
            csv = display_df.to_csv()
            st.download_button(
                label="CSVダウンロード",
                data=csv,
                file_name="real_estate_indices.csv",
                mime="text/csv",
            )
    
    with tab3:
        st.header("インデックス比較分析")
        
        if len(selected_indices) < 2:
            st.warning("比較するには2つ以上のインデックスを選択してください")
        else:
            # 相関分析
            st.subheader("インデックス間の相関係数")
            corr_matrix = filtered_df[selected_indices].corr()
            
            # ヒートマップ表示
            fig = px.imshow(
                corr_matrix,
                text_auto=True,
                color_continuous_scale="Blues",
                labels=dict(x="インデックス", y="インデックス", color="相関係数")
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # 正規化比較
            st.subheader("正規化比較（開始値=100）")
            
            normalized_df = pd.DataFrame()
            for idx in selected_indices:
                normalized_df[idx] = (filtered_df[idx] / filtered_df[idx].iloc[0]) * 100
            
            fig = px.line(
                normalized_df,
                labels={"value": "正規化指数（開始=100）", "variable": "インデックス"},
                title="基準化したインデックス比較"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # フッター情報
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: gray; font-size: 0.8em;">
        不動産インデックスデータベース | データ最終更新日: 2023-12-31
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()