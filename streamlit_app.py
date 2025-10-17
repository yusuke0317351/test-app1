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

# セッション状態の完全リセット（デバッグ用）
if 'app_initialized' not in st.session_state:
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
    """バーコード（JAN）から商品名を取得"""
    if not barcode:
        return None
   
    try:
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
       
        if data.get('status') == 1:
            product = data.get('product', {})
            product_name = (product.get('product_name_ja') or 
                          product.get('product_name') or 
                          product.get('product_name_en'))
            
            if product_name:
                product_name = product_name.split('【')[0].split('(')[0].strip()
                return product_name
        
        return None
           
    except Exception as e:
        st.error(f"API エラー: {str(e)}")
        return None

# レシピ生成関数（大幅改善版）
def generate_recipe_suggestions(selected_items, recipe_type, items_df):
    """選択された食材からレシピを生成"""
    recipes = []
    items_str = "、".join(selected_items)
    
    # 食材リストを生成するヘルパー関数
    def make_ingredients(items):
        return [f"{item} 適量" for item in items]
    
    # 大幅に拡充したレシピデータベース
    recipe_db = {
        # 和食
        "野菜炒め": {
            "keywords": ["野菜", "肉", "キャベツ", "ピーマン", "玉ねぎ", "にんじん", "もやし"],
            "type": ["和食", "簡単レシピ"],
            "time": "15分",
            "servings": "2人分",
            "difficulty": "⭐ 簡単",
            "ingredients": make_ingredients(selected_items) + ["醤油 大さじ1", "酒 大さじ1", "塩こしょう 少々", "サラダ油 大さじ1"],
            "steps": [
                "野菜を食べやすい大きさに切る",
                "フライパンに油を熱し、火が通りにくいものから炒める",
                "全体に火が通ったら、醤油・酒・塩こしょうで味付けする",
                "強火でサッと炒めて完成"
            ],
            "tips": "野菜は大きさを揃えて切ると、火の通りが均一になります。"
        },
        "具だくさん味噌汁": {
            "keywords": ["野菜", "豆腐", "キャベツ", "大根", "にんじん", "じゃがいも", "わかめ"],
            "type": ["和食", "簡単レシピ"],
            "time": "20分",
            "servings": "3-4人分",
            "difficulty": "⭐ 簡単",
            "ingredients": make_ingredients(selected_items) + ["水 800ml", "だしの素 小さじ2", "味噌 大さじ3"],
            "steps": [
                "野菜を一口大に切る",
                "鍋に水とだしの素を入れて沸騰させる",
                "火が通りにくい野菜から順に入れて煮る",
                "全ての野菜が柔らかくなったら、味噌を溶き入れる",
                "ひと煮立ちしたら完成"
            ],
            "tips": "味噌は沸騰させると香りが飛ぶので、火を止める直前に入れましょう。"
        },
        "肉じゃが": {
            "keywords": ["じゃがいも", "にんじん", "玉ねぎ", "肉", "牛肉", "豚肉"],
            "type": ["和食"],
            "time": "30分",
            "servings": "3-4人分",
            "difficulty": "⭐⭐ 普通",
            "ingredients": make_ingredients(selected_items) + ["醤油 大さじ3", "砂糖 大さじ2", "みりん 大さじ2", "だし汁 400ml"],
            "steps": [
                "じゃがいも・にんじん・玉ねぎを一口大に切る",
                "鍋に油を熱し、肉を炒める",
                "野菜を加えて軽く炒める",
                "だし汁と調味料を加えて20分ほど煮込む",
                "じゃがいもが柔らかくなったら完成"
            ],
            "tips": "じゃがいもは煮崩れしにくいメークインがおすすめです。"
        },
        "親子丼": {
            "keywords": ["鶏肉", "卵", "玉ねぎ"],
            "type": ["和食", "簡単レシピ"],
            "time": "15分",
            "servings": "2人分",
            "difficulty": "⭐ 簡単",
            "ingredients": make_ingredients(selected_items) + ["ご飯 2膳", "醤油 大さじ2", "みりん 大さじ2", "砂糖 大さじ1", "だし汁 100ml"],
            "steps": [
                "玉ねぎをスライスし、鶏肉は一口大に切る",
                "フライパンにだし汁と調味料を入れて煮立てる",
                "鶏肉と玉ねぎを加えて煮る",
                "溶き卵を回し入れ、半熟になったらご飯にのせる"
            ],
            "tips": "卵は2回に分けて入れると、ふわふわに仕上がります。"
        },
        "鮭のムニエル": {
            "keywords": ["鮭", "魚"],
            "type": ["洋食", "簡単レシピ"],
            "time": "15分",
            "servings": "2人分",
            "difficulty": "⭐ 簡単",
            "ingredients": make_ingredients(selected_items) + ["小麦粉 適量", "バター 20g", "レモン汁 少々", "塩こしょう 少々"],
            "steps": [
                "鮭に塩こしょうをして、小麦粉をまぶす",
                "フライパンにバターを溶かし、鮭を焼く",
                "両面こんがり焼けたら、レモン汁をかける",
                "お皿に盛り付けて完成"
            ],
            "tips": "小麦粉は薄くまぶすと、カリッと仕上がります。"
        },
        # 中華・アジア
        "簡単チャーハン": {
            "keywords": ["卵", "野菜", "肉", "ネギ", "玉ねぎ", "ハム", "ソーセージ"],
            "type": ["中華", "簡単レシピ"],
            "time": "10分",
            "servings": "2人分",
            "difficulty": "⭐⭐ 普通",
            "ingredients": ["ご飯 2膳分"] + make_ingredients(selected_items) + ["醤油 大さじ1", "塩こしょう 少々", "ごま油 大さじ1", "中華スープの素 小さじ1"],
            "steps": [
                "材料を細かく刻む",
                "フライパンを強火で熱し、ごま油を入れる",
                "溶き卵を入れてすぐにご飯を加え、パラパラになるまで炒める",
                "野菜や肉を加えてさらに炒める",
                "醤油、中華スープの素、塩こしょうで味付けして完成"
            ],
            "tips": "ご飯は冷ご飯を使うとパラパラに仕上がりやすいです。"
        },
        "麻婆豆腐": {
            "keywords": ["豆腐", "肉", "ひき肉", "ネギ"],
            "type": ["中華"],
            "time": "20分",
            "servings": "2-3人分",
            "difficulty": "⭐⭐ 普通",
            "ingredients": make_ingredients(selected_items) + ["豆板醤 大さじ1", "醤油 大さじ1", "鶏ガラスープ 200ml", "片栗粉 大さじ1", "ごま油 少々"],
            "steps": [
                "豆腐を2cm角に切り、下茹でする",
                "フライパンで肉を炒め、豆板醤を加える",
                "スープと調味料を加えて煮立てる",
                "豆腐を加えて煮込み、水溶き片栗粉でとろみをつける",
                "ごま油を回しかけて完成"
            ],
            "tips": "豆板醤の量で辛さを調整できます。"
        },
        "八宝菜": {
            "keywords": ["野菜", "肉", "キャベツ", "にんじん", "玉ねぎ", "ピーマン", "豚肉"],
            "type": ["中華"],
            "time": "20分",
            "servings": "3-4人分",
            "difficulty": "⭐⭐ 普通",
            "ingredients": make_ingredients(selected_items) + ["オイスターソース 大さじ1", "醤油 大さじ1", "鶏ガラスープ 150ml", "片栗粉 大さじ1", "ごま油 大さじ1"],
            "steps": [
                "材料を食べやすい大きさに切る",
                "フライパンで肉を炒め、野菜を加える",
                "スープと調味料を加えて炒め煮する",
                "水溶き片栗粉でとろみをつけて完成"
            ],
            "tips": "具材はお好みで変更できます。海鮮を入れても美味しいです。"
        },
        # 洋食
        "オムレツ": {
            "keywords": ["卵", "野菜", "チーズ", "ハム"],
            "type": ["洋食", "簡単レシピ"],
            "time": "10分",
            "servings": "1-2人分",
            "difficulty": "⭐⭐ 普通",
            "ingredients": make_ingredients(selected_items) + ["牛乳 大さじ2", "バター 10g", "塩こしょう 少々"],
            "steps": [
                "卵を溶きほぐし、牛乳、塩こしょうを混ぜる",
                "具材は細かく刻んでおく",
                "フライパンにバターを溶かし、卵液を流し込む",
                "半熟になったら具材をのせて半分に折る"
            ],
            "tips": "火は中火より少し弱めで、ゆっくり焼くとふわふわに仕上がります。"
        },
        "トマトパスタ": {
            "keywords": ["トマト", "パスタ", "野菜", "ベーコン", "ツナ"],
            "type": ["洋食"],
            "time": "20分",
            "servings": "2人分",
            "difficulty": "⭐ 簡単",
            "ingredients": ["パスタ 200g"] + make_ingredients(selected_items) + ["トマト缶 1缶", "にんにく 1片", "オリーブオイル 大さじ2", "塩こしょう 少々", "バジル お好みで"],
            "steps": [
                "パスタを茹で始める",
                "にんにくをみじん切りにし、オリーブオイルで炒める",
                "トマト缶と具材を加えて煮込む",
                "茹でたパスタを加えて和え、塩こしょうで味を整える"
            ],
            "tips": "パスタの茹で汁を少し加えると、ソースがよく絡みます。"
        },
        "クリームシチュー": {
            "keywords": ["じゃがいも", "にんじん", "玉ねぎ", "肉", "鶏肉", "ブロッコリー"],
            "type": ["洋食"],
            "time": "30分",
            "servings": "3-4人分",
            "difficulty": "⭐⭐ 普通",
            "ingredients": make_ingredients(selected_items) + ["牛乳 400ml", "シチューのルー 1/2箱", "バター 20g", "水 400ml"],
            "steps": [
                "材料を一口大に切る",
                "鍋にバターを溶かし、肉と野菜を炒める",
                "水を加えて20分ほど煮込む",
                "ルーと牛乳を加えてとろみがつくまで煮る"
            ],
            "tips": "ルーを入れる前に一度火を止めると、ダマになりにくいです。"
        },
        "ハンバーグ": {
            "keywords": ["ひき肉", "肉", "玉ねぎ", "卵"],
            "type": ["洋食"],
            "time": "30分",
            "servings": "3-4個分",
            "difficulty": "⭐⭐⭐ 普通",
            "ingredients": make_ingredients(selected_items) + ["パン粉 大さじ3", "牛乳 大さじ2", "ナツメグ 少々", "塩こしょう 少々", "ケチャップ 大さじ2", "ウスターソース 大さじ2"],
            "steps": [
                "玉ねぎをみじん切りにして炒め、冷ます",
                "ひき肉に卵、パン粉、牛乳、玉ねぎ、調味料を混ぜる",
                "よく練って小判型に成形する",
                "フライパンで両面を焼き、蓋をして中まで火を通す",
                "ソースで味付けして完成"
            ],
            "tips": "タネを冷蔵庫で30分寝かせると、成形しやすくなります。"
        },
        # その他
        "野菜スープ": {
            "keywords": ["野菜", "キャベツ", "にんじん", "玉ねぎ", "じゃがいも", "トマト"],
            "type": ["簡単レシピ"],
            "time": "20分",
            "servings": "3-4人分",
            "difficulty": "⭐ 簡単",
            "ingredients": make_ingredients(selected_items) + ["水 800ml", "コンソメ 2個", "塩こしょう 少々", "オリーブオイル 大さじ1"],
            "steps": [
                "野菜を一口大に切る",
                "鍋にオリーブオイルを熱し、野菜を軽く炒める",
                "水とコンソメを加えて15分ほど煮込む",
                "塩こしょうで味を整えて完成"
            ],
            "tips": "余った野菜を何でも入れられる、冷蔵庫整理にぴったりのレシピです。"
        },
        "卵焼き": {
            "keywords": ["卵"],
            "type": ["和食", "簡単レシピ"],
            "time": "10分",
            "servings": "2人分",
            "difficulty": "⭐⭐ 普通",
            "ingredients": make_ingredients(selected_items) + ["砂糖 大さじ1", "醤油 小さじ1", "だし汁 大さじ2", "サラダ油 適量"],
            "steps": [
                "卵を溶きほぐし、調味料を混ぜる",
                "卵焼き器に油を薄く引き、卵液を1/3流し込む",
                "半熟になったら手前に巻く",
                "同じ作業を繰り返して厚みを出す"
            ],
            "tips": "火加減は中火で、焦げないように注意しましょう。"
        },
        "サラダ": {
            "keywords": ["野菜", "レタス", "キャベツ", "トマト", "きゅうり", "にんじん"],
            "type": ["簡単レシピ"],
            "time": "5分",
            "servings": "2-3人分",
            "difficulty": "⭐ 簡単",
            "ingredients": make_ingredients(selected_items) + ["ドレッシング お好みで", "塩 少々"],
            "steps": [
                "野菜をよく洗う",
                "食べやすい大きさに切る",
                "お皿に盛り付け、ドレッシングをかける"
            ],
            "tips": "野菜は冷水に浸すとシャキッとします。"
        }
    }
    
    # レシピマッチングとスコアリング
    scored_recipes = []
    for recipe_name, recipe_data in recipe_db.items():
        match_score = sum(1 for item in selected_items if any(keyword in item for keyword in recipe_data["keywords"]))
        
        # レシピタイプでのフィルタリング
        type_match = False
        if recipe_type == "おまかせ":
            type_match = True
        elif recipe_type in recipe_data["type"]:
            type_match = True
        
        if match_score > 0 and type_match:
            scored_recipes.append({
                "name": recipe_name,
                "score": match_score,
                "data": recipe_data
            })
    
    # スコアでソートして上位を取得
    scored_recipes.sort(key=lambda x: x["score"], reverse=True)
    
    # レシピを構築
    for scored in scored_recipes[:5]:  # 上位5つまで
        recipe_data = scored["data"]
        recipe = {
            "title": scored["name"],
            "time": recipe_data["time"],
            "servings": recipe_data["servings"],
            "difficulty": recipe_data["difficulty"],
            "ingredients_used": selected_items,
            "ingredients": recipe_data["ingredients"],
            "steps": recipe_data["steps"],
            "tips": recipe_data["tips"],
            "match_count": scored["score"]
        }
        recipes.append(recipe)
    
    # デフォルトレシピ（マッチするものがない場合）
    if not recipes:
        recipes.append({
            "title": f"{items_str}の炒め物",
            "time": "15分",
            "servings": "2人分",
            "difficulty": "⭐ 簡単",
            "ingredients_used": selected_items,
            "ingredients": make_ingredients(selected_items) + ["醤油 大さじ1", "みりん 大さじ1", "サラダ油 大さじ1"],
            "steps": [
                "材料を食べやすい大きさに切る",
                "フライパンに油を熱し、火が通りにくいものから順に炒める",
                "醤油とみりんで味付けする",
                "全体に味が馴染んだら完成"
            ],
            "tips": "余った食材を有効活用できる万能レシピです！",
            "match_count": 0
        })
    
    return recipes[:3]

