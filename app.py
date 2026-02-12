import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from datetime import date, timedelta

st.set_page_config(page_title="Deepak Life OS", layout="centered")

# ---------------- PASSWORD ----------------
if "APP_PASSWORD" not in st.secrets:
    st.error("APP_PASSWORD not set in secrets.")
    st.stop()

password = st.text_input("Enter Password", type="password")

if password != st.secrets["APP_PASSWORD"]:
    st.stop()

st.title("🔥 Deepak Life Operating System")

# ---------------- DATABASE ----------------
if "DATABASE_URL" not in st.secrets:
    st.error("DATABASE_URL not set in secrets.")
    st.stop()

DATABASE_URL = st.secrets["DATABASE_URL"]

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"sslmode": "require"}
    )

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

except Exception as e:
    st.error("Database Connection Failed ❌")
    st.write(str(e))
    st.stop()

# ---------------- TABS ----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["🥗 Nutrition", "📋 Tasks", "🔥 Habits", "💪 Body", "📊 Weekly"]
)

# =================================================
# 🥗 NUTRITION
# =================================================
with tab1:
    food_db = pd.read_csv("deepak_master_food_database.csv")

    mode = st.selectbox("Goal Mode", ["Bulk", "Cut"])

    CAL_TARGET = 3000 if mode == "Bulk" else 2400
    PROTEIN_TARGET = 170 if mode == "Bulk" else 160

    with st.form("food_form"):
        entry_date = st.date_input("Date", date.today())
        meal = st.selectbox("Meal", ["Breakfast", "Lunch", "Dinner", "Snacks"])
        selected_food = st.selectbox("Food", food_db["Food"])
        quantity = st.number_input("Quantity (grams)", 0.0, 1000.0, step=10.0)
        submit = st.form_submit_button("Add Food")

        if submit and quantity > 0:
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
        today = pd.to_datetime(date.today())
        today_data = food_log[food_log["date"] == today]

        total_cal = today_data["calories"].sum()
        total_protein = today_data["protein"].sum()

        st.metric("Calories", round(total_cal))
        st.progress(min(total_cal/CAL_TARGET, 1.0))

        st.metric("Protein", round(total_protein))
        st.progress(min(total_protein/PROTEIN_TARGET, 1.0))

# =================================================
# 📋 TASKS
# =================================================
with tab2:
    with st.form("task_form"):
        task_text = st.text_input("New Task")
        add_task = st.form_submit_button("Add Task")

        if add_task and task_text:
            pd.DataFrame([{
                "date": date.today(),
                "task": task_text,
                "completed": False
            }]).to_sql("task_log", engine, if_exists="append", index=False)

    tasks = pd.read_sql("SELECT * FROM task_log", engine)
    tasks["date"] = pd.to_datetime(tasks["date"])

    today_tasks = tasks[tasks["date"] == pd.to_datetime(date.today())]

    completed = 0

    for _, row in today_tasks.iterrows():
        checked = st.checkbox(row["task"], value=row["completed"], key=row["id"])

        if checked != row["completed"]:
            with engine.connect() as conn:
                conn.execute(
                    text("UPDATE task_log SET completed=:c WHERE id=:i"),
                    {"c": checked, "i": row["id"]}
                )
                conn.commit()

        if checked:
            completed += 1

    total = len(today_tasks)
    rate = completed/total if total > 0 else 0
    st.progress(rate)
    st.write(f"{round(rate*100)}% Completed")

# =================================================
# 🔥 HABITS
# =================================================
with tab3:
    with st.form("habit_form"):
        water = st.number_input("Water (Liters)", 0.0, 10.0)
        reading = st.number_input("Reading (minutes)", 0)
        coding = st.number_input("Coding (minutes)", 0)
        submit = st.form_submit_button("Save Habits")

        if submit:
            pd.DataFrame([{
                "date": date.today(),
                "water_liters": water,
                "reading_minutes": reading,
                "coding_minutes": coding
            }]).to_sql("habit_log", engine, if_exists="append", index=False)
            st.success("Habits Saved ✅")

# =================================================
# 💪 BODY
# =================================================
with tab4:
    with st.form("body_form"):
        weight = st.number_input("Weight (kg)", 40.0, 150.0)
        submit = st.form_submit_button("Save Weight")

        if submit:
            pd.DataFrame([{
                "date": date.today(),
                "weight": weight
            }]).to_sql("body_metrics", engine, if_exists="append", index=False)

    body_data = pd.read_sql("SELECT * FROM body_metrics", engine)

    if not body_data.empty:
        body_data["date"] = pd.to_datetime(body_data["date"])
        fig = px.line(body_data, x="date", y="weight", markers=True)
        st.plotly_chart(fig, use_container_width=True)

# =================================================
# 📊 WEEKLY
# =================================================
with tab5:
    food_log = pd.read_sql("SELECT * FROM food_log", engine)

    if not food_log.empty:
        food_log["date"] = pd.to_datetime(food_log["date"])
        weekly = food_log.groupby(
            food_log["date"].dt.isocalendar().week
        )["calories"].sum()

        st.line_chart(weekly)


