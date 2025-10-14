def generate_recipe_suggestions(selected_items, recipe_type, items_df):
    """選択された食材からレシピを生成"""
    recipes = []
    
    # 食材の組み合わせに基づいてレシピを提案
    items_str = "、".join(selected_items)
    
    # 食材リストを生成する関数
    def make_ingredient_list(items):
        return [f"{item} 適量" for item in items]
    
    # レシピデータベース（簡易版）
    recipe_db = {
        "野菜炒め": {
            "keywords": ["野菜", "肉", "キャベツ", "ピーマン", "玉ねぎ", "にんじん"],
            "time": "15分",
            "servings": "2人分",
            "difficulty": "⭐ 簡単",
            "ingredients": make_ingredient_list(selected_items) + [
                "醤油 大さじ1",
                "酒 大さじ1",
                "塩こしょう 少々",
                "サラダ油 大さじ1"
            ],
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
            "ingredients": make_ingredient_list(selected_items) + [
                "水 800ml",
                "だしの素 小さじ2",
                "味噌 大さじ3"
            ],
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
            "ingredients": ["ご飯 2膳分"] + make_ingredient_list(selected_items) + [
                "醤油 大さじ1",
                "塩こしょう 少々",
                "ごま油 大さじ1"
            ],
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
            "ingredients": make_ingredient_list(selected_items) + [
                "カレールー 1/2箱",
                "水 600ml",
                "サラダ油 大さじ1"
            ],
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
            "ingredients": ["卵 3個"] + make_ingredient_list(selected_items) + [
                "塩こしょう 少々",
                "バター 10g",
                "牛乳 大さじ2"
            ],
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
            "ingredients": make_ingredient_list(selected_items) + [
                "醤油 大さじ1",
                "みりん 大さじ1",
                "サラダ油 大さじ1"
            ],
            "steps": [
                "材料を食べやすい大きさに切る",
                "フライパンに油を熱し、火が通りにくいものから順に炒める",
                "醤油とみりんで味付けする",
                "全体に味が馴染んだら完成"
            ],
            "tips": "余った食材を有効活用できる万能レシピです！"
        })
    
    return recipes[:3]  # 最大3つのレシピを返す