# 日付の検証
def validate_dates(purchase_date, expiry_date):
    """日付の妥当性をチェック"""
    if expiry_date < purchase_date:
        return False, "賞味期限は購入日より後の日付を選択してください"
    return True, ""
 
# カスタムCSS
st.markdown("""
    <style>
    .big-font { font-size: 24px !important; font-weight: bold; }
    .warning-font { font-size: 28px !important; font-weight: bold; color: #ff4444; }
    .safe-font { font-size: 22px !important; color: #44ff44; }
    .stButton>button { font-size: 18px; padding: 15px 20px; width: 100%; min-height: 50px; border-radius: 10px; font-weight: bold; }
    @media (max-width: 768px) {
        h1 { font-size: 28px !important; }
        h2 { font-size: 22px !important; }
        .stButton>button { font-size: 20px; padding: 18px 25px; min-height: 60px; }
        .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>select { font-size: 18px !important; padding: 12px !important; min-height: 50px !important; }
    }
    </style>
    """, unsafe_allow_html=True)
 
st.title("🍱 冷蔵庫管理アプリ")
st.markdown("---")
 
# ユーザー選択
st.markdown("### 👤 利用者を選択")

if len(st.session_state['users']) > 0:
    user_list = ["新しい利用者を追加"] + list(st.session_state['users'].keys())
    current_index = 0
    if st.session_state['current_user'] and st.session_state['current_user'] in user_list:
        current_index = user_list.index(st.session_state['current_user'])
    
    selected_user = st.selectbox("利用者名", user_list, index=current_index, label_visibility="collapsed")
