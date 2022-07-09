import streamlit as st

st.set_page_config(
    page_title="Tefaa Metrics",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)
st.subheader('School of Physical Education and Sports Science')
st.markdown("# Main page")
st.sidebar.markdown("# Main page ")

st.write("# Welcome to SPES Data Analysis Project!")

st.sidebar.success("Select a app above.")

st.markdown(
    "Navigate to left sidebar menu to choose your desire section!"
)


st.markdown(
    "Prepare your file: You can edit and prepare your file ready for calculation!"
)

st.markdown(
    "Insert new entry: Add a new entry into database system!"
)

st.markdown(
    "Calculate results: For each entry make awesome calculations!"
)
