"""
Weather Pipeline Dashboard
Streamlit app that visualizes weather forecast data from the SQLite database.

Run: streamlit run dashboard.py
"""
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

# -- Page config ---------------------------------------------------------------
st.set_page_config(
    page_title="Weather Pipeline Dashboard",
    page_icon="🌤",
    layout="wide",
)

# -- Constants -----------------------------------------------------------------
DB_PATH = Path("data/weather.db")

# WMO Weather interpretation codes
WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog",
    51: "Light drizzle", 53: "Mod. drizzle", 55: "Dense drizzle",
    56: "Freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Mod. rain", 65: "Heavy rain",
    66: "Freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Mod. snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight showers", 81: "Mod. showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm w/ hail", 99: "Thunderstorm w/ heavy hail",
}

# -- Data loading --------------------------------------------------------------
@st.cache_data(ttl=300)
def load_data(db_path: str) -> pd.DataFrame:
    """Load all weather data from SQLite."""
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql("SELECT * FROM weather_forecast", conn)
        conn.close()
        df["time"] = pd.to_datetime(df["time"])
        df["date"] = pd.to_datetime(df["date"])
        df["weather_label"] = df["weathercode"].map(WMO_CODES).fillna("Unknown")
        return df
    except Exception as e:
        return pd.DataFrame()


# -- Header --------------------------------------------------------------------
st.title("Weather Pipeline Dashboard")
st.caption("7-day hourly forecast data from [Open-Meteo API](https://open-meteo.com) — powered by an idempotent ETL pipeline")

# -- Load data -----------------------------------------------------------------
if not DB_PATH.exists():
    st.warning(
        "No database found at `data/weather.db`. "
        "Run the pipeline first: `python main.py`"
    )
    st.stop()

df = load_data(str(DB_PATH))

if df.empty:
    st.warning("Database exists but contains no data. Run `python main.py` to fetch forecasts.")
    st.stop()

# -- City selector -------------------------------------------------------------
cities = sorted(df["city"].unique().tolist())
selected_city = st.selectbox("Select City", cities, index=0)
city_df = df[df["city"] == selected_city].sort_values("time").reset_index(drop=True)

# -- KPI cards -----------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    latest_temp = city_df["temperature_2m"].iloc[-1]
    st.metric("Latest Temperature", f"{latest_temp:.1f} °C")

with col2:
    avg_humidity = city_df["relative_humidity_2m"].mean()
    st.metric("Avg Humidity", f"{avg_humidity:.1f}%")

with col3:
    max_wind = city_df["windspeed_10m"].max()
    st.metric("Max Wind Speed", f"{max_wind:.1f} km/h")

with col4:
    total_rows = len(city_df)
    date_range = f"{city_df['date'].min().strftime('%b %d')} — {city_df['date'].max().strftime('%b %d')}"
    st.metric("Data Points", f"{total_rows}", help=date_range)

st.divider()

# -- Temperature trend (hourly) ------------------------------------------------
st.subheader("Temperature Trend (Hourly)")
fig_temp = px.line(
    city_df,
    x="time", y="temperature_2m",
    labels={"time": "Time", "temperature_2m": "Temperature (°C)"},
    line_shape="spline",
)
fig_temp.update_layout(height=350, margin=dict(l=20, r=20, t=10, b=20))
st.plotly_chart(fig_temp, use_container_width=True)

# -- Humidity (daily average) --------------------------------------------------
st.subheader("Average Humidity by Day")
daily_humidity = city_df.groupby("date")["relative_humidity_2m"].mean().reset_index()
fig_hum = px.bar(
    daily_humidity,
    x="date", y="relative_humidity_2m",
    labels={"date": "Date", "relative_humidity_2m": "Avg Humidity (%)"},
)
fig_hum.update_layout(height=300, margin=dict(l=20, r=20, t=10, b=20))
st.plotly_chart(fig_hum, use_container_width=True)

# -- Wind speed + Weather code (side by side) ----------------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Wind Speed Over Time")
    fig_wind = px.scatter(
        city_df,
        x="time", y="windspeed_10m",
        labels={"time": "Time", "windspeed_10m": "Wind Speed (km/h)"},
        opacity=0.7,
    )
    fig_wind.update_layout(height=320, margin=dict(l=20, r=20, t=10, b=20))
    st.plotly_chart(fig_wind, use_container_width=True)

with col_right:
    st.subheader("Weather Conditions")
    weather_counts = city_df["weather_label"].value_counts().reset_index()
    weather_counts.columns = ["Condition", "Count"]
    fig_pie = px.pie(
        weather_counts,
        names="Condition", values="Count",
        hole=0.4,
    )
    fig_pie.update_layout(height=320, margin=dict(l=20, r=20, t=10, b=20))
    st.plotly_chart(fig_pie, use_container_width=True)

# -- Precipitation probability ------------------------------------------------
st.subheader("Precipitation Probability (Hourly)")
fig_precip = go.Figure()
fig_precip.add_trace(go.Scatter(
    x=city_df["time"],
    y=city_df["precipitation_probability"],
    fill="tozeroy",
    name="Precipitation %",
    line=dict(color="#636EFA", width=1),
    fillcolor="rgba(99,110,250,0.15)",
))
fig_precip.update_layout(
    height=280,
    margin=dict(l=20, r=20, t=10, b=20),
    xaxis_title="Time",
    yaxis_title="Probability (%)",
    yaxis_range=[0, 100],
)
st.plotly_chart(fig_precip, use_container_width=True)

# -- Raw data table ------------------------------------------------------------
with st.expander("View Raw Data"):
    st.dataframe(
        city_df.drop(columns=["weather_label"]),
        use_container_width=True,
        height=400,
    )

# -- Footer --------------------------------------------------------------------
st.divider()
st.caption(
    f"Data source: Open-Meteo API | City: {selected_city} | "
    f"{len(city_df)} hourly records | "
    f"Last updated: {city_df['time'].max().strftime('%Y-%m-%d %H:%M')}"
)