else:
    selected_user = "新しい利用者を追加"
    st.info("👋 最初の利用者を登録してください")

if selected_user == "新しい利用者を追加":
    new_user_name = st.text_input("利用者の名前", placeholder="例: 田中太郎")
    
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
 
if st.session_state['current_user']:
    st.success(f"📱 現在の利用者: **{st.session_state['current_user']}**さん")
    if st.session_state['items_user'] != st.session_state['current_user']:
        st.session_state['items'] = list(st.session_state['users'].get(st.session_state['current_user'], []))
        st.session_state['items_user'] = st.session_state['current_user']
else:
    st.warning("⚠️ 利用者を選択してください")
    st.stop()
 
st.markdown("---")

# 通知
if st.session_state.get('notification_enabled', True):
    current_items = st.session_state['items']
    if isinstance(current_items, list) and len(current_items) > 0:
        df_check = pd.DataFrame(current_items)
        df_check['expiry_date_dt'] = pd.to_datetime(df_check['expiry_date'])
        today = pd.Timestamp(datetime.now().date())
        df_check['days_left'] = (df_check['expiry_date_dt'] - today).dt.days
        
        notification_days = st.session_state.get('notification_days', 3)
        
        expired = df_check[df_check['days_left'] < 0]
        if not expired.empty:
            st.error(f"🚨 **緊急**: {len(expired)}個の食材が期限切れです！")
        
        today_expiry = df_check[df_check['days_left'] == 0]
        if not today_expiry.empty:
            st.warning(f"⚠️ **今日が期限**: {len(today_expiry)}個")
        
        warning_items = df_check[(df_check['days_left'] > 0) & (df_check['days_left'] <= notification_days)]
        if not warning_items.empty:
            st.info(f"📢 **注意**: {len(warning_items)}個が{notification_days}日以内に期限切れ")

