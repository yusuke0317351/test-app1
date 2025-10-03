import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
from pathlib import Path

# ページ設定
st.set_page_config(
    page_title="冷蔵庫管理アプリ",
    page_icon="🍱",
    layout="wide"
)

# データファイルのパス
DATA_FILE = Path("fridge_data.json")

# カスタムCSS
st.markdown("""
<style>
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
    }
    .warning-box {
        background-color: #ffcccc;
        padding: 20px;
        border-radius: 10px;
        border: 3px solid #ff0000;
        margin: 10px 0;
    }
    .safe-box {
        background-color: #ccffcc;
        padding: 20px;
        border-radius: 10px;
        border: 3px solid #00aa00;
        margin: 10px 0;
    }
    .caution-box {
        background-color: #ffffcc;
        padding: 20px;
        border-radius: 10px;
        border: 3px solid #ffaa00;
        margin: 10px 0;
    }
    .stButton>button {
        font-size: 20px;
        padding: 20px 40px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# データの読み込み
def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# データの保存
def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 賞味期限までの日数を計算
def days_until_expiry(expiry_date):
    today = datetime.now().date()
    expiry = datetime.strptime(expiry_date, "%Y-%m-%d").date()
    return (expiry - today).days

# セッション状態の初期化
if 'items' not in st.session_state:
    loaded_data = load_data()
    st.session_state.items = loaded_data if isinstance(loaded_data, list) else []

# タイトル
st.title("🍱 冷蔵庫管理アプリ")
st.markdown("### 食材の賞味期限を管理して、食品ロスを防ぎましょう！")
st.markdown("---")

# タブの作成
tab1, tab2, tab3 = st.tabs(["📋 食材リスト", "➕ 食材を追加", "ℹ️ 使い方"])

# タブ1: 食材リスト
with tab1:
    st.header("登録されている食材")
    
    if len(st.session_state.items) == 0:
        st.info("📭 まだ食材が登録されていません。「食材を追加」タブから登録してください。")
    else:
        # 賞味期限でソート
        sorted_items = sorted(st.session_state.items, 
                            key=lambda x: x['expiry_date'])
        
        # 警告カウント
        urgent_count = 0
        warning_count = 0
        
        for item in sorted_items:
            days_left = days_until_expiry(item['expiry_date'])
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # 緊急（3日以内）
                if days_left <= 3:
                    urgent_count += 1
                    st.markdown(f"""
                    <div class="warning-box">
                        <h2>🚨 {item['name']}</h2>
                        <p class="big-font">賞味期限: {item['expiry_date']}</p>
                        <p class="big-font" style="color: red;">⚠️ あと{days_left}日！今日か明日食べてください！</p>
                        <p>購入日: {item['purchase_date']}</p>
                        <p>バーコード: {item['barcode']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # 注意（7日以内）
                elif days_left <= 7:
                    warning_count += 1
                    st.markdown(f"""
                    <div class="caution-box">
                        <h2>⚠️ {item['name']}</h2>
                        <p class="big-font">賞味期限: {item['expiry_date']}</p>
                        <p class="big-font" style="color: orange;">注意: あと{days_left}日です</p>
                        <p>購入日: {item['purchase_date']}</p>
                        <p>バーコード: {item['barcode']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # 安全
                else:
                    st.markdown(f"""
                    <div class="safe-box">
                        <h2>✅ {item['name']}</h2>
                        <p class="big-font">賞味期限: {item['expiry_date']}</p>
                        <p class="big-font" style="color: green;">まだ{days_left}日あります</p>
                        <p>購入日: {item['purchase_date']}</p>
                        <p>バーコード: {item['barcode']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                if st.button(f"🗑️ 削除", key=f"delete_{item['barcode']}_{item['purchase_date']}"):
                    st.session_state.items.remove(item)
                    save_data(st.session_state.items)
                    st.rerun()
        
        # サマリー表示
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🚨 緊急（3日以内）", f"{urgent_count}個")
        with col2:
            st.metric("⚠️ 注意（7日以内）", f"{warning_count}個")
        with col3:
            st.metric("📊 合計", f"{len(st.session_state.items)}個")

# タブ2: 食材を追加
with tab2:
    st.header("新しい食材を登録")
    
    # よく使う食材のプリセット
    st.subheader("🍽️ よく使う食材から選ぶ")
    
    preset_foods = {
        "牛乳": {"days": 7, "barcode": "4901234567890"},
        "卵": {"days": 14, "barcode": "4901234567891"},
        "豆腐": {"days": 5, "barcode": "4901234567892"},
        "ヨーグルト": {"days": 14, "barcode": "4901234567893"},
        "納豆": {"days": 7, "barcode": "4901234567894"},
        "食パン": {"days": 5, "barcode": "4901234567895"},
        "ハム": {"days": 7, "barcode": "4901234567896"},
        "チーズ": {"days": 30, "barcode": "4901234567897"},
        "もやし": {"days": 2, "barcode": "4901234567898"},
        "キャベツ": {"days": 7, "barcode": "4901234567899"},
    }
    
    cols = st.columns(5)
    for idx, (food_name, food_data) in enumerate(preset_foods.items()):
        with cols[idx % 5]:
            if st.button(f"🛒 {food_name}", key=f"preset_{food_name}", use_container_width=True):
                new_item = {
                    'name': food_name,
                    'barcode': food_data['barcode'],
                    'purchase_date': datetime.now().strftime("%Y-%m-%d"),
                    'expiry_date': (datetime.now() + timedelta(days=food_data['days'])).strftime("%Y-%m-%d"),
                    'photo': None
                }
                st.session_state.items.append(new_item)
                save_data(st.session_state.items)
                st.success(f"✅ {food_name} を登録しました！")
                st.balloons()
                st.rerun()
    
    st.markdown("---")
    st.subheader("✏️ 手動で登録する")
    
    # 入力方法の選択
    input_method = st.radio(
        "入力方法を選んでください",
        ["📝 すべて手入力", "📷 バーコードを入力"],
        horizontal=True
    )
    
    with st.form("add_item_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("食材名 *", placeholder="例: 牛乳", 
                               help="食材の名前を入力してください")
            
            if input_method == "📷 バーコードを入力":
                st.info("💡 商品のバーコード番号を入力してください")
                barcode = st.text_input("バーコード番号 *", 
                                       placeholder="例: 4901234567890",
                                       help="13桁のバーコード番号を入力してください")
            else:
                barcode = st.text_input("バーコード番号（任意）", 
                                       placeholder="なければ空欄でOK",
                                       help="バーコードがあれば入力してください")
                if not barcode:
                    barcode = f"MANUAL_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            purchase_date = st.date_input("購入日 *", 
                                         value=datetime.now(),
                                         help="食材を購入した日を選択してください")
        
        with col2:
            # 賞味期限の入力方法
            expiry_input = st.radio(
                "賞味期限の入力方法",
                ["📅 日付を選ぶ", "🔢 日数で指定"],
                horizontal=True
            )
            
            if expiry_input == "📅 日付を選ぶ":
                expiry_date = st.date_input("賞味期限 *", 
                                           value=datetime.now() + timedelta(days=7),
                                           help="賞味期限の日付を選択してください")
            else:
                days = st.number_input("何日後まで？ *", 
                                      min_value=1, 
                                      max_value=365, 
                                      value=7,
                                      help="今日から何日後が賞味期限ですか？")
                expiry_date = datetime.now() + timedelta(days=days)
                st.info(f"📅 賞味期限: {expiry_date.strftime('%Y年%m月%d日')}")
            
            # 写真アップロード（オプション）
            photo = st.file_uploader("賞味期限の写真（任意）", 
                                    type=['jpg', 'jpeg', 'png'],
                                    help="賞味期限が写った写真をアップロードできます")
        
        st.markdown("---")
        col_submit1, col_submit2, col_submit3 = st.columns([1, 2, 1])
        with col_submit2:
            submitted = st.form_submit_button("📝 この食材を登録する", use_container_width=True)
        
        if submitted:
            if name:
                new_item = {
                    'name': name,
                    'barcode': barcode,
                    'purchase_date': purchase_date.strftime("%Y-%m-%d") if isinstance(purchase_date, datetime) else purchase_date.strftime("%Y-%m-%d"),
                    'expiry_date': expiry_date.strftime("%Y-%m-%d") if isinstance(expiry_date, datetime) else expiry_date.strftime("%Y-%m-%d"),
                    'photo': photo.name if photo else None
                }
                st.session_state.items.append(new_item)
                save_data(st.session_state.items)
                st.success(f"✅ {name} を登録しました！")
                st.balloons()
                st.rerun()
            else:
                st.error("⚠️ 食材名は必須です。")

# タブ3: 使い方
with tab3:
    st.header("📖 アプリの使い方")
    
    st.markdown("""
    ## このアプリでできること
    
    ### 1️⃣ 食材を登録する
    - 「食材を追加」タブで新しい食材を登録できます
    - バーコード番号、購入日、賞味期限を入力してください
    - 賞味期限の写真もアップロードできます（任意）
    
    ### 2️⃣ 食材の状態を確認する
    - 「食材リスト」タブで登録した食材を確認できます
    - 賞味期限が近い順に並んでいます
    
    ### 3️⃣ 警告システム
    - 🚨 **赤色（緊急）**: 賞味期限まで3日以内 → すぐに食べてください！
    - ⚠️ **黄色（注意）**: 賞味期限まで7日以内 → 早めに食べましょう
    - ✅ **緑色（安全）**: まだ余裕があります
    
    ### 4️⃣ 食材を削除する
    - 食べ終わったら「削除」ボタンで削除してください
    
    ## ヒント
    - 買い物から帰ったら、すぐに登録しましょう
    - 毎日「食材リスト」を確認する習慣をつけましょう
    - 赤色の食材は優先的に使いましょう
    """)
    
    st.info("💡 このアプリを使って、食品ロスを減らし、安全においしく食事を楽しみましょう！")

# フッター
st.markdown("---")
st.markdown("### 🏠 毎日の健康的な食生活をサポートします")