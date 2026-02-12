import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from datetime import date, timedelta

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
st.set_page_config(page_title="Deepak Life OS", layout="centered")

# ---------------- PASSWORD PROTECTION -------------
password = st.text_input("Enter Password", type="password")
if password != st.secrets["APP_PASSWORD"]:
    st.stop()

st.title("🔥 Deepak Life Operating System")

# ---------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------
DATABASE_URL = st.secrets["DATABASE_URL"]
engine = create_engine(DATABASE_URL)

# ---------------------------------------------------
# TABS
# ---------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🥗 Nutrition",
    "📋 Tasks",
    "🔥 Habits",
    "💪 Body Metrics",
    "📊 Weekly Analytics"
])

# ===================================================
# 🥗 NUTRITION TAB
# ===================================================
with tab1:

    food_db = pd.read_csv("deepak_master_food_database.csv")

    mode = st.selectbox("Goal Mode", ["Bulk","Cut"])

    if mode == "Bulk":
        CAL_TARGET = 3000
        PROTEIN_TARGET = 170
    else:
        CAL_TARGET = 2400
        PROTEIN_TARGET = 160

    with st.form("food_form"):
        entry_date = st.date_input("Date", date.today())
        meal = st.selectbox("Meal", ["Breakfast","Lunch","Dinner","Snacks"])
        selected_food = st.selectbox("Food", food_db["Food"])
        quantity = st.number_input("Quantity (grams)", 0.0, 1000.0, step=10.0)
        submit = st.form_submit_button("Add Food")

        if submit:
            food_info = food_db[food_db["Food"] == selected_food].iloc[0]

            new_row = pd.DataFrame([{
                "date": entry_date,
                "meal": meal,
                "food": selected_food,
                "quantity": quantity,
                "calories": (quantity/100) * food_info["Calories"],
                "protein": (quantity/100) * food_info["Protein"],
                "carbs": (quantity/100) * food_info["Carbs"],
                "fats": (quantity/100) * food_info["Fats"]
            }])

            new_row.to_sql("food_log", engine, if_exists="append", index=False)
            st.success("Food Saved ✅")

    food_log = pd.read_sql("SELECT * FROM food_log", engine)

    if not food_log.empty:
        food_log["date"] = pd.to_datetime(food_log["date"])
        daily = food_log.groupby("date").sum(numeric_only=True).reset_index()

        today = pd.to_datetime(date.today())
        today_data = daily[daily["date"] == today]

        if not today_data.empty:
            today_cal = today_data["calories"].values[0]
            today_protein = today_data["protein"].values[0]
        else:
            today_cal = today_protein = 0

        st.metric("Calories", round(today_cal), delta=round(today_cal-CAL_TARGET))
        st.progress(min(today_cal/CAL_TARGET,1.0))

        st.metric("Protein", round(today_protein), delta=round(today_protein-PROTEIN_TARGET))
        st.progress(min(today_protein/PROTEIN_TARGET,1.0))

# ===================================================
# 📋 TASK TAB
# ===================================================
with tab2:

    with st.form("task_form"):
        task_text = st.text_input("New Task")
        add_task = st.form_submit_button("Add Task")

        if add_task and task_text:
            new_task = pd.DataFrame([{
                "date": date.today(),
                "task": task_text,
                "completed": False
            }])
            new_task.to_sql("task_log", engine, if_exists="append", index=False)
            st.success("Task Added")

    tasks = pd.read_sql("SELECT * FROM task_log", engine)
    tasks["date"] = pd.to_datetime(tasks["date"])

    today_tasks = tasks[tasks["date"] == pd.to_datetime(date.today())]

    completed_count = 0

    for i, row in today_tasks.iterrows():
        checked = st.checkbox(row["task"], value=row["completed"], key=row["id"])

        if checked != row["completed"]:
            with engine.connect() as conn:
                conn.execute(text(
                    f"UPDATE task_log SET completed = {checked} WHERE id = {row['id']}"
                ))
                conn.commit()

        if checked:
            completed_count += 1

    total = len(today_tasks)
    completion_rate = completed_count/total if total > 0 else 0

    st.progress(completion_rate)
    st.write(f"{round(completion_rate*100)}% Completed")

    # -------- STREAK --------
    streak = 0
    check_date = date.today()

    while True:
        day_tasks = tasks[tasks["date"] == pd.to_datetime(check_date)]

        if day_tasks.empty:
            break

        if day_tasks["completed"].all():
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    st.metric("🔥 Current Streak (Days)", streak)

# ===================================================
# 🔥 HABITS TAB
# ===================================================
with tab3:

    with st.form("habit_form"):
        water = st.number_input("Water (Liters)", 0.0, 10.0, step=0.1)
        reading = st.number_input("Reading (minutes)", 0)
        coding = st.number_input("Coding (minutes)", 0)
        submit = st.form_submit_button("Save Habits")

        if submit:
            new_row = pd.DataFrame([{
                "date": date.today(),
                "water_liters": water,
                "reading_minutes": reading,
                "coding_minutes": coding
            }])
            new_row.to_sql("habit_log", engine, if_exists="append", index=False)
            st.success("Habits Saved ✅")

# ===================================================
# 💪 BODY METRICS TAB
# ===================================================
with tab4:

    with st.form("body_form"):
        weight = st.number_input("Weight (kg)", 40.0, 150.0, step=0.1)
        body_fat = st.number_input("Body Fat %", 0.0, 50.0, step=0.1)
        waist = st.number_input("Waist (cm)", 0.0, 150.0, step=0.5)
        chest = st.number_input("Chest (cm)", 0.0, 150.0, step=0.5)
        arms = st.number_input("Arms (cm)", 0.0, 100.0, step=0.5)
        submit = st.form_submit_button("Save Metrics")

        if submit:
            new_row = pd.DataFrame([{
                "date": date.today(),
                "weight": weight,
                "body_fat": body_fat,
                "waist": waist,
                "chest": chest,
                "arms": arms
            }])
            new_row.to_sql("body_metrics", engine, if_exists="append", index=False)
            st.success("Metrics Saved ✅")

    body_data = pd.read_sql("SELECT * FROM body_metrics", engine)

    if not body_data.empty:
        body_data["date"] = pd.to_datetime(body_data["date"])
        fig = px.line(body_data, x="date", y="weight", markers=True)
        st.plotly_chart(fig, use_container_width=True)

# ===================================================
# 📊 WEEKLY ANALYTICS TAB
# ===================================================
with tab5:

    food_log = pd.read_sql("SELECT * FROM food_log", engine)
    habit_log = pd.read_sql("SELECT * FROM habit_log", engine)

    if not food_log.empty:
        food_log["date"] = pd.to_datetime(food_log["date"])
        weekly_cal = food_log.groupby(
            food_log["date"].dt.isocalendar().week
        )["calories"].sum()

        st.subheader("Weekly Calories")
        st.line_chart(weekly_cal)

    if not habit_log.empty:
        habit_log["date"] = pd.to_datetime(habit_log["date"])
        weekly_coding = habit_log.groupby(
            habit_log["date"].dt.isocalendar().week
        )["coding_minutes"].sum()

        st.subheader("Weekly Coding Minutes")
        st.line_chart(weekly_coding)