st.markdown("---")
 
# タブ
tab1, tab2, tab3, tab4 = st.tabs(["📝 食材を登録", "📋 食材リスト", "⚠️ 警告", "🍳 レシピ提案"])
 
# タブ1: 食材登録
with tab1:
    st.header("新しい食材を登録")
   
    uploaded_file = st.file_uploader("写真をアップロード", type=['png', 'jpg', 'jpeg'])
   
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="アップロードされた写真", use_container_width=True)
   
    barcode = st.text_input("バーコード番号（JAN）", placeholder="例: 4901234567890", key="barcode_input")
   
    search_button = st.button("🔍 商品名を検索", type="secondary", use_container_width=True)
   
    auto_product_name = ""
    if search_button and barcode:
        with st.spinner("商品を検索中..."):
            auto_product_name = get_product_name_from_barcode(barcode)
            if auto_product_name:
                st.success(f"✅ 商品が見つかりました: {auto_product_name}")
            else:
                st.warning("⚠️ 商品が見つかりませんでした")
   
    item_name = st.text_input("食材名", value=auto_product_name if auto_product_name else "", placeholder="例: 牛乳", key="item_name_input")
    purchase_date = st.date_input("購入日", value=datetime.now())
    expiry_date = st.date_input("賞味期限", value=datetime.now() + timedelta(days=7))
    category = st.selectbox("カテゴリ", ["野菜", "果物", "肉類", "魚類", "乳製品", "卵", "調味料", "その他"])
    quantity = st.number_input("数量", min_value=1, value=1)
   
    st.markdown("---")
    if st.button("✅ 登録する", type="primary", key="register_button", use_container_width=True):
        if item_name:
            # 日付の検証
            is_valid, error_msg = validate_dates(purchase_date, expiry_date)
            if not is_valid:
                st.error(f"⚠️ {error_msg}")
            else:
                new_item = {
                    'name': item_name,
                    'barcode': barcode if barcode else "未登録",
                    'purchase_date': purchase_date.strftime('%Y-%m-%d'),
                    'expiry_date': expiry_date.strftime('%Y-%m-%d'),
                    'category': category,
                    'quantity': quantity,
                    'registered_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'registered_by': st.session_state['current_user']
                }
                current_items = list(st.session_state['items'])
                current_items.append(new_item)
                st.session_state['items'] = current_items
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
        df = pd.DataFrame(current_items)
        
        if 'registered_by' not in df.columns:
            df['registered_by'] = '不明'
       
        df['expiry_date_dt'] = pd.to_datetime(df['expiry_date'])
        today = pd.Timestamp(datetime.now().date())
        df['days_left'] = (df['expiry_date_dt'] - today).dt.days
        df = df.sort_values('days_left').reset_index(drop=True)
       
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            selected_category = st.selectbox("カテゴリで絞り込み", ["すべて"] + list(df['category'].unique()))
        
        with col_filter2:
            unique_users = list(df['registered_by'].unique())
            selected_user_filter = st.selectbox("登録者で絞り込み", ["すべて"] + unique_users)
       
        df_display = df.copy()
        if selected_category != "すべて":
            df_display = df_display[df_display['category'] == selected_category]
        if selected_user_filter != "すべて":
            df_display = df_display[df_display['registered_by'] == selected_user_filter]
        
        df_display = df_display.reset_index(drop=True)
        
        if len(df_display) > 0:
            st.info(f"📊 表示中: {len(df_display)}個 / 全{len(df)}個")
       
        for idx in range(len(df_display)):
            row = df_display.iloc[idx]
            days_left = row['days_left']
            registered_by = row.get('registered_by', '不明')
           
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
           
            with st.container():
                st.markdown(f"""
                    <div style="background-color: {alert_color}; padding: 15px; border-radius: 10px; margin: 10px 0;">
                        <h2 style="margin: 0; font-size: 20px;">{row['name']} ({row['category']})</h2>
                        <p class="{alert_class}" style="margin: 10px 0;">{alert_text}</p>
                        <p style="margin: 5px 0;"><strong>数量:</strong> {row['quantity']}</p>
                        <p style="margin: 5px 0;"><strong>購入日:</strong> {row['purchase_date']}</p>
                        <p style="margin: 5px 0;"><strong>賞味期限:</strong> {row['expiry_date']}</p>
                        <p style="margin: 5px 0;"><strong>登録者:</strong> {registered_by}</p>
                    </div>
                """, unsafe_allow_html=True)
               
                if st.button(f"🗑️ 削除", key=f"del_{idx}_{row['name']}_{row['purchase_date']}", use_container_width=True):
                    item_to_remove = row.to_dict()
                    updated_items = [item for item in current_items if not all(item.get(k) == v for k, v in item_to_remove.items())]
                    st.session_state['items'] = updated_items
                    st.session_state['users'][st.session_state['current_user']] = list(updated_items)
                    st.success("削除しました！")
                    st.rerun()
    else:
        st.info("📝 まだ食材が登録されていません")
 
