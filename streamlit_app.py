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
 
# カスタムCSS（大きな文字とボタン）
st.markdown("""
    <style>
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
    .stButton>button {
        font-size: 20px;
        padding: 15px 30px;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)
 
# タイトル
st.title("🍱 冷蔵庫管理アプリ")
 
st.markdown("---")
 
# ユーザー選択・登録セクション
col_user1, col_user2, col_user3 = st.columns([2, 2, 1])
 
with col_user1:
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
            help="管理したい方の名前を選んでください"
        )
    else:
        selected_user = "新しい利用者を追加"
        st.info("👋 最初の利用者を登録してください")
 
with col_user2:
    if selected_user == "新しい利用者を追加":
        new_user_name = st.text_input(
            "利用者の名前",
            placeholder="例: 田中太郎、山田花子",
            help="名前を入力してください"
        )
 
with col_user3:
    st.write("")  # スペース調整
    st.write("")  # スペース調整
    if selected_user == "新しい利用者を追加":
        if st.button("➕ 登録", type="primary"):
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
        if st.button("✅ 選択"):
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
st.markdown("### 食材の管理を簡単に！")
 
# タブの作成
tab1, tab2, tab3 = st.tabs(["📝 食材を登録", "📋 食材リスト", "⚠️ 警告"])
 
# タブ1: 食材登録
with tab1:
    st.header("新しい食材を登録")
   
    col1, col2 = st.columns(2)
   
    with col1:
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
   
    with col2:
        st.subheader("📝 食材情報を入力")
       
        # バーコード番号入力
        barcode = st.text_input(
            "バーコード番号（JAN）",
            placeholder="例: 4901234567890",
            help="バーコードの番号を入力してください（13桁）",
            key="barcode_input"
        )
       
        # バーコードから商品名を検索するボタン
        col_search1, col_search2 = st.columns([1, 2])
        with col_search1:
            search_button = st.button("🔍 商品名を検索", type="secondary")
       
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
       
        # 登録ボタン
        if st.button("✅ 登録する", type="primary", key="register_button"):
            if item_name:
                new_item = {
                    'name': item_name,
                    'barcode': barcode if barcode else "未登録",
                    'purchase_date': purchase_date.strftime('%Y-%m-%d'),
                    'expiry_date': expiry_date.strftime('%Y-%m-%d'),
                    'category': category,
                    'quantity': quantity,
                    'registered_at': datetime.now().strftime('%Y-%m-%d %H:%M')
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
       
        # 賞味期限までの日数を計算
        df['expiry_date_dt'] = pd.to_datetime(df['expiry_date'])
        today = pd.Timestamp(datetime.now().date())
        df['days_left'] = (df['expiry_date_dt'] - today).dt.days
       
        # ソート
        df = df.sort_values('days_left')
        df = df.reset_index(drop=True)
       
        # カテゴリでフィルター
        selected_category = st.selectbox(
            "カテゴリで絞り込み",
            ["すべて"] + list(df['category'].unique())
        )
       
        if selected_category != "すべて":
            df_display = df[df['category'] == selected_category].reset_index(drop=True)
        else:
            df_display = df
       
        # 食材カードを表示
        for idx in range(len(df_display)):
            row = df_display.iloc[idx]
            days_left = row['days_left']
           
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
           
            # カード表示
            with st.container():
                st.markdown(f"""
                    <div style="background-color: {alert_color}; padding: 20px; border-radius: 10px; margin: 10px 0;">
                        <h2 style="margin: 0;">{row['name']} ({row['category']})</h2>
                        <p class="{alert_class}">{alert_text}</p>
                        <p><strong>数量:</strong> {row['quantity']}</p>
                        <p><strong>購入日:</strong> {row['purchase_date']}</p>
                        <p><strong>賞味期限:</strong> {row['expiry_date']}</p>
                        <p><strong>バーコード:</strong> {row['barcode']}</p>
                    </div>
                """, unsafe_allow_html=True)
               
                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button(f"🗑️ 削除", key=f"del_{idx}_{row['name']}"):
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
                st.markdown(f"""
                    <div style="background-color: #ffcccc; padding: 15px; border-radius: 10px; margin: 10px 0; border: 3px solid red;">
                        <h2 style="color: red;">🚨 {row['name']}</h2>
                        <p class="warning-font">期限切れ: {abs(row['days_left'])}日前に切れました</p>
                        <p><strong>賞味期限:</strong> {row['expiry_date']}</p>
                    </div>
                """, unsafe_allow_html=True)
       
        # 今日が期限
        if not today_expiry.empty:
            st.warning("⚠️ 今日が期限の食材があります！")
            for _, row in today_expiry.iterrows():
                st.markdown(f"""
                    <div style="background-color: #ffeecc; padding: 15px; border-radius: 10px; margin: 10px 0; border: 3px solid orange;">
                        <h2 style="color: orange;">⚠️ {row['name']}</h2>
                        <p class="warning-font">今日が賞味期限です！</p>
                        <p><strong>早めに食べてください</strong></p>
                    </div>
                """, unsafe_allow_html=True)
       
        # 3日以内
        if not warning.empty:
            st.warning("📢 もうすぐ期限が切れる食材があります")
            for _, row in warning.iterrows():
                st.markdown(f"""
                    <div style="background-color: #fff4cc; padding: 15px; border-radius: 10px; margin: 10px 0; border: 2px solid orange;">
                        <h2>{row['name']}</h2>
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
 
# サイドバー
with st.sidebar:
    st.header("⚙️ 設定")
   
    st.info("🔍 バーコード検索機能\n\nOpen Food Facts APIを使用（無料・APIキー不要）")
   
    st.divider()
   
    st.header("📊 統計情報")
   
    # 現在のユーザー情報
    if st.session_state['current_user']:
        st.info(f"👤 {st.session_state['current_user']}さん")
    
    current_items = st.session_state['items']
   
    if isinstance(current_items, list) and len(current_items) > 0:
        total = len(current_items)
        df = pd.DataFrame(current_items)
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
   
    # データ管理
    st.subheader("🗑️ データ管理")
   
    # 現在のユーザーのデータを削除
    if st.session_state['current_user']:
        if st.button("このユーザーの食材を全削除"):
            st.session_state['items'] = []
            st.session_state['users'][st.session_state['current_user']] = []
            st.rerun()
       
        if st.button("このユーザーを削除"):
            del st.session_state['users'][st.session_state['current_user']]
            st.session_state['current_user'] = None
            st.session_state['items'] = []
            st.session_state['items_user'] = None
            st.rerun()
   
    # すべてのデータのクリア
    if st.button("🗑️ すべてのデータを削除"):
        st.session_state['users'] = {}
        st.session_state['current_user'] = None
        st.session_state['items'] = []
        st.session_state['items_user'] = None
        st.rerun()