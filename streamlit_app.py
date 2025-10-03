import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
from pathlib import Path
from PIL import Image
import io
import re

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
    .camera-box {
        background-color: #e3f2fd;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #2196F3;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# データの読み込み
def load_data():
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except:
            return []
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

# 画像から日付を抽出（簡易版）
def extract_date_from_image(image):
    """
    画像から日付を抽出する簡易版
    実際の実装では、pytesseractなどのOCRライブラリを使用します
    """
    # ここではデモとして、ユーザーに手動入力を促します
    st.info("📷 写真をアップロードしました。下のフォームで賞味期限を入力してください。")
    return None

# バーコードデータベース（簡易版）
BARCODE_DATABASE = {
    "4901234567890": {"name": "牛乳", "typical_days": 7},
    "4901234567891": {"name": "卵", "typical_days": 14},
    "4901234567892": {"name": "豆腐", "typical_days": 5},
    "4901234567893": {"name": "ヨーグルト", "typical_days": 14},
    "4901234567894": {"name": "納豆", "typical_days": 7},
    "4901234567895": {"name": "食パン", "typical_days": 5},
    "4901234567896": {"name": "ハム", "typical_days": 7},
    "4901234567897": {"name": "チーズ", "typical_days": 30},
    "4901234567898": {"name": "もやし", "typical_days": 2},
    "4901234567899": {"name": "キャベツ", "typical_days": 7},
}

# バーコードから商品情報を取得
def get_product_info(barcode):
    if barcode in BARCODE_DATABASE:
        return BARCODE_DATABASE[barcode]
    return None

# セッション状態の初期化
if 'food_items' not in st.session_state:
    st.session_state.food_items = load_data()

if 'scanned_barcode' not in st.session_state:
    st.session_state.scanned_barcode = ""

if 'scanned_product' not in st.session_state:
    st.session_state.scanned_product = None

# タイトル
st.title("🍱 冷蔵庫管理アプリ")
st.markdown("### 食材の賞味期限を管理して、食品ロスを防ぎましょう！")
st.markdown("---")

# タブの作成
tab1, tab2, tab3, tab4 = st.tabs(["📋 食材リスト", "➕ 食材を追加", "📷 カメラで読み取り", "ℹ️ 使い方"])

# タブ1: 食材リスト
with tab1:
    st.header("登録されている食材")
    
    if len(st.session_state.food_items) == 0:
        st.info("📭 まだ食材が登録されていません。「食材を追加」タブから登録してください。")
    else:
        # 賞味期限でソート
        sorted_items = sorted(st.session_state.food_items, 
                            key=lambda x: x['expiry_date'])
        
        # 警告カウント
        urgent_count = 0
        warning_count = 0
        
        for idx, item in enumerate(sorted_items):
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
                if st.button(f"🗑️ 削除", key=f"delete_{idx}_{item['barcode']}"):
                    st.session_state.food_items.remove(item)
                    save_data(st.session_state.food_items)
                    st.rerun()
        
        # サマリー表示
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🚨 緊急（3日以内）", f"{urgent_count}個")
        with col2:
            st.metric("⚠️ 注意（7日以内）", f"{warning_count}個")
        with col3:
            st.metric("📊 合計", f"{len(st.session_state.food_items)}個")

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
                st.session_state.food_items.append(new_item)
                save_data(st.session_state.food_items)
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
                # バーコードが空の場合は自動生成
                if not barcode:
                    barcode = f"MANUAL_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                new_item = {
                    'name': name,
                    'barcode': barcode,
                    'purchase_date': purchase_date.strftime("%Y-%m-%d") if isinstance(purchase_date, datetime) else purchase_date.strftime("%Y-%m-%d"),
                    'expiry_date': expiry_date.strftime("%Y-%m-%d") if isinstance(expiry_date, datetime) else expiry_date.strftime("%Y-%m-%d"),
                    'photo': photo.name if photo else None
                }
                st.session_state.food_items.append(new_item)
                save_data(st.session_state.food_items)
                st.success(f"✅ {name} を登録しました！")
                st.balloons()
                st.rerun()
            else:
                st.error("⚠️ 食材名は必須です。")

