import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import json

# ページ設定
st.set_page_config(
    page_title="冷蔵庫管理＆献立支援アプリ",
    page_icon="🍽️",
    layout="wide"
)

# セッション状態の初期化
if 'fridge_items' not in st.session_state:
    st.session_state.fridge_items = []

if 'menu_items' not in st.session_state:
    st.session_state.menu_items = []

# ヘルパー関数
def check_expiring_soon(expiry_date, days=3):
    """賞味期限が近いかチェック"""
    today = date.today()
    diff = (expiry_date - today).days
    return 0 <= diff <= days

def check_expired(expiry_date):
    """賞味期限が切れているかチェック"""
    return expiry_date < date.today()

def get_missing_ingredients(menu_ingredients, fridge_items):
    """不足している食材を計算"""
    missing = []
    
    for ingredient in menu_ingredients:
        # 冷蔵庫から同じ名前と単位の食材を検索
        fridge_item = next((item for item in fridge_items 
                           if item['name'].lower() == ingredient['name'].lower() 
                           and item['unit'] == ingredient['unit']), None)
        
        if not fridge_item:
            # 全く在庫がない場合
            missing.append({
                'name': ingredient['name'],
                'needed': ingredient['quantity'],
                'unit': ingredient['unit']
            })
        elif fridge_item['quantity'] < ingredient['quantity']:
            # 在庫が不足している場合
            missing.append({
                'name': ingredient['name'],
                'needed': ingredient['quantity'] - fridge_item['quantity'],
                'unit': ingredient['unit']
            })
    
    return missing

def save_data():
    """データを保存（セッション状態）"""
    pass  # Streamlitのセッション状態を使用するため、特別な保存処理は不要

# メインアプリケーション
st.title("🍽️ 冷蔵庫管理＆献立支援アプリ")
st.markdown("食材管理から献立計画まで、お料理をスマートにサポート")

# サイドバーでタブ選択
tab = st.sidebar.radio(
    "機能を選択",
    ["🥬 冷蔵庫管理", "🍳 献立管理", "📊 統計情報"]
)

# 単位のリスト
units = ['個', 'g', 'ml', 'パック', '本', '枚', 'kg', 'L', 'カップ', '大さじ', '小さじ']