# タブ3: 警告
with tab3:
    st.header("⚠️ 賞味期限の警告")
    
    current_items = st.session_state['items']
   
    if isinstance(current_items, list) and len(current_items) > 0:
        df = pd.DataFrame(current_items)
        
        if 'registered_by' not in df.columns:
            df['registered_by'] = '不明'
            
        df['expiry_date_dt'] = pd.to_datetime(df['expiry_date'])
        today = pd.Timestamp(datetime.now().date())
        df['days_left'] = (df['expiry_date_dt'] - today).dt.days
       
        expired = df[df['days_left'] < 0].sort_values('days_left')
        today_expiry = df[df['days_left'] == 0]
        warning = df[(df['days_left'] > 0) & (df['days_left'] <= 3)].sort_values('days_left')
       
        if not expired.empty:
            st.error(f"🚨 期限切れの食材が {len(expired)} 個あります！")
            for _, row in expired.iterrows():
                st.markdown(f"**{row['name']}** ({row['category']}) - 期限切れ: {abs(row['days_left'])}日前")
       
        if not today_expiry.empty:
            st.warning(f"⚠️ 今日が期限の食材が {len(today_expiry)} 個あります！")
            for _, row in today_expiry.iterrows():
                st.markdown(f"**{row['name']}** ({row['category']}) - 今日が賞味期限")
       
        if not warning.empty:
            st.warning(f"📢 もうすぐ期限が切れる食材が {len(warning)} 個あります")
            for _, row in warning.iterrows():
                st.markdown(f"**{row['name']}** ({row['category']}) - あと{row['days_left']}日")
       
        if expired.empty and today_expiry.empty and warning.empty:
            st.success("✅ すべての食材の賞味期限に余裕があります！")
    else:
        st.info("📝 まだ食材が登録されていません")
 
