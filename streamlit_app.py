import streamlit as st
import pandas as pd
from datetime import date, timedelta

# --- アプリのタイトルと説明 ---
st.title('高齢者向け買い物支援アプリ 🛒')
st.markdown('冷蔵庫にある食品の賞味期限を管理し、買い物のタイミングを予測します。')
st.markdown('食品名と賞味期限を入力して、買い物のタイミングを把握しましょう。')

# --- データの初期化 ---
if 'food_data' not in st.session_state:
    st.session_state.food_data = pd.DataFrame(columns=['食品名', '賞味期限'])

# --- 食品情報の入力 ---
st.header('食品の追加 ➕')
with st.form(key='add_food_form'):
    food_name = st.text_input('食品名', key='food_name_input')
    expiry_date = st.date_input('賞味期限', min_value=date.today(), key='expiry_date_input')
    submit_button = st.form_submit_button(label='追加')

    if submit_button:
        if food_name:
            new_row = pd.DataFrame([{'食品名': food_name, '賞味期限': expiry_date}])
            st.session_state.food_data = pd.concat([st.session_state.food_data, new_row], ignore_index=True)
            st.success(f'{food_name} を追加しました！')
        else:
            st.warning('食品名を入力してください。')

# --- 登録された食品の一覧表示 ---
st.header('冷蔵庫の中身 🍎')
if not st.session_state.food_data.empty:
    st.dataframe(st.session_state.food_data.sort_values(by='賞味期限'))
else:
    st.info('まだ食品が登録されていません。')

# --- 買い物タイミングの予測 ---
st.header('買い物が必要な日 🛍️')
if not st.session_state.food_data.empty:
    # 賞味期限が最も近い食品を特定
    soonest_expiry = st.session_state.food_data['賞味期限'].min()

    # 賞味期限が近い食品をリストアップ
    expiring_soon_foods = st.session_state.food_data[st.session_state.food_data['賞味期限'] == soonest_expiry]

    # 今日の日付
    today = date.today()

    # 賞味期限までの残り日数を計算
    days_until_expiry = (soonest_expiry - today).days

    if days_until_expiry <= 3 and days_until_expiry >= 0:
        st.error(f'🚨 **急いで！** {expiring_soon_foods["食品名"].iloc[0]} の賞味期限が{soonest_expiry}に迫っています！')
        st.subheader('おすすめの買い物日: **今日**')
        st.markdown('買い物を済ませることをお勧めします。')
    elif days_until_expiry < 0:
        st.warning(f'⚠️ **注意！** {expiring_soon_foods["食品名"].iloc[0]} は賞味期限が切れています！')
        st.subheader('買い物が必要です。')
    else:
        # 買い物が必要な日を賞味期限の2日前に設定
        shopping_day = soonest_expiry - timedelta(days=2)
        st.info(f'次の買い物は **{shopping_day.strftime("%Y年%m月%d日")}** になるでしょう。')
        st.markdown(f'この日までに **{expiring_soon_foods["食品名"].iloc[0]}** がなくなる可能性があります。')
        st.markdown(f'賞味期限まで残り {days_until_expiry} 日です。')

else:
    st.info('食品を登録すると、買い物のタイミングが予測されます。')

# --- データの削除機能 (オプション) ---
st.header('食品の削除 🗑️')
if not st.session_state.food_data.empty:
    food_to_delete = st.selectbox('削除したい食品を選択', st.session_state.food_data['食品名'])
    if st.button('削除'):
        st.session_state.food_data = st.session_state.food_data[st.session_state.food_data['食品名'] != food_to_delete]
        st.success(f'{food_to_delete} を冷蔵庫から削除しました。')
        st.rerun() # 削除後、アプリを再読み込みして最新の状態を表示