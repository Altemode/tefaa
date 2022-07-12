import os
import streamlit as st
import pandas as pd

 
############## ############## PAGE 1 PREPARE THE FILE ############# ############# ############## ##############
    
st.set_page_config(
    page_title="Tefaa Metrics",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
   
)

st.sidebar.success("_From this section you can prepare your txt file with raw data!_")
st.sidebar.info("- Import the file in the form!")
st.sidebar.info("- Give the value of the platform mass.")
st.sidebar.info("- Choose your preffered time range area to cut!")
st.sidebar.info("- Finaly check the Verify box and export the file from the 'Export File' button!")

st.title('Prepare the file')



with st.expander("Show File Form", expanded=True):
    uploaded_file = st.file_uploader("Choose a file")
platform_mass = st.number_input("Give the platfrom mass:")
#@st.cache(allow_output_mutation=True)
def get_data():
    if uploaded_file:
        df_raw_data = pd.read_csv(uploaded_file, sep='\s+', skiprows=10, index_col = None)
        #Define Header columns
        columns_count = len(df_raw_data.axes[1])
        if columns_count == 6:
            df_raw_data.columns = ['Time', 'Col_2', 'Mass_1', 'Mass_2', 'Mass_3', 'Mass_4']
        if columns_count == 8:
            df_raw_data.columns = ['Time', 'Col_2', 'Mass_1', 'Mass_2', 'Mass_3', 'Mass_4', 'Col_7', 'Col_8']
        if columns_count == 9:
            df_raw_data.columns = ['Time', 'Col_2', 'Mass_1', 'Mass_2', 'Mass_3', 'Mass_4', 'Col_7', 'Col_8', 'Col_9']
        if columns_count == 10:
            df_raw_data.columns = ['Time', 'Col_2', 'Mass_1', 'Mass_2', 'Mass_3', 'Mass_4', 'Col_7', 'Col_8', 'Col_9', 'Col_10']
        if columns_count == 11:
            df_raw_data.columns = ['Time', 'Col_2', 'Mass_1', 'Mass_2', 'Mass_3', 'Mass_4', 'Col_7', 'Col_8', 'Col_9', 'Col_10','Col_11']
        C = 406.831
        #sr = 1000
        resolution = 16
        # Calculate for A Sensor Mass $ Weight
        Vfs_1 = 2.00016
        df_raw_data['Mass_1'] = df_raw_data['Mass_1'] * C / (Vfs_1 * ( (2**resolution) - 1 ) )
        # Calculate for B Sensor Mass $ Weight
        Vfs_2 = 2.00002
        df_raw_data['Mass_2'] = df_raw_data['Mass_2'] * C / (Vfs_2 * ( (2**resolution) - 1 ) )
        # Calculate for C Sensor Mass $ Weight
        Vfs_3 = 2.00057
        df_raw_data['Mass_3'] = df_raw_data['Mass_3'] * C / (Vfs_3 * ( (2**resolution) - 1 ) )
        # Calculate for D Sensor Mass $ Weight
        Vfs_4 = 2.00024
        df_raw_data['Mass_4'] = df_raw_data['Mass_4'] * C / (Vfs_4 * ( (2**resolution) - 1 ) )
        # Calculate the sum of all sensors Mass $ Weight
        df_raw_data['Mass_Sum'] = (df_raw_data['Mass_1'] + df_raw_data['Mass_2'] + df_raw_data['Mass_3'] + df_raw_data['Mass_4']) - platform_mass
        df_raw_data['Rows_Count'] = df_raw_data.index
        return df_raw_data

if uploaded_file:
    
    df_raw_data= get_data()
    
    # if st.button('Reload Dataframe with Raw Data'):
    #     get_data()
    if df_raw_data is not None:
        min_time = int(df_raw_data.index.min())
        max_time = int(df_raw_data.index.max())
        selected_time_range = st.slider('Select the whole time range of the graph, per 100', min_time, max_time, (min_time, max_time), 1)
        selected_area = (df_raw_data.Rows_Count.between(selected_time_range[0], selected_time_range[1]) )
        df_prepared = pd.DataFrame(df_raw_data[selected_area])
        
        st.line_chart(df_prepared['Mass_Sum'])
        # To Drop the unnecessary Columns
        df_prepared.drop(['Rows_Count'], axis = 1, inplace=True)
        filename = uploaded_file.name
        # To Get only the filename without extension (.txt)
        final_filename = os.path.splitext(filename)[0]
        st.write("The file name of your file is : ", final_filename)
        show_df_prepared = st.checkbox("Display the final dataframe")
        if show_df_prepared:
            st.dataframe(df_prepared)
        # if platform_mass >1:
        #     st.download_button(
        #         label="Export File",
        #         data=df_prepared.to_csv(index=False),
        #         file_name=final_filename +'.csv',
        #         mime='text/csv',
        #     )


        export = st.checkbox('Verify you have insert proper Platform Mass Value:')

        if export:
            if 4.5 <= platform_mass <= 7.5:
                st.success("You are able to export your data.")
                st.download_button(
                    label="Export File",
                    data=df_prepared.to_csv(index=False),
                    file_name=final_filename +'.csv',
                    mime='text/csv',
                )
            else:
                st.warning("Please give correct platform mass!")
