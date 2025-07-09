
import streamlit as st
import pandas as pd
import json

# セッション初期化
if "tentative_type" not in st.session_state:
    st.session_state["tentative_type"] = None
if "final_type" not in st.session_state:
    st.session_state["final_type"] = None

st.title("鍼灸 弁証診断フォーム（基礎情報付き）")

# 基礎情報入力
with st.form("user_info"):
    st.subheader("基礎情報入力")
    age = st.number_input("年齢", min_value=0, max_value=120, value=30)
    sex = st.selectbox("性別", ["男性", "女性", "その他"])
    height = st.number_input("身長（cm）", min_value=100, max_value=250, value=165)
    weight = st.number_input("体重（kg）", min_value=30, max_value=150, value=60)
    submitted_info = st.form_submit_button("情報を送信")

if submitted_info:
    st.session_state["age"] = age
    st.session_state["sex"] = sex
    st.session_state["height"] = height
    st.session_state["weight"] = weight

# ユーザー情報確認
if "age" in st.session_state:
    st.markdown(f"**年齢:** {st.session_state['age']}歳")
    st.markdown(f"**性別:** {st.session_state['sex']}")
    st.markdown(f"**身長:** {st.session_state['height']} cm")
    st.markdown(f"**体重:** {st.session_state['weight']} kg")

    bmi = st.session_state["weight"] / ((st.session_state["height"] / 100) ** 2)
    st.markdown(f"**BMI:** {bmi:.1f}")

# --- Step 1: 一次質問 ---
st.subheader("ステップ1: 質問票")

try:
    questions_df = pd.read_csv("questions.csv", encoding="utf-8-sig")
except FileNotFoundError:
    st.error("questions.csv が見つかりません。正しいパスに配置してください。")
    st.stop()

scores = {}
for _, row in questions_df.iterrows():
    q, b = row["質問"], row["弁証"]
    answer = st.radio(q, ["はい", "いいえ"], key=q)
    if answer == "はい":
        scores[b] = scores.get(b, 0) + 1

if st.button("弁証を仮判定"):
    if not scores:
        st.warning("少なくとも1つは「はい」にしてください")
        st.stop()

    max_score = max(scores.values())
    primary_candidates = [k for k, v in scores.items() if v == max_score]
    tentative_type = primary_candidates[0]

    st.session_state["tentative_type"] = tentative_type
    st.success(f"仮の弁証タイプ: {tentative_type}")

# --- Step 2: 深掘り質問 ---
if st.session_state["tentative_type"]:
    st.subheader("ステップ2: 深掘り質問")

    try:
        deep_df = pd.read_csv("deep_questions.csv", encoding="utf-8-sig")
    except FileNotFoundError:
        st.error("deep_questions.csv が見つかりません。")
        st.stop()

    deep_scores = {}
    for _, row in deep_df.iterrows():
        dq = row["質問"]
        db = row["弁証"]
        ans = st.radio(dq, ["はい", "いいえ"], key=f"deep_{dq}")
        if ans == "はい":
            deep_scores[db] = deep_scores.get(db, 0) + 1

    if st.button("最終弁証を決定"):
        max_deep_score = max(deep_scores.values()) if deep_scores else 0
        final_candidates = [k for k, v in deep_scores.items() if v == max_deep_score]
        st.session_state["final_type"] = final_candidates[0] if final_candidates else st.session_state["tentative_type"]

# --- Step 3: 結果表示 ---
if st.session_state["final_type"]:
    st.subheader("ステップ3: 診断結果")

    final_type = st.session_state["final_type"]
    st.markdown(f"### 最終弁証: {final_type}")

    try:
        with open("prescriptions.json", "r", encoding="utf-8-sig") as f:
            prescriptions = json.load(f)
    except FileNotFoundError:
        st.error("prescriptions.json が見つかりません。")
        st.stop()

    if final_type in prescriptions:
        ekketsu = prescriptions[final_type].get("経穴", [])
        shido = prescriptions[final_type].get("生活指導", "")
        st.markdown("#### 推奨経穴:")
        st.write(", ".join(ekketsu))
        st.markdown("#### 生活指導:")
        st.info(shido)
    else:
        st.warning("該当する処方がありません。")
