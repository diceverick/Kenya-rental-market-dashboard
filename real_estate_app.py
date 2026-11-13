import streamlit as st
import pandas as pd

# UI Setup
st.set_page_config(page_title="Nairobi Real Estate Market", layout="wide", initial_sidebar_state="expanded")

# The Mercedes Brutalist Dark Mode Injection
st.markdown("""
<style>
    .stApp { background-color: #000000 !important; color: #FFFFFF !important; }
    header { background-color: transparent !important; }
    [data-testid="stSidebar"] { border-right: 1px solid #333333 !important; }
    h1, h2, h3, p, label { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important; }
    h1 { font-weight: 400 !important; border-bottom: 1px solid #333333; padding-bottom: 20px; margin-bottom: 30px; }
    div[data-baseweb="select"] > div, .stSlider > div, div[data-testid="stAlert"] {
        background-color: #0A0A0A !important;
        border: 1px solid #333333 !important;
        border-radius: 0px !important;
    }
    div[data-baseweb="select"] > div:hover { border-color: #FFFFFF !important; }
    [data-testid="stDataFrame"] > div {
        background-color: transparent !important;
        border: none !important;
        border-radius: 0px !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("KNBS Market Intelligence: Real Estate 🏢")

# 1. Load the Excel file and clean outliers
@st.cache_data
def load_data():
    # Make sure this matches your actual Excel file name
    df = pd.read_excel('buyrent_rentals_data.xlsx')
    
    # Drop rows with missing prices or bedrooms
    df = df.dropna(subset=['Price (KSh)', 'Bedrooms', 'City', 'Neighborhood'])
    
    # Ensure prices and bedrooms are numbers
    df['Price (KSh)'] = pd.to_numeric(df['Price (KSh)'], errors='coerce')
    df['Bedrooms'] = pd.to_numeric(df['Bedrooms'], errors='coerce')
    
    # Filter out insane outliers (like the 5.5M rent in Kitisuru on row 9)
    df = df[df['Price (KSh)'] < 1000000]
    
    return df

df = load_data()

# 2. Sidebar Filters
st.sidebar.header("Market Filters")

# Get unique cities (e.g. Westlands, Nairobi, Ruiru) and neighborhoods
all_cities = sorted(df['City'].unique().tolist())
all_neighborhoods = sorted(df['Neighborhood'].unique().tolist())

# Select City first
selected_city = st.sidebar.multiselect("Select Region (City)", all_cities, default=["Westlands"])

# Filter the available neighborhoods based on the chosen city
city_filtered_df = df[df['City'].isin(selected_city)]
available_neighborhoods = sorted(city_filtered_df['Neighborhood'].unique().tolist())

selected_neighborhoods = st.sidebar.multiselect(
    "Select Neighborhood", 
    available_neighborhoods, 
    default=available_neighborhoods[:3] if len(available_neighborhoods) > 0 else None
)

# Slider for bedrooms
max_beds = int(df['Bedrooms'].max())
selected_beds = st.sidebar.slider("Number of Bedrooms", 1, max_beds, 2)

# 3. Filter the pandas dataframe based on user choice
filtered_db = city_filtered_df[
    (city_filtered_df['Neighborhood'].isin(selected_neighborhoods)) & 
    (city_filtered_df['Bedrooms'] == selected_beds)
]

# 4. Calculate the average price and build the UI
if not filtered_db.empty:
    avg_price = filtered_db['Price (KSh)'].mean()
    
    # Display the big KPI number
    st.metric(label=f"Average {selected_beds}-Bedroom Rent in Selected Areas", value=f"KSh {avg_price:,.0f}")
    
    st.divider()
    
    # Show a bar chart comparing the areas
    st.subheader(f"Average {selected_beds}-Bedroom Rent by Neighborhood")
    
    # Group by Neighborhood and get the average price
    chart_data = filtered_db.groupby('Neighborhood')['Price (KSh)'].mean().reset_index()
    
    # Set the Neighborhood as the index so Streamlit charts it properly
    st.bar_chart(chart_data.set_index('Neighborhood'))
    
    st.divider()
    
    # Show the raw data table
    st.subheader("Raw Database")
    
    st.dataframe(
        filtered_db, 
        width='stretch', 
        hide_index=True,
        column_config={
            "Price (KSh)": st.column_config.NumberColumn("Price (KSh)", format="KSh %d"),
            "Size (sq ft)": st.column_config.NumberColumn("Size (sq ft)", format="%d sq ft")
        }
    )
else:
    st.warning("No apartments found for this specific filter combination.")