# 冷蔵庫管理タブ
if tab == "🥬 冷蔵庫管理":
    st.header("🥬 冷蔵庫管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("食材を追加")
        with st.form("add_item"):
            name = st.text_input("食材名", placeholder="例: トマト")
            
            col_qty, col_unit = st.columns(2)
            with col_qty:
                quantity = st.number_input("数量", min_value=0.1, step=0.1, format="%.1f")
            with col_unit:
                unit = st.selectbox("単位", units)
            
            expiry_date = st.date_input(
                "賞味期限", 
                value=date.today() + timedelta(days=7),
                min_value=date.today()
            )
            
            submit = st.form_submit_button("追加する", use_container_width=True)
            
            if submit and name:
                new_item = {
                    'id': len(st.session_state.fridge_items) + 1,
                    'name': name,
                    'quantity': quantity,
                    'unit': unit,
                    'expiry_date': expiry_date
                }
                st.session_state.fridge_items.append(new_item)
                st.success(f"{name}を追加しました！")
                st.rerun()
    
    with col2:
        st.subheader("冷蔵庫の中身")
        
        if not st.session_state.fridge_items:
            st.info("まだ食材が登録されていません")
        else:
            for i, item in enumerate(st.session_state.fridge_items):
                # 賞味期限の状態に応じて色を変更
                if check_expired(item['expiry_date']):
                    status = "🔴 期限切れ"
                    color = "red"
                elif check_expiring_soon(item['expiry_date']):
                    status = "🟡 期限間近"
                    color = "orange"
                else:
                    status = "🟢 新鮮"
                    color = "green"
                
                with st.container():
                    col_info, col_del = st.columns([4, 1])
                    
                    with col_info:
                        st.markdown(f"""
                        <div style="border-left: 4px solid {color}; padding-left: 10px; margin-bottom: 10px;">
                            <strong>{item['name']}</strong> ({item['quantity']}{item['unit']})<br>
                            <small>期限: {item['expiry_date']} | {status}</small>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_del:
                        if st.button("🗑️", key=f"del_{item['id']}", help="削除"):
                            st.session_state.fridge_items.remove(item)
                            st.rerun()

# 献立管理タブ
elif tab == "🍳 献立管理":
    st.header("🍳 献立管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("献立を作成")
        
        with st.form("add_menu"):
            menu_name = st.text_input("料理名", placeholder="例: カレーライス")
            
            st.write("**材料を追加**")
            
            # 材料入力のためのセッション状態
            if 'temp_ingredients' not in st.session_state:
                st.session_state.temp_ingredients = []
            
            col_ing_name, col_ing_qty, col_ing_unit = st.columns([2, 1, 1])
            
            with col_ing_name:
                ing_name = st.text_input("材料名", key="ing_name")
            with col_ing_qty:
                ing_quantity = st.number_input("数量", min_value=0.1, step=0.1, key="ing_qty", format="%.1f")
            with col_ing_unit:
                ing_unit = st.selectbox("単位", units, key="ing_unit")
            
            if st.form_submit_button("材料を追加"):
                if ing_name:
                    ingredient = {
                        'name': ing_name,
                        'quantity': ing_quantity,
                        'unit': ing_unit
                    }
                    st.session_state.temp_ingredients.append(ingredient)
                    st.rerun()
            
            # 追加した材料を表示
            if st.session_state.temp_ingredients:
                st.write("**追加した材料:**")
                for i, ing in enumerate(st.session_state.temp_ingredients):
                    col_ing_info, col_ing_del = st.columns([4, 1])
                    with col_ing_info:
                        st.write(f"• {ing['name']}: {ing['quantity']}{ing['unit']}")
                    with col_ing_del:
                        if st.button("❌", key=f"del_ing_{i}"):
                            st.session_state.temp_ingredients.pop(i)
                            st.rerun()
            
            if st.form_submit_button("献立を保存", use_container_width=True):
                if menu_name and st.session_state.temp_ingredients:
                    new_menu = {
                        'id': len(st.session_state.menu_items) + 1,
                        'name': menu_name,
                        'ingredients': st.session_state.temp_ingredients.copy()
                    }
                    st.session_state.menu_items.append(new_menu)
                    st.session_state.temp_ingredients = []
                    st.success(f"{menu_name}を保存しました！")
                    st.rerun()
    
    with col2:
        st.subheader("献立リストと買い物チェック")
        
        if not st.session_state.menu_items:
            st.info("まだ献立が登録されていません")
        else:
            for menu in st.session_state.menu_items:
                with st.expander(f"🍴 {menu['name']}", expanded=True):
                    # 材料リスト
                    st.write("**材料:**")
                    for ing in menu['ingredients']:
                        st.write(f"• {ing['name']}: {ing['quantity']}{ing['unit']}")
                    
                    # 不足食材チェック
                    missing = get_missing_ingredients(menu['ingredients'], st.session_state.fridge_items)
                    
                    if missing:
                        st.error("**🛒 買い物が必要な食材:**")
                        for item in missing:
                            st.write(f"• {item['name']}: {item['needed']}{item['unit']}")
                    else:
                        st.success("✅ すべての材料が冷蔵庫にあります！")
                    
                    # 削除ボタン
                    if st.button(f"献立を削除", key=f"del_menu_{menu['id']}"):
                        st.session_state.menu_items = [m for m in st.session_state.menu_items if m['id'] != menu['id']]
                        st.rerun()

# 統計情報タブ
elif tab == "📊 統計情報":
    st.header("📊 統計情報")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("冷蔵庫の状況")
        
        if st.session_state.fridge_items:
            total_items = len(st.session_state.fridge_items)
            expired_items = len([item for item in st.session_state.fridge_items if check_expired(item['expiry_date'])])
            expiring_soon = len([item for item in st.session_state.fridge_items if check_expiring_soon(item['expiry_date'])])
            fresh_items = total_items - expired_items - expiring_soon
            
            st.metric("総食材数", total_items)
            
            col_metrics = st.columns(3)
            with col_metrics[0]:
                st.metric("新鮮", fresh_items, delta=None)
            with col_metrics[1]:
                st.metric("期限間近", expiring_soon, delta=None)
            with col_metrics[2]:
                st.metric("期限切れ", expired_items, delta=None)
            
            # 賞味期限の近い食材を警告
            if expired_items > 0:
                st.error(f"⚠️ {expired_items}個の食材が期限切れです！")
            elif expiring_soon > 0:
                st.warning(f"⚠️ {expiring_soon}個の食材が期限間近です！")
        else:
            st.info("食材データがありません")
    
    with col2:
        st.subheader("献立の状況")
        
        if st.session_state.menu_items:
            total_menus = len(st.session_state.menu_items)
            can_make = 0
            
            for menu in st.session_state.menu_items:
                missing = get_missing_ingredients(menu['ingredients'], st.session_state.fridge_items)
                if not missing:
                    can_make += 1
            
            st.metric("登録済み献立", total_menus)
            st.metric("作れる献立", can_make)
            st.metric("買い物が必要", total_menus - can_make)
            
            if can_make == total_menus and total_menus > 0:
                st.success("🎉 すべての献立が作れます！")
            elif can_make > 0:
                st.info(f"✅ {can_make}個の献立が作れます")
        else:
            st.info("献立データがありません")

# フッター
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        💡 ヒント: 定期的に賞味期限をチェックして、食材の無駄を防ぎましょう！
    </div>
    """, 
    unsafe_allow_html=True
)

# データのエクスポート/インポート機能（オプション）
with st.sidebar:
    st.markdown("---")
    st.subheader("データ管理")
    
    if st.button("データをクリア", type="secondary"):
        if st.checkbox("本当にすべてのデータを削除しますか？"):
            st.session_state.fridge_items = []
            st.session_state.menu_items = []
            if 'temp_ingredients' in st.session_state:
                st.session_state.temp_ingredients = []
            st.success("データをクリアしました")
            st.rerun()
    
    # 簡単なデータエクスポート
    if st.session_state.fridge_items or st.session_state.menu_items:
        export_data = {
            'fridge_items': st.session_state.fridge_items,
            'menu_items': st.session_state.menu_items
        }
        
        # 日付をシリアライズ可能な形式に変換
        for item in export_data['fridge_items']:
            item['expiry_date'] = item['expiry_date'].isoformat()
        
        st.download_button(
            label="データをダウンロード",
            data=json.dumps(export_data, indent=2, ensure_ascii=False),
            file_name=f"fridge_data_{date.today()}.json",
            mime="application/json"
        )