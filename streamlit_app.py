import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
from PIL import Image
import io
import requests
from urllib.parse import urlencode
 
# ページ設定
st.set_page_config(
    page_title="冷蔵庫管理アプリ",
    page_icon="🍱",
    layout="wide"
)

# セッション状態の完全リセット（デバッグ用 - 問題が解決したら削除してください）
if 'app_initialized' not in st.session_state:
    # 既存の壊れたステートをクリア
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.app_initialized = True
 
# セッション状態の初期化
if 'users' not in st.session_state:
    st.session_state['users'] = {}
if 'current_user' not in st.session_state:
    st.session_state['current_user'] = None
if 'items' not in st.session_state:
    st.session_state['items'] = []
if 'items_user' not in st.session_state:
    st.session_state['items_user'] = None
 
# Open Food Facts APIから商品名を取得
def get_product_name_from_barcode(barcode):
    """
    バーコード（JAN）から商品名を取得
    Open Food Facts APIを使用（APIキー不要）
    """
    if not barcode:
        return None
   
    try:
        # Open Food Facts APIのエンドポイント
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
       
        # APIリクエスト
        response = requests.get(url, timeout=5)
        response.raise_for_status()
       
        # レスポンス解析
        data = response.json()
       
        # 商品が見つかった場合
        if data.get('status') == 1:
            product = data.get('product', {})
            # 日本語名を優先、なければ英語名など
            product_name = (product.get('product_name_ja') or 
                          product.get('product_name') or 
                          product.get('product_name_en'))
            
            if product_name:
                # 商品名から不要な文字を削除（より簡潔に）
                product_name = product_name.split('【')[0].split('(')[0].strip()
                return product_name
        
        return None
           
    except Exception as e:
        st.error(f"API エラー: {str(e)}")
        return None
 
# カスタムCSS（スマートフォン対応・大きな文字とボタン）
st.markdown("""
    <style>
    /* 基本フォント */
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
    }
    .warning-font {
        font-size: 28px !important;
        font-weight: bold;
        color: #ff4444;
    }
    .safe-font {
        font-size: 22px !important;
        color: #44ff44;
    }
    
    /* ボタンのスタイル - タッチしやすいサイズ */
    .stButton>button {
        font-size: 18px;
        padding: 15px 20px;
        width: 100%;
        min-height: 50px;
        border-radius: 10px;
        font-weight: bold;
    }
    
    /* モバイル対応 */
    @media (max-width: 768px) {
        /* タイトルをモバイル用に調整 */
        h1 {
            font-size: 28px !important;
        }
        h2 {
            font-size: 22px !important;
        }
        h3 {
            font-size: 18px !important;
        }
        
        /* ボタンをさらに大きく */
        .stButton>button {
            font-size: 20px;
            padding: 18px 25px;
            min-height: 60px;
        }
        
        /* 入力フィールドを大きく */
        .stTextInput>div>div>input,
        .stNumberInput>div>div>input,
        .stSelectbox>div>div>select {
            font-size: 18px !important;
            padding: 12px !important;
            min-height: 50px !important;
        }
        
        /* 日付ピッカーも大きく */
        .stDateInput>div>div>input {
            font-size: 18px !important;
            padding: 12px !important;
            min-height: 50px !important;
        }
        
        /* カードの余白調整 */
        .element-container {
            margin-bottom: 10px;
        }
        
        /* フォントサイズの調整 */
        .big-font {
            font-size: 20px !important;
        }
        .warning-font {
            font-size: 24px !important;
        }
        .safe-font {
            font-size: 18px !important;
        }
        
        /* カード内のテキスト */
        div[style*="padding: 20px"] h2 {
            font-size: 20px !important;
        }
        div[style*="padding: 20px"] p {
            font-size: 16px !important;
        }
        
        /* メトリクスを大きく */
        .stMetric {
            font-size: 18px !important;
        }
        
        /* 通知を目立たせる */
        .stAlert {
            font-size: 16px !important;
            padding: 15px !important;
        }
    }
    
    /* 小さいスマホ用 */
    @media (max-width: 480px) {
        h1 {
            font-size: 24px !important;
        }
        
        /* さらにボタンを大きく */
        .stButton>button {
            font-size: 18px;
            padding: 15px 20px;
            min-height: 55px;
        }
        
        /* カードの余白を小さく */
        div[style*="padding: 20px"] {
            padding: 15px !important;
        }
    }
    
    /* タッチ操作の改善 */
    button, input, select {
        -webkit-tap-highlight-color: rgba(0,0,0,0.1);
        touch-action: manipulation;
    }
    
    /* スクロールバーをモバイルフレンドリーに */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 4px;
    }
    </style>
    """, unsafe_allow_html=True)
 
# タイトル
st.title("🍱 冷蔵庫管理アプリ")
 
st.markdown("---")
 
# ユーザー選択・登録セクション（モバイル対応）
st.markdown("### 👤 利用者を選択")

