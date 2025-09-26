import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import cv2
import numpy as np
from PIL import Image
import requests
import json
from pyzbar import pyzbar
import io
import base64

# ページ設定（高齢者向け）
st.set_page_config(
    page_title="らくらく冷蔵庫管理",
    page_icon="📱",
    layout="wide"
)

# 高齢者向けのCSSスタイル（さらに大きく、見やすく）
st.markdown("""
<style>
    /* 全体的に文字を大きく */
    .stApp {
        font-size: 20px;
    }
    
    /* ヘッダーをより大きく */
    h1 {
        font-size: 3.5rem !important;
        text-align: center;
        color: #2E8B57 !important;
        margin-bottom: 2rem !important;
    }
    
    h2 {
        font-size: 2.5rem !important;
        color: #4169E1 !important;
    }
    
    h3 {
        font-size: 2rem !important;
        color: #333 !important;
    }
    
    /* ボタンを非常に大きく */
    .stButton > button {
        font-size: 24px !important;
        height: 80px !important;
        font-weight: bold !important;
        border-radius: 15px !important;
        border: 3px solid #333 !important;
    }
    
    /* カメラボタン専用スタイル */
    .camera-button {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4) !important;
        color: white !important;
        font-size: 28px !important;
        height: 100px !important;
    }
    
    /* バーコードボタン専用スタイル */
    .barcode-button {
        background: linear-gradient(45deg, #667eea, #764ba2) !important;
        color: white !important;
        font-size: 28px !important;
        height: 100px !important;
    }
    
    /* 入力フィールドを大きく */
    .stTextInput > div > div > input {
        font-size: 22px !important;
        height: 60px !important;
        border: 3px solid #ccc !important;
    }
    
    /* 警告ボックスをより目立つように */
    .urgent-warning {
        background-color: #ff4444 !important;
        color: white !important;
        font-size: 28px !important;
        font-weight: bold !important;
        text-align: center !important;
        padding: 30px !important;
        border-radius: 15px !important;
        animation: blink 1s infinite !important;
    }
    
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    /* 食材カードスタイル */
    .food-card {
        padding: 25px;
        margin: 15px 0;
        border-radius: 15px;
        border: 4px solid;
        font-size: 20px;
    }
    
    .expired { border-color: #ff0000; background-color: #ffe6e6; }
    .warning { border-color: #ff8800; background-color: #fff3e0; }
    .safe { border-color: #00aa00; background-color: #e8f5e8; }
</style>
""", unsafe_allow_html=True)

# セッション状態の初期化
def init_session_state():
    if 'fridge_items' not in st.session_state:
        st.session_state.fridge_items = []
    if 'camera_enabled' not in st.session_state:
        st.session_state.camera_enabled = False

init_session_state()

# バーコード読み取り機能（模擬版）
def mock_barcode_lookup(barcode):
    """バーコードから商品情報を取得（模擬版）"""
    # 実際の実装では、商品データベースAPIを使用
    mock_products = {
        "4901777123456": {"name": "牛乳", "category": "乳製品", "typical_days": 7},
        "4902777654321": {"name": "食パン", "category": "パン類", "typical_days": 4},
        "4903777987654": {"name": "卵", "category": "卵類", "typical_days": 14},
        "4904777456789": {"name": "豆腐", "category": "豆腐", "typical_days": 5},
        "4905777321098": {"name": "納豆", "category": "発酵食品", "typical_days": 7},
    }
    return mock_products.get(barcode, {"name": "不明な商品", "category": "その他", "typical_days": 3})

def decode_barcode_from_image(image):
    """画像からバーコードを読み取り"""
    try:
        # PIL ImageをOpenCV形式に変換
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # バーコードを検出
        barcodes = pyzbar.decode(opencv_image)
        
        if barcodes:
            return barcodes[0].data.decode('utf-8')
        return None
    except Exception as e:
        st.error(f"バーコード読み取りエラー: {str(e)}")
        return None

def analyze_expiry_date_image(image):
    """賞味期限の画像を解析（OCR機能の模擬版）"""
    # 実際の実装では、OCRライブラリ（pytesseract等）を使用
    # ここでは模擬的に今日から数日後の日付を返す
    import random
    days_ahead = random.randint(3, 14)
    expiry_date = date.today() + timedelta(days=days_ahead)
    return expiry_date

def check_expiring_soon(expiry_date, days=3):
    """賞味期限が近いかチェック"""
    if isinstance(expiry_date, str):
        expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
    today = date.today()
    diff = (expiry_date - today).days
    return 0 <= diff <= days

def check_expired(expiry_date):
    """賞味期限が切れているかチェック"""
    if isinstance(expiry_date, str):
        expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
    return expiry_date < date.today()

def get_days_until_expiry(expiry_date):
    """賞味期限まであと何日かを計算"""
    if isinstance(expiry_date, str):
        expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
    today = date.today()
    return (expiry_date - today).days