# タブ4: レシピ提案
with tab4:
    st.header("🍳 レシピ提案")
    
    current_items = st.session_state['items']
    
    if isinstance(current_items, list) and len(current_items) > 0:
        df = pd.DataFrame(current_items)
        
        if 'registered_by' not in df.columns:
            df['registered_by'] = '不明'
            
        df['expiry_date_dt'] = pd.to_datetime(df['expiry_date'])
        today = pd.Timestamp(datetime.now().date())
        df['days_left'] = (df['expiry_date_dt'] - today).dt.days
        
        st.subheader("🎯 レシピ設定")
        
        col_recipe1, col_recipe2 = st.columns(2)
        
        with col_recipe1:
            recipe_priority = st.selectbox("優先する食材", ["緊急の食材を優先", "すべての食材から選択"])
        
        with col_recipe2:
            recipe_type = st.selectbox("料理のタイプ", ["おまかせ", "和食", "洋食", "簡単レシピ"])
        
        st.markdown("### 🥗 使いたい食材を選択")
        
        if recipe_priority == "緊急の食材を優先":
            urgent_items = df[df['days_left'] <= 5].sort_values('days_left')
            if len(urgent_items) > 0:
                selected_items = st.multiselect("レシピに使う食材", options=urgent_items['name'].tolist(), default=urgent_items['name'].tolist()[:5])
            else:
                selected_items = st.multiselect("レシピに使う食材", options=df['name'].tolist())
        else:
            selected_items = st.multiselect("レシピに使う食材", options=df['name'].tolist())
        
        if st.button("🍳 レシピを提案してもらう", type="primary", use_container_width=True):
            if not selected_items:
                st.error("⚠️ 食材を選択してください")
            else:
                with st.spinner("🤖 AIがレシピを考えています..."):
                    import time
                    time.sleep(1)
                    
                    recipes = generate_recipe_suggestions(selected_items, recipe_type, df)
                    
                    st.success("✅ レシピを提案しました！")
                    
                    for idx, recipe in enumerate(recipes):
                        with st.expander(f"📖 {recipe['title']}", expanded=(idx==0)):
                            st.markdown(f"**🍳 料理名:** {recipe['title']}")
                            st.markdown(f"**⏱️ 調理時間:** {recipe['time']}")
                            st.markdown(f"**👥 分量:** {recipe['servings']}")
                            st.markdown(f"**📊 難易度:** {recipe['difficulty']}")
                            
                            st.markdown("**📝 材料:**")
                            for ingredient in recipe['ingredients']:
                                st.markdown(f"• {ingredient}")
                            
                            st.markdown("**👨‍🍳 作り方:**")
                            for step_num, step in enumerate(recipe['steps'], 1):
                                st.markdown(f"{step_num}. {step}")
                            
                            st.markdown(f"💡 **ポイント:** {recipe['tips']}")
    else:
        st.info("📝 食材を登録すると、レシピを提案できます！")
 
# サイドバー
with st.sidebar:
    st.header("⚙️ 設定")
    
    st.divider()
    
    st.subheader("🔔 通知設定")
    
    if 'notification_enabled' not in st.session_state:
        st.session_state['notification_enabled'] = True
    
    notification_enabled = st.checkbox("通知を有効にする", value=st.session_state['notification_enabled'])
    st.session_state['notification_enabled'] = notification_enabled
    
    if 'notification_days' not in st.session_state:
        st.session_state['notification_days'] = 3
    
    notification_days = st.slider("何日前に通知するか", min_value=1, max_value=7, value=st.session_state['notification_days'])
    st.session_state['notification_days'] = notification_days