if len(st.session_state['users']) > 0:
    user_list = ["新しい利用者を追加"] + list(st.session_state['users'].keys())
    current_index = 0
    if st.session_state['current_user'] and st.session_state['current_user'] in user_list:
        current_index = user_list.index(st.session_state['current_user'])
    
    selected_user = st.selectbox(
        "利用者名",
        user_list,
        index=current_index,
        help="管理したい方の名前を選んでください",
        label_visibility="collapsed"
    )
else:
    selected_user = "新しい利用者を追加"
    st.info("👋 最初の利用者を登録してください")

if selected_user == "新しい利用者を追加":
    new_user_name = st.text_input(
        "利用者の名前",
        placeholder="例: 田中太郎、山田花子",
        help="名前を入力してください"
    )
    
    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button("➕ 登録", type="primary", use_container_width=True):
            if new_user_name and new_user_name.strip():
                if new_user_name not in st.session_state['users']:
                    st.session_state['users'][new_user_name] = []
                    st.session_state['current_user'] = new_user_name
                    st.session_state['items'] = []
                    st.session_state['items_user'] = new_user_name
                    st.success(f"✅ {new_user_name}さんを登録しました！")
                    st.rerun()
                else:
                    st.error("⚠️ すでに登録されています")
            else:
                st.error("⚠️ 名前を入力してください")
else:
    if st.button("✅ この利用者を選択", type="primary", use_container_width=True):
        st.session_state['current_user'] = selected_user
        st.session_state['items'] = list(st.session_state['users'].get(selected_user, []))
        st.session_state['items_user'] = selected_user
        st.rerun()
 
# 現在のユーザー表示
if st.session_state['current_user']:
    st.success(f"📱 現在の利用者: **{st.session_state['current_user']}**さん")
    # 現在のユーザーのアイテムリストを同期
    if st.session_state['items_user'] != st.session_state['current_user']:
        st.session_state['items'] = list(st.session_state['users'].get(st.session_state['current_user'], []))
        st.session_state['items_user'] = st.session_state['current_user']
else:
    st.warning("⚠️ 利用者を選択してください")
    st.stop()
 
st.markdown("---")