# タブ3: カメラで読み取り
with tab3:
    st.header("📷 カメラで情報を読み取る")
    
    st.markdown("""
    <div class="camera-box">
        <h3>📱 読み取り機能の使い方</h3>
        <p style="font-size: 18px;">
        1. バーコードの写真を撮影またはアップロード<br>
        2. 賞味期限の写真を撮影またはアップロード<br>
        3. 自動で情報が入力されます
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ステップ1: バーコードスキャン
    st.subheader("ステップ1: バーコードを読み取る")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📷 バーコード画像")
        barcode_image = st.camera_input("バーコードを撮影してください")
        
        if barcode_image is None:
            barcode_upload = st.file_uploader("または画像をアップロード", 
                                            type=['jpg', 'jpeg', 'png'],
                                            key="barcode_upload")
            if barcode_upload:
                barcode_image = barcode_upload
    
    with col2:
        if barcode_image is not None:
            st.image(barcode_image, caption="読み取った画像", use_container_width=True)
            st.info("💡 実際の実装では、ここでバーコードを自動認識します")
            
            # デモ用: バーコード番号を手動入力
            detected_barcode = st.text_input(
                "検出されたバーコード番号（手動入力）",
                placeholder="例: 4901234567890",
                key="detected_barcode"
            )
            
            if detected_barcode:
                product_info = get_product_info(detected_barcode)
                if product_info:
                    st.success(f"✅ 商品を認識: {product_info['name']}")
                    st.session_state.scanned_barcode = detected_barcode
                    st.session_state.scanned_product = product_info
                else:
                    st.warning("⚠️ 商品データベースに登録されていません")
                    st.session_state.scanned_barcode = detected_barcode
                    st.session_state.scanned_product = None
    
    st.markdown("---")
    
    # ステップ2: 賞味期限読み取り
    st.subheader("ステップ2: 賞味期限を読み取る")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📷 賞味期限の画像")
        expiry_image = st.camera_input("賞味期限を撮影してください")
        
        if expiry_image is None:
            expiry_upload = st.file_uploader("または画像をアップロード", 
                                           type=['jpg', 'jpeg', 'png'],
                                           key="expiry_upload")
            if expiry_upload:
                expiry_image = expiry_upload
    
    with col2:
        if expiry_image is not None:
            st.image(expiry_image, caption="読み取った画像", use_container_width=True)
            st.info("💡 実際の実装では、ここで日付を自動認識します")
            
            # デモ用: 賞味期限を手動入力
            detected_expiry = st.date_input(
                "検出された賞味期限（手動入力）",
                value=datetime.now() + timedelta(days=7),
                key="detected_expiry"
            )
    
    st.markdown("---")
    
    # ステップ3: 登録
    st.subheader("ステップ3: 食材を登録する")
    
    if st.session_state.scanned_barcode:
        with st.form("camera_register_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                if st.session_state.scanned_product:
                    camera_name = st.text_input(
                        "食材名",
                        value=st.session_state.scanned_product['name']
                    )
                else:
                    camera_name = st.text_input(
                        "食材名",
                        placeholder="食材名を入力してください"
                    )
                
                camera_barcode = st.text_input(
                    "バーコード",
                    value=st.session_state.scanned_barcode,
                    disabled=True
                )
            
            with col2:
                camera_purchase = st.date_input(
                    "購入日",
                    value=datetime.now()
                )
                
                if 'detected_expiry' in locals():
                    camera_expiry = st.date_input(
                        "賞味期限",
                        value=detected_expiry
                    )
                else:
                    if st.session_state.scanned_product:
                        default_days = st.session_state.scanned_product['typical_days']
                        camera_expiry = st.date_input(
                            "賞味期限",
                            value=datetime.now() + timedelta(days=default_days)
                        )
                    else:
                        camera_expiry = st.date_input(
                            "賞味期限",
                            value=datetime.now() + timedelta(days=7)
                        )
            
            submitted_camera = st.form_submit_button("📝 この食材を登録する", use_container_width=True)
            
            if submitted_camera and camera_name:
                new_item = {
                    'name': camera_name,
                    'barcode': camera_barcode,
                    'purchase_date': camera_purchase.strftime("%Y-%m-%d"),
                    'expiry_date': camera_expiry.strftime("%Y-%m-%d"),
                    'photo': 'scanned'
                }
                st.session_state.food_items.append(new_item)
                save_data(st.session_state.food_items)
                st.success(f"✅ {camera_name} を登録しました！")
                st.balloons()
                
                # リセット
                st.session_state.scanned_barcode = ""
                st.session_state.scanned_product = None
                st.rerun()
    else:
        st.info("👆 まずバーコードを読み取ってください")

# タブ4: 使い方
with tab4:
    st.header("📖 アプリの使い方")
    
    st.markdown("""
    ## このアプリでできること
    
    ### 1️⃣ 食材を登録する（3つの方法）
    
    #### 方法1: ワンクリック登録（一番簡単！）
    - 「食材を追加」タブの「よく使う食材」ボタンをクリック
    - 牛乳、卵、豆腐などが自動で登録されます
    
    #### 方法2: 手動で登録
    - 「食材を追加」タブで詳細を入力
    - バーコード、購入日、賞味期限を自分で入力
    - 賞味期限は「日付」または「何日後」で指定できます
    
    #### 方法3: カメラで読み取り（NEW!）
    - 「カメラで読み取り」タブを開く
    - バーコードの写真を撮影
    - 賞味期限の写真を撮影
    - 自動で情報が入力されます
    
    ### 2️⃣ 食材の状態を確認する
    - 「食材リスト」タブで登録した食材を確認
    - 賞味期限が近い順に並んでいます
    
    ### 3️⃣ 警告システム
    - 🚨 **赤色（緊急）**: 賞味期限まで3日以内 → すぐに食べてください！
    - ⚠️ **黄色（注意）**: 賞味期限まで7日以内 → 早めに食べましょう
    - ✅ **緑色（安全）**: まだ余裕があります
    
    ### 4️⃣ 食材を削除する
    - 食べ終わったら「削除」ボタンで削除
    
    ## 📱 カメラ機能について
    
    現在のバージョンでは、カメラで撮影した後に手動で情報を入力する必要があります。
    
    **将来のバージョンで実装予定:**
    - バーコードの自動認識（pyzbar使用）
    - 賞味期限の自動読み取り（OCR機能、pytesseract使用）
    - リアルタイムスキャン
    
    ## 💡 ヒント
    - 買い物から帰ったら、すぐに登録しましょう
    - 毎日「食材リスト」を確認する習慣をつけましょう
    - 赤色の食材は優先的に使いましょう
    - カメラ機能を使えば、より簡単に登録できます
    """)
    
    st.info("💡 このアプリを使って、食品ロスを減らし、安全においしく食事を楽しみましょう！")
    
    st.markdown("---")
    
    st.markdown("""
    ### 🔧 技術情報
    
    **完全自動化のために必要なライブラリ:**
    ```bash
    pip install pyzbar opencv-python pytesseract
    ```
    
    これらをインストールすると、バーコードと賞味期限の自動認識が可能になります。
    """)

# フッター
st.markdown("---")
st.markdown("### 🏠 毎日の健康的な食生活をサポートします")