# メインアプリケーション
st.title("📱 らくらく冷蔵庫管理")
st.markdown("### 🎯 バーコードと写真で簡単管理！")

# 緊急警告の表示
urgent_items = [item for item in st.session_state.fridge_items if check_expired(item['expiry_date'])]
if urgent_items:
    st.markdown(f"""
    <div class="urgent-warning">
        🚨 緊急！🚨<br>
        {len(urgent_items)}個の食材が期限切れです！<br>
        すぐに確認してください！
    </div>
    """, unsafe_allow_html=True)

# 警告アイテムの表示
warning_items = [item for item in st.session_state.fridge_items if check_expiring_soon(item['expiry_date'])]
if warning_items:
    st.warning(f"⚠️ 注意：{len(warning_items)}個の食材がもうすぐ期限です！")

st.markdown("---")

# 大きなボタンで機能選択
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📷 写真で登録")
    if st.button("📸 バーコードを撮影", key="barcode_camera", use_container_width=True):
        st.session_state.current_page = "barcode_scan"

with col2:
    st.markdown("### 📅 期限を撮影")
    if st.button("📆 賞味期限を撮影", key="expiry_camera", use_container_width=True):
        st.session_state.current_page = "expiry_scan"

col3, col4 = st.columns(2)

with col3:
    if st.button("🥬 食材一覧を見る", key="view_items", use_container_width=True):
        st.session_state.current_page = "view_items"

with col4:
    if st.button("✍️ 手動で登録", key="manual_add", use_container_width=True):
        st.session_state.current_page = "manual_add"

# デフォルトページ設定
if 'current_page' not in st.session_state:
    st.session_state.current_page = "view_items"

st.markdown("---")

# バーコードスキャンページ
if st.session_state.current_page == "barcode_scan":
    st.header("📷 バーコードを読み取り")
    
    st.markdown("""
    ### 📝 使い方：
    1. **商品のバーコード部分を撮影**してください
    2. **はっきりと見えるように**撮影してください
    3. **光の反射**に注意してください
    """)
    
    # カメラ入力
    barcode_image = st.camera_input("バーコードを撮影してください", key="barcode_cam")
    
    if barcode_image is not None:
        # 撮影した画像を表示
        image = Image.open(barcode_image)
        st.image(image, caption="撮影した画像", width=300)
        
        # バーコード読み取り処理
        with st.spinner("バーコードを読み取っています..."):
            barcode_data = decode_barcode_from_image(image)
            
            if barcode_data:
                st.success(f"✅ バーコードを読み取りました: {barcode_data}")
                
                # 商品情報取得
                product_info = mock_barcode_lookup(barcode_data)
                st.info(f"📦 商品名: {product_info['name']}")
                
                # 購入日入力
                purchase_date = st.date_input("いつ買いましたか？", value=date.today())
                
                # 推定賞味期限表示
                estimated_expiry = purchase_date + timedelta(days=product_info['typical_days'])
                st.info(f"📅 推定賞味期限: {estimated_expiry}")
                
                if st.button("この情報で登録する", use_container_width=True):
                    new_item = {
                        'id': len(st.session_state.fridge_items) + 1,
                        'name': product_info['name'],
                        'barcode': barcode_data,
                        'purchase_date': purchase_date,
                        'expiry_date': estimated_expiry,
                        'method': 'バーコード'
                    }
                    st.session_state.fridge_items.append(new_item)
                    st.success("✅ 食材を登録しました！")
                    st.balloons()
            else:
                st.error("❌ バーコードが読み取れませんでした。もう一度撮影してください。")

# 賞味期限スキャンページ
elif st.session_state.current_page == "expiry_scan":
    st.header("📅 賞味期限を読み取り")
    
    st.markdown("""
    ### 📝 使い方：
    1. **パッケージの賞味期限表示**を撮影してください
    2. **数字がはっきり見える**ように撮影してください
    3. **影にならない**ように注意してください
    """)
    
    # 食材名入力
    item_name = st.text_input("食材の名前を入力してください", placeholder="例：牛乳、卵、パン")
    
    # カメラ入力
    expiry_image = st.camera_input("賞味期限を撮影してください", key="expiry_cam")
    
    if expiry_image is not None and item_name:
        # 撮影した画像を表示
        image = Image.open(expiry_image)
        st.image(image, caption="撮影した画像", width=300)
        
        # 賞味期限読み取り処理
        with st.spinner("賞味期限を読み取っています..."):
            expiry_date = analyze_expiry_date_image(image)
            st.success(f"✅ 賞味期限: {expiry_date}")
            
            # 購入日入力
            purchase_date = st.date_input("いつ買いましたか？", value=date.today())
            
            if st.button("この情報で登録する", use_container_width=True):
                new_item = {
                    'id': len(st.session_state.fridge_items) + 1,
                    'name': item_name,
                    'purchase_date': purchase_date,
                    'expiry_date': expiry_date,
                    'method': '写真読み取り'
                }
                st.session_state.fridge_items.append(new_item)
                st.success("✅ 食材を登録しました！")
                st.balloons()

# 食材一覧ページ
elif st.session_state.current_page == "view_items":
    st.header("🥬 冷蔵庫の食材一覧")
    
    if not st.session_state.fridge_items:
        st.info("📝 まだ食材が登録されていません。バーコードや写真で登録してみましょう！")
    else:
        # 食材を期限順にソート
        sorted_items = sorted(st.session_state.fridge_items, key=lambda x: x['expiry_date'])
        
        for item in sorted_items:
            days_left = get_days_until_expiry(item['expiry_date'])
            
            # 状態に応じてスタイルを決定
            if days_left < 0:
                card_class = "expired"
                status_icon = "🚨"
                status_text = f"期限切れ（{abs(days_left)}日経過）"
                status_color = "#ff0000"
            elif days_left <= 3:
                card_class = "warning"
                status_icon = "⚠️"
                status_text = f"あと{days_left}日で期限"
                status_color = "#ff8800"
            else:
                card_class = "safe"
                status_icon = "✅"
                status_text = f"あと{days_left}日"
                status_color = "#00aa00"
            
            # 食材カード表示
            st.markdown(f"""
            <div class="food-card {card_class}">
                <h3>{status_icon} {item['name']}</h3>
                <p><strong>購入日:</strong> {item['purchase_date']}</p>
                <p><strong>賞味期限:</strong> {item['expiry_date']}</p>
                <p style="color: {status_color}; font-weight: bold; font-size: 22px;">
                    {status_text}
                </p>
                <p><small>登録方法: {item.get('method', '手動')}</small></p>
            </div>
            """, unsafe_allow_html=True)
            
            # 削除ボタン
            if st.button(f"🗑️ {item['name']}を削除", key=f"del_{item['id']}"):
                st.session_state.fridge_items = [x for x in st.session_state.fridge_items if x['id'] != item['id']]
                st.rerun()
            
            st.markdown("---")

# 手動登録ページ
elif st.session_state.current_page == "manual_add":
    st.header("✍️ 手動で食材を登録")
    
    name = st.text_input("食材の名前", placeholder="例：トマト、牛乳、卵")
    
    col1, col2 = st.columns(2)
    with col1:
        purchase_date = st.date_input("いつ買いましたか？", value=date.today())
    
    with col2:
        expiry_date = st.date_input("賞味期限はいつですか？", 
                                   value=date.today() + timedelta(days=7),
                                   min_value=date.today())
    
    if st.button("📝 登録する", use_container_width=True):
        if name.strip():
            new_item = {
                'id': len(st.session_state.fridge_items) + 1,
                'name': name.strip(),
                'purchase_date': purchase_date,
                'expiry_date': expiry_date,
                'method': '手動入力'
            }
            st.session_state.fridge_items.append(new_item)
            st.success(f"✅ {name}を登録しました！")
            st.rerun()

# 今日食べるべき食材の通知
st.markdown("---")
st.header("🍽️ 今日のおすすめ")

today_items = [item for item in st.session_state.fridge_items 
               if get_days_until_expiry(item['expiry_date']) <= 1]

if today_items:
    st.error("🍴 今日中に食べることをおすすめします：")
    for item in today_items:
        st.markdown(f"• **{item['name']}** (期限: {item['expiry_date']})")
else:
    st.success("😊 今日急いで食べるものはありません")

# フッター
st.markdown("---")
st.markdown("""
<div style='text-align: center; font-size: 22px; color: #666; padding: 20px;'>
    📱 カメラが使えない場合は「手動で登録」をお使いください<br>
    💡 困ったときはご家族にお声かけください<br>
    🎯 毎日チェックして、安全で美味しい食事を！
</div>
""", unsafe_allow_html=True)

# サイドバー（緊急時対応）
with st.sidebar:
    st.markdown("### 🚨 緊急時対応")
    
    # 期限切れアイテム数
    expired_count = len([item for item in st.session_state.fridge_items if check_expired(item['expiry_date'])])
    if expired_count > 0:
        st.error(f"⚠️ 期限切れ: {expired_count}個")
    
    # 期限間近アイテム数
    warning_count = len([item for item in st.session_state.fridge_items if check_expiring_soon(item['expiry_date'])])
    if warning_count > 0:
        st.warning(f"🔔 期限間近: {warning_count}個")
    
    st.markdown("---")
    st.markdown("### 📞 困ったときは")
    st.markdown("- カメラが映らない → 手動登録を使用")
    st.markdown("- 文字が小さい → ブラウザで拡大")
    st.markdown("- 操作がわからない → ご家族に相談")
    
    st.markdown("---")
    if st.button("🗑️ 全データ削除"):
        if st.checkbox("本当に削除しますか？"):
            st.session_state.fridge_items = []
            st.success("削除しました")
            st.rerun()