# 🔔 賞味期限の通知チェック
if st.session_state.get('notification_enabled', True):
    current_items = st.session_state['items']
    if isinstance(current_items, list) and len(current_items) > 0:
        df_check = pd.DataFrame(current_items)
        df_check['expiry_date_dt'] = pd.to_datetime(df_check['expiry_date'])
        today = pd.Timestamp(datetime.now().date())
        df_check['days_left'] = (df_check['expiry_date_dt'] - today).dt.days
        
        notification_days = st.session_state.get('notification_days', 3)
        sound_alert = st.session_state.get('sound_alert', False)
        
        # 期限切れ
        expired = df_check[df_check['days_left'] < 0]
        if not expired.empty:
            with st.container():
                st.error(f"🚨 **緊急通知**: {len(expired)}個の食材が期限切れです！")
                for _, item in expired.head(3).iterrows():
                    st.markdown(f"- **{item['name']}** (賞味期限: {item['expiry_date']})")
                if len(expired) > 3:
                    st.markdown(f"...他 {len(expired) - 3}個")
        
        # 今日が期限
        today_expiry = df_check[df_check['days_left'] == 0]
        if not today_expiry.empty:
            with st.container():
                st.warning(f"⚠️ **今日が期限**: {len(today_expiry)}個の食材が今日期限切れになります！")
                for _, item in today_expiry.iterrows():
                    st.markdown(f"- **{item['name']}**")
        
        # 設定した日数以内
        warning_items = df_check[(df_check['days_left'] > 0) & (df_check['days_left'] <= notification_days)]
        if not warning_items.empty:
            with st.container():
                st.info(f"📢 **注意**: {len(warning_items)}個の食材が{notification_days}日以内に期限切れになります")
                for _, item in warning_items.head(5).iterrows():
                    st.markdown(f"- **{item['name']}** (あと{item['days_left']}日)")
                if len(warning_items) > 5:
                    st.markdown(f"...他 {len(warning_items) - 5}個")
        
        # 音声アラートのオプション
        if sound_alert and (not expired.empty or not today_expiry.empty):
            st.markdown("""
                <audio autoplay>
                    <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
                </audio>
            """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("### 食材の管理を簡単に！")
 
# タブの作成
tab1, tab2, tab3, tab4 = st.tabs(["📝 食材を登録", "📋 食材リスト", "⚠️ 警告", "🍳 レシピ提案"])
 
# タブ1: 食材登録（モバイル最適化）
with tab1:
    st.header("新しい食材を登録")
   
    # モバイルでは縦に並べる
    st.subheader("📷 バーコードまたは賞味期限の写真")
    uploaded_file = st.file_uploader(
        "写真をアップロード",
        type=['png', 'jpg', 'jpeg'],
        help="バーコードや賞味期限が写っている写真を選択してください"
    )
   
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="アップロードされた写真", use_container_width=True)
        st.info("💡 写真を確認しました。下の情報を入力してください。")
   
    st.subheader("📝 食材情報を入力")
   
    # バーコード番号入力
    barcode = st.text_input(
        "バーコード番号（JAN）",
        placeholder="例: 4901234567890",
        help="バーコードの番号を入力してください（13桁）",
        key="barcode_input"
    )
   
    # バーコードから商品名を検索するボタン
    search_button = st.button("🔍 商品名を検索", type="secondary", use_container_width=True)
   
    # 商品名の自動取得
    auto_product_name = ""
    if search_button and barcode:
        with st.spinner("商品を検索中..."):
            auto_product_name = get_product_name_from_barcode(barcode)
            if auto_product_name:
                st.success(f"✅ 商品が見つかりました: {auto_product_name}")
            else:
                st.warning("⚠️ 商品が見つかりませんでした。手動で入力してください。")
   
    # 食材名入力（自動取得された名前をデフォルト値に）
    item_name = st.text_input(
        "食材名",
        value=auto_product_name if auto_product_name else "",
        placeholder="例: 牛乳、卵、豆腐",
        help="食材の名前を入力してください（バーコード検索で自動入力できます）",
        key="item_name_input"
    )
   
    # 購入日
    purchase_date = st.date_input(
        "購入日",
        value=datetime.now(),
        help="食材を買った日を選択してください"
    )
   
    # 賞味期限
    expiry_date = st.date_input(
        "賞味期限",
        value=datetime.now() + timedelta(days=7),
        help="賞味期限を選択してください"
    )
   
    # カテゴリ
    category = st.selectbox(
        "カテゴリ",
        ["野菜", "果物", "肉類", "魚類", "乳製品", "卵", "調味料", "その他"],
        help="食材の種類を選んでください"
    )
   
    # 数量
    quantity = st.number_input(
        "数量",
        min_value=1,
        value=1,
        help="個数やパック数を入力してください"
    )
   
    # 登録ボタン（モバイルで目立つように）
    st.markdown("---")
    if st.button("✅ 登録する", type="primary", key="register_button", use_container_width=True):
        if item_name:
            new_item = {
                'name': item_name,
                'barcode': barcode if barcode else "未登録",
                'purchase_date': purchase_date.strftime('%Y-%m-%d'),
                'expiry_date': expiry_date.strftime('%Y-%m-%d'),
                'category': category,
                'quantity': quantity,
                'registered_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'registered_by': st.session_state['current_user']  # 登録者を記録
            }
            # リストに追加
            current_items = list(st.session_state['items'])
            current_items.append(new_item)
            st.session_state['items'] = current_items
            # ユーザーデータを更新
            st.session_state['users'][st.session_state['current_user']] = list(current_items)
            st.success(f"✅ {item_name} を登録しました！")
            st.balloons()
            st.rerun()
        else:
            st.error("⚠️ 食材名を入力してください")
 
# タブ2: 食材リスト
with tab2:
    st.header("登録されている食材")
    
    current_items = st.session_state['items']
    
    if isinstance(current_items, list) and len(current_items) > 0:
        # データフレームに変換
        df = pd.DataFrame(current_items)
        
        # 登録者情報がない古いデータに対応
        if 'registered_by' not in df.columns:
            df['registered_by'] = '不明'
       
        # 賞味期限までの日数を計算
        df['expiry_date_dt'] = pd.to_datetime(df['expiry_date'])
        today = pd.Timestamp(datetime.now().date())
        df['days_left'] = (df['expiry_date_dt'] - today).dt.days
       
        # ソート
        df = df.sort_values('days_left')
        df = df.reset_index(drop=True)
       
        # フィルターセクション
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            # カテゴリでフィルター
            selected_category = st.selectbox(
                "カテゴリで絞り込み",
                ["すべて"] + list(df['category'].unique())
            )
        
        with col_filter2:
            # 登録者でフィルター
            unique_users = list(df['registered_by'].unique())
            selected_user_filter = st.selectbox(
                "登録者で絞り込み",
                ["すべて"] + unique_users
            )
       
        # フィルタリング
        df_display = df.copy()
        if selected_category != "すべて":
            df_display = df_display[df_display['category'] == selected_category]
        if selected_user_filter != "すべて":
            df_display = df_display[df_display['registered_by'] == selected_user_filter]
        
        df_display = df_display.reset_index(drop=True)
        
        # 統計情報を表示
        if len(df_display) > 0:
            st.info(f"📊 表示中: {len(df_display)}個 / 全{len(df)}個")
       
        # 食材カードを表示
        for idx in range(len(df_display)):
            row = df_display.iloc[idx]
            days_left = row['days_left']
            registered_by = row.get('registered_by', '不明')
           
            # 警告レベルの判定
            if days_left < 0:
                alert_color = "#ffcccc"
                alert_text = f"⚠️ 期限切れ（{abs(days_left)}日前）"
                alert_class = "warning-font"
            elif days_left == 0:
                alert_color = "#ffeecc"
                alert_text = "⚠️ 今日が期限です！"
                alert_class = "warning-font"
            elif days_left <= 2:
                alert_color = "#fff4cc"
                alert_text = f"⚠️ あと{days_left}日"
                alert_class = "warning-font"
            elif days_left <= 5:
                alert_color = "#ffffcc"
                alert_text = f"注意: あと{days_left}日"
                alert_class = "big-font"
            else:
                alert_color = "#e8f5e9"
                alert_text = f"あと{days_left}日"
                alert_class = "safe-font"
           
            # カード表示（モバイル最適化 + 登録者情報）
            with st.container():
                st.markdown(f"""
                    <div style="background-color: {alert_color}; padding: 15px; border-radius: 10px; margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                            <h2 style="margin: 0; font-size: 20px;">{row['name']} ({row['category']})</h2>
                            <span style="background-color: rgba(0,0,0,0.1); padding: 5px 10px; border-radius: 15px; font-size: 14px; white-space: nowrap;">👤 {registered_by}</span>
                        </div>
                        <p class="{alert_class}" style="margin: 10px 0;">{alert_text}</p>
                        <p style="margin: 5px 0;"><strong>数量:</strong> {row['quantity']}</p>
                        <p style="margin: 5px 0;"><strong>購入日:</strong> {row['purchase_date']}</p>
                        <p style="margin: 5px 0;"><strong>賞味期限:</strong> {row['expiry_date']}</p>
                        <p style="margin: 5px 0;"><strong>バーコード:</strong> {row['barcode']}</p>
                    </div>
                """, unsafe_allow_html=True)
               
                # 削除ボタンを全幅で表示（モバイル対応）
                if st.button(f"🗑️ 削除", key=f"del_{idx}_{row['name']}", use_container_width=True):
                    # 元のリストから該当アイテムを削除
                    item_to_remove = row.to_dict()
                    updated_items = [item for item in current_items if item != item_to_remove]
                    st.session_state['items'] = updated_items
                    # ユーザーデータを更新
                    st.session_state['users'][st.session_state['current_user']] = list(updated_items)
                    st.rerun()
    else:
        st.info("📝 まだ食材が登録されていません。「食材を登録」タブから登録してください。")
 
# タブ3: 警告
with tab3:
    st.header("⚠️ 賞味期限の警告")
    
    current_items = st.session_state['items']
   
    if isinstance(current_items, list) and len(current_items) > 0:
        df = pd.DataFrame(current_items)
        
        # 登録者情報がない古いデータに対応
        if 'registered_by' not in df.columns:
            df['registered_by'] = '不明'
            
        df['expiry_date_dt'] = pd.to_datetime(df['expiry_date'])
        today = pd.Timestamp(datetime.now().date())
        df['days_left'] = (df['expiry_date_dt'] - today).dt.days
       
        # 期限切れ・近い食材
        expired = df[df['days_left'] < 0]
        today_expiry = df[df['days_left'] == 0]
        warning = df[(df['days_left'] > 0) & (df['days_left'] <= 3)]
       
        # 期限切れ
        if not expired.empty:
            st.error("🚨 期限切れの食材があります！")
            for _, row in expired.iterrows():
                registered_by = row.get('registered_by', '不明')
                st.markdown(f"""
                    <div style="background-color: #ffcccc; padding: 15px; border-radius: 10px; margin: 10px 0; border: 3px solid red;">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <h2 style="color: red; margin: 0;">🚨 {row['name']}</h2>
                            <span style="background-color: rgba(255,255,255,0.7); padding: 5px 10px; border-radius: 15px; font-size: 14px;">👤 {registered_by}</span>
                        </div>
                        <p class="warning-font">期限切れ: {abs(row['days_left'])}日前に切れました</p>
                        <p><strong>賞味期限:</strong> {row['expiry_date']}</p>
                    </div>
                """, unsafe_allow_html=True)
       
        # 今日が期限
        if not today_expiry.empty:
            st.warning("⚠️ 今日が期限の食材があります！")
            for _, row in today_expiry.iterrows():
                registered_by = row.get('registered_by', '不明')
                st.markdown(f"""
                    <div style="background-color: #ffeecc; padding: 15px; border-radius: 10px; margin: 10px 0; border: 3px solid orange;">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <h2 style="color: orange; margin: 0;">⚠️ {row['name']}</h2>
                            <span style="background-color: rgba(255,255,255,0.7); padding: 5px 10px; border-radius: 15px; font-size: 14px;">👤 {registered_by}</span>
                        </div>
                        <p class="warning-font">今日が賞味期限です！</p>
                        <p><strong>早めに食べてください</strong></p>
                    </div>
                """, unsafe_allow_html=True)
       
        # 3日以内
        if not warning.empty:
            st.warning("📢 もうすぐ期限が切れる食材があります")
            for _, row in warning.iterrows():
                registered_by = row.get('registered_by', '不明')
                st.markdown(f"""
                    <div style="background-color: #fff4cc; padding: 15px; border-radius: 10px; margin: 10px 0; border: 2px solid orange;">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <h2 style="margin: 0;">{row['name']}</h2>
                            <span style="background-color: rgba(255,255,255,0.7); padding: 5px 10px; border-radius: 15px; font-size: 14px;">👤 {registered_by}</span>
                        </div>
                        <p class="big-font">あと{row['days_left']}日で期限です</p>
                        <p><strong>賞味期限:</strong> {row['expiry_date']}</p>
                    </div>
                """, unsafe_allow_html=True)
       
        # 問題なし
        if expired.empty and today_expiry.empty and warning.empty:
            st.success("✅ すべての食材の賞味期限に余裕があります！")
            st.balloons()
    else:
        st.info("📝 まだ食材が登録されていません。")
 
# タブ4: レシピ提案
with tab4:
    st.header("🍳 レシピ提案")
    st.markdown("賞味期限が近い食材を使ったレシピを提案します！")
    
    current_items = st.session_state['items']
    
    if isinstance(current_items, list) and len(current_items) > 0:
        df = pd.DataFrame(current_items)
        
        # 登録者情報がない古いデータに対応
        if 'registered_by' not in df.columns:
            df['registered_by'] = '不明'
            
        df['expiry_date_dt'] = pd.to_datetime(df['expiry_date'])
        today = pd.Timestamp(datetime.now().date())
        df['days_left'] = (df['expiry_date_dt'] - today).dt.days
        
        # 優先度の設定
        st.subheader("📊 食材の優先度")
        
        col_priority1, col_priority2, col_priority3 = st.columns(3)
        
        with col_priority1:
            urgent = df[df['days_left'] <= 2]
            st.metric("🚨 緊急（2日以内）", f"{len(urgent)}個", delta="最優先")
        
        with col_priority2:
            soon = df[(df['days_left'] > 2) & (df['days_left'] <= 5)]
            st.metric("⚠️ 近日（3-5日）", f"{len(soon)}個", delta="優先")
        
        with col_priority3:
            safe = df[df['days_left'] > 5]
            st.metric("✅ 余裕あり", f"{len(safe)}個")
        
        st.markdown("---")
        
        # レシピ生成の設定
        st.subheader("🎯 レシピ設定")
        
        col_recipe1, col_recipe2 = st.columns(2)
        
        with col_recipe1:
            recipe_priority = st.selectbox(
                "優先する食材",
                ["緊急の食材を優先", "すべての食材から選択", "特定の食材を指定"]
            )
        
        with col_recipe2:
            recipe_type = st.selectbox(
                "料理のタイプ",
                ["おまかせ", "和食", "洋食", "中華", "簡単レシピ", "作り置き"]
            )
        
        # 使用する食材の選択
        st.markdown("### 🥗 使いたい食材を選択")
        
        if recipe_priority == "特定の食材を指定":
            # 全食材から選択
            selected_items = st.multiselect(
                "食材を選んでください",
                options=df['name'].tolist(),
                default=df[df['days_left'] <= 5]['name'].tolist() if len(df[df['days_left'] <= 5]) > 0 else []
            )
        elif recipe_priority == "緊急の食材を優先":
            # 賞味期限が近い順に表示
            urgent_items = df[df['days_left'] <= 5].sort_values('days_left')
            if len(urgent_items) > 0:
                st.info(f"🚨 賞味期限が近い食材（5日以内）: {len(urgent_items)}個")
                selected_items = st.multiselect(
                    "レシピに使う食材を選択",
                    options=urgent_items['name'].tolist(),
                    default=urgent_items['name'].tolist()[:5] if len(urgent_items) >= 5 else urgent_items['name'].tolist()
                )
            else:
                st.success("✅ 緊急の食材はありません！")
                selected_items = st.multiselect(
                    "レシピに使う食材を選択",
                    options=df['name'].tolist(),
                    default=df['name'].tolist()[:3] if len(df) >= 3 else df['name'].tolist()
                )
        else:
            # すべての食材から
            selected_items = st.multiselect(
                "レシピに使う食材を選択",
                options=df['name'].tolist(),
                default=df.sort_values('days_left')['name'].tolist()[:5] if len(df) >= 5 else df['name'].tolist()
            )
        
        # 選択された食材の詳細表示
        if selected_items:
            st.markdown("#### 📝 選択された食材")
            selected_df = df[df['name'].isin(selected_items)].sort_values('days_left')
            
            cols = st.columns(min(len(selected_items), 4))
            for idx, (_, item) in enumerate(selected_df.iterrows()):
                with cols[idx % 4]:
                    days_left = item['days_left']
                    if days_left <= 2:
                        emoji = "🚨"
                        color = "#ffcccc"
                    elif days_left <= 5:
                        emoji = "⚠️"
                        color = "#fff4cc"
                    else:
                        emoji = "✅"
                        color = "#e8f5e9"
                    
                    st.markdown(f"""
                        <div style="background-color: {color}; padding: 10px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 24px;">{emoji}</div>
                            <div style="font-weight: bold;">{item['name']}</div>
                            <div style="font-size: 12px;">あと{days_left}日</div>
                        </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # レシピ生成ボタン
        if st.button("🍳 レシピを提案してもらう", type="primary", use_container_width=True):
            if not selected_items:
                st.error("⚠️ 食材を選択してください")
            else:
                with st.spinner("🤖 AIがレシピを考えています..."):
                    # レシピ生成（サンプル）
                    import time
                    time.sleep(1.5)  # 処理中の演出
                    
                    # 簡易的なレシピ生成ロジック
                    recipes = generate_recipe_suggestions(selected_items, recipe_type, selected_df)
                    
                    st.success("✅ レシピを提案しました！")
                    
                    for idx, recipe in enumerate(recipes):
                        with st.expander(f"📖 {recipe['title']}", expanded=(idx==0)):
                            col_r1, col_r2 = st.columns([2, 1])
                            
                            with col_r1:
                                st.markdown(f"**🍳 料理名:** {recipe['title']}")
                                st.markdown(f"**⏱️ 調理時間:** {recipe['time']}")
                                st.markdown(f"**👥 分量:** {recipe['servings']}")
                                st.markdown(f"**📊 難易度:** {recipe['difficulty']}")
                            
                            with col_r2:
                                st.markdown("**使用する食材:**")
                                for ingredient in recipe['ingredients_used']:
                                    st.markdown(f"• {ingredient}")
                            
                            st.markdown("---")
                            st.markdown("**📝 材料:**")
                            for ingredient in recipe['ingredients']:
                                st.markdown(f"• {ingredient}")
                            
                            st.markdown("**👨‍🍳 作り方:**")
                            for step_num, step in enumerate(recipe['steps'], 1):
                                st.markdown(f"{step_num}. {step}")
                            
                            st.markdown("---")
                            st.markdown(f"💡 **ポイント:** {recipe['tips']}")
        
        # 人気レシピのクイックアクセス
        st.markdown("---")
        st.subheader("🌟 人気のレシピカテゴリ")
        
        col_cat1, col_cat2, col_cat3, col_cat4 = st.columns(4)
        
        with col_cat1:
            if st.button("🍛 カレー・煮込み", use_container_width=True):
                st.info("カレーや煮込み料理は余った野菜や肉を使い切るのに最適です！")
        
        with col_cat2:
            if st.button("🥗 サラダ・副菜", use_container_width=True):
                st.info("新鮮な野菜を使って、健康的な一品を！")
        
        with col_cat3:
            if st.button("🍜 麺類・丼", use_container_width=True):
                st.info("手軽に作れて、いろんな食材を組み合わせられます！")
        
        with col_cat4:
            if st.button("🍰 作り置き", use_container_width=True):
                st.info("まとめて作って冷凍保存できるレシピです！")
    
    else:
        st.info("📝 食材を登録すると、レシピを提案できます！")
        st.markdown("「食材を登録」タブから食材を追加してください。")

# レシピ生成関数
def generate_recipe_suggestions(selected_items, recipe_type, items_df):
    """選択された食材からレシピを生成"""
    recipes = []
    
    # 食材の組み合わせに基づいてレシピを提案
    items_str = "、".join(selected_items)
    
    # レシピデータベース（簡易版）
    recipe_db = {
        "野菜炒め": {
            "keywords": ["野菜", "肉", "キャベツ", "ピーマン", "玉ねぎ", "にんじん"],
            "time": "15分",
            "servings": "2人分",
            "difficulty": "⭐ 簡単",
            "ingredients": [
                f"{item} 適量" for item in selected_items
            ] + ["醤油 大さじ1", "酒 大さじ1", "塩こしょう 少々", "サラダ油 大さじ1"],
            "steps": [
                "野菜を食べやすい大きさに切る",
                "フライパンに油を熱し、火が通りにくいものから炒める",
                "全体に火が通ったら、醤油・酒・塩こしょうで味付けする",
                "強火でサッと炒めて完成"
            ],
            "tips": "野菜は大きさを揃えて切ると、火の通りが均一になります。"
        },
        "具だくさん味噌汁": {
            "keywords": ["野菜", "豆腐", "キャベツ", "大根", "にんじん", "じゃがいも"],
            "time": "20分",
            "servings": "3-4人分",
            "difficulty": "⭐ 簡単",
            "ingredients": [
                f"{item} 適量" for item in selected_items
            ] + ["水 800ml", "だしの素 小さじ2", "味噌 大さじ3"],
            "steps": [
                "野菜を一口大に切る",
                "鍋に水とだしの素を入れて沸騰させる",
                "火が通りにくい野菜から順に入れて煮る",
                "全ての野菜が柔らかくなったら、味噌を溶き入れる",
                "ひと煮立ちしたら完成"
            ],
            "tips": "味噌は沸騰させると香りが飛ぶので、火を止める直前に入れましょう。"
        },
        "簡単チャーハン": {
            "keywords": ["卵", "野菜", "肉", "ネギ", "玉ねぎ"],
            "time": "10分",
            "servings": "2人分",
            "difficulty": "⭐⭐ 普通",
            "ingredients": [
                "ご飯 2膳分",
                f"{item} 適量" for item in selected_items
            ] + ["醤油 大さじ1", "塩こしょう 少々", "ごま油 大さじ1"],
            "steps": [
                "材料を細かく刻む",
                "フライパンを強火で熱し、ごま油を入れる",
                "溶き卵を入れてすぐにご飯を加え、パラパラになるまで炒める",
                "野菜や肉を加えてさらに炒める",
                "醤油と塩こしょうで味付けして完成"
            ],
            "tips": "ご飯は冷ご飯を使うとパラパラに仕上がりやすいです。"
        },
        "野菜たっぷりカレー": {
            "keywords": ["野菜", "肉", "じゃがいも", "にんじん", "玉ねぎ"],
            "time": "40分",
            "servings": "4人分",
            "difficulty": "⭐⭐ 普通",
            "ingredients": [
                f"{item} 適量" for item in selected_items
            ] + ["カレールー 1/2箱", "水 600ml", "サラダ油 大さじ1"],
            "steps": [
                "野菜と肉を一口大に切る",
                "鍋に油を熱し、肉を炒める",
                "野菜を加えてさらに炒める",
                "水を加えて沸騰したらアクを取り、弱火で20分煮込む",
                "火を止めてカレールーを溶かし、再び弱火で5分煮込む"
            ],
            "tips": "煮込む時間を長くすると、野菜の甘みが出て美味しくなります。"
        },
        "オムレツ": {
            "keywords": ["卵", "野菜", "チーズ", "ハム"],
            "time": "10分",
            "servings": "1-2人分",
            "difficulty": "⭐⭐ 普通",
            "ingredients": [
                "卵 3個",
                f"{item} 適量" for item in selected_items
            ] + ["塩こしょう 少々", "バター 10g", "牛乳 大さじ2"],
            "steps": [
                "具材を細かく切り、軽く炒めておく",
                "ボウルに卵を割り、牛乳と塩こしょうを加えてよく混ぜる",
                "フライパンにバターを熱し、卵液を流し入れる",
                "半熟になったら具材を乗せ、半分に折りたたむ",
                "形を整えて完成"
            ],
            "tips": "中火で手早く作ると、ふわふわに仕上がります。"
        }
    }
    
    # 選択された食材に基づいてレシピをマッチング
    for recipe_name, recipe_data in recipe_db.items():
        # キーワードマッチング
        match_score = sum(1 for item in selected_items if any(keyword in item for keyword in recipe_data["keywords"]))
        
        if match_score > 0 or recipe_type == "おまかせ":
            recipe = {
                "title": recipe_name,
                "time": recipe_data["time"],
                "servings": recipe_data["servings"],
                "difficulty": recipe_data["difficulty"],
                "ingredients_used": selected_items,
                "ingredients": recipe_data["ingredients"],
                "steps": recipe_data["steps"],
                "tips": recipe_data["tips"]
            }
            recipes.append(recipe)
    
    # レシピタイプでフィルタリング
    if recipe_type != "おまかせ":
        if recipe_type == "簡単レシピ":
            recipes = [r for r in recipes if "簡単" in r["difficulty"]]
        elif recipe_type == "和食":
            recipes = [r for r in recipes if any(word in r["title"] for word in ["味噌汁", "煮物", "焼き魚"])]
    
    # レシピが見つからない場合の汎用レシピ
    if not recipes:
        recipes.append({
            "title": f"{items_str}の炒め物",
            "time": "15分",
            "servings": "2人分",
            "difficulty": "⭐ 簡単",
            "ingredients_used": selected_items,
            "ingredients": [f"{item} 適量" for item in selected_items] + ["醤油 大さじ1", "みりん 大さじ1", "サラダ油 大さじ1"],
            "steps": [
                "材料を食べやすい大きさに切る",
                "フライパンに油を熱し、火が通りにくいものから順に炒める",
                "醤油とみりんで味付けする",
                "全体に味が馴染んだら完成"
            ],
            "tips": "余った食材を有効活用できる万能レシピです！"
        })
    
    return recipes[:3]  # 最大3つのレシピを返す
 
# サイドバー
with st.sidebar:
    st.header("⚙️ 設定")
   
    st.info("🔍 バーコード検索機能\n\nOpen Food Facts APIを使用（無料・APIキー不要）")
    
    st.divider()
    
    # 通知設定
    st.subheader("🔔 通知設定")
    
    # 通知の有効/無効
    if 'notification_enabled' not in st.session_state:
        st.session_state['notification_enabled'] = True
    
    notification_enabled = st.checkbox(
        "通知を有効にする",
        value=st.session_state['notification_enabled'],
        help="アプリを開いたときに賞味期限の警告を表示します"
    )
    st.session_state['notification_enabled'] = notification_enabled
    
    # 通知の日数設定
    if 'notification_days' not in st.session_state:
        st.session_state['notification_days'] = 3
    
    notification_days = st.slider(
        "何日前に通知するか",
        min_value=1,
        max_value=7,
        value=st.session_state['notification_days'],
        help="賞味期限の何日前から通知するかを設定"
    )
    st.session_state['notification_days'] = notification_days
    
    # 音声アラート
    if 'sound_alert' not in st.session_state:
        st.session_state['sound_alert'] = False
    
    sound_alert = st.checkbox(
        "音声アラート",
        value=st.session_state['sound_alert'],
        help="期限切れの食材がある場合に音でお知らせ"
    )
    st.session_state['sound_alert'] = sound_alert
   
    st.divider()
   
    st.header("📊 統計情報")
   
    # 現在のユーザー情報
    if st.session_state['current_user']:
        st.info(f"👤 {st.session_state['current_user']}さん")
    
    current_items = st.session_state['items']
   
    if isinstance(current_items, list) and len(current_items) > 0:
        total = len(current_items)
        df = pd.DataFrame(current_items)
        
        # 登録者情報がない古いデータに対応
        if 'registered_by' not in df.columns:
            df['registered_by'] = '不明'
            
        df['expiry_date_dt'] = pd.to_datetime(df['expiry_date'])
        today = pd.Timestamp(datetime.now().date())
        df['days_left'] = (df['expiry_date_dt'] - today).dt.days
       
        expired_count = len(df[df['days_left'] < 0])
        warning_count = len(df[(df['days_left'] >= 0) & (df['days_left'] <= 3)])
        safe_count = len(df[df['days_left'] > 3])
       
        st.metric("登録食材数", f"{total}個")
        st.metric("期限切れ", f"{expired_count}個", delta=None if expired_count == 0 else "注意")
        st.metric("要注意(3日以内)", f"{warning_count}個")
        st.metric("安全", f"{safe_count}個")
       
        # カテゴリ別
        st.subheader("カテゴリ別")
        category_counts = df['category'].value_counts()
        for cat, count in category_counts.items():
            st.write(f"• {cat}: {count}個")
        
        # 登録者別の統計
        st.subheader("登録者別")
        user_counts = df['registered_by'].value_counts()
        for user, count in user_counts.items():
            st.write(f"• {user}: {count}個")
    else:
        st.info("データがありません")
   
    st.divider()
   
    # すべての利用者の概要
    if len(st.session_state['users']) > 0:
        st.subheader("👥 全利用者")
        for user_name, user_items in st.session_state['users'].items():
            item_count = len(user_items) if isinstance(user_items, list) else 0
            if item_count > 0:
                # 警告のある食材をカウント
                df_temp = pd.DataFrame(user_items)
                df_temp['expiry_date_dt'] = pd.to_datetime(df_temp['expiry_date'])
                today = pd.Timestamp(datetime.now().date())
                df_temp['days_left'] = (df_temp['expiry_date_dt'] - today).dt.days
                warning_count = len(df_temp[df_temp['days_left'] <= 3])
               
                icon = "⚠️" if warning_count > 0 else "✅"
                st.write(f"{icon} **{user_name}**: {item_count}個")
                if warning_count > 0:
                    st.write(f"   要注意: {warning_count}個")
            else:
                st.write(f"📝 **{user_name}**: 未登録")
   
    st.divider()
   
    # データ管理（モバイル対応）
    st.subheader("🗑️ データ管理")
   
    # 現在のユーザーのデータを削除
    if st.session_state['current_user']:
        if st.button("このユーザーの食材を全削除", use_container_width=True):
            st.session_state['items'] = []
            st.session_state['users'][st.session_state['current_user']] = []
            st.rerun()
       
        if st.button("このユーザーを削除", use_container_width=True):
            del st.session_state['users'][st.session_state['current_user']]
            st.session_state['current_user'] = None
            st.session_state['items'] = []
            st.session_state['items_user'] = None
            st.rerun()
   
    # すべてのデータのクリア
    if st.button("🗑️ すべてのデータを削除", use_container_width=True):
        st.session_state['users'] = {}
        st.session_state['current_user'] = None
        st.session_state['items'] = []
        st.session_state['items_user'] = None
        st.rerun()