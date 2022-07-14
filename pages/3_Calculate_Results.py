import os
import streamlit as st
import pandas as pd
import numpy as np
from supabase import create_client, Client
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode
import altair as alt
import biosignalsnotebooks as bsnb
import plotly.graph_objects as go

import sympy as sy

############## ############## PAGE 3 CALCULATE RESULTS ############# ############# ############## ########################
st.set_page_config(
    page_title="Tefaa Metrics",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)

#Make the connection with Supabase - Database:
@st.experimental_singleton
def init_connection():
    url = st.secrets["supabase_url"]
    key = st.secrets["supabase_key"]
    #client = create_client(url, key)
    return create_client(url, key)
con = init_connection()

st.title("Calculate Results")
# st.sidebar.info("""Some Usefull Tips:  
# • initial stationary position (FGRF = BW)  
# • unweighting phase (FGRF < BW)  
# • propulsion phase (FGRF > BW)  
# • instant of take-off (FGRF = 0 N)  
# • flight phase (FGRF = 0 N)  
# • instant of landing  
# • the landing ‘impact’ force peak  
# • final stationary position (FGRF = BW)""")

url_list=[]
with st.expander("From here you may display and calculate results from any entry of the database!", expanded=True):
    st.caption("Use the below search fields to filter the datatable!")
    #uploaded_file = st.file_uploader("Choose a file1")
    #@st.experimental_memo(ttl=600)
    def select_all_from_main_table():
        query=con.table("main_table").select("*").execute()
        return query
    query = select_all_from_main_table()


    df_main_table = pd.DataFrame(query.data)
    if not df_main_table.empty:
        df_main_table.columns = ['ID', 'Created At', 'Fullname', 'Email', 'Occupy', 'Type of Trial', 'Filename', 'Filepath', 'Height', 'Weight', 'Age']
        col1, col2, col3, col4, col5 = st.columns(5)
        with col3:
            type_of_trial_search = st.text_input("Type of Trial:")

        with col5:
            st.write("")

        with col4:
            st.write("")
        
        with col2:
            occupy_search = st.text_input("Occupy:")
            
        with col1:
            fullname_search = st.text_input("Fullname:")
            

        if not occupy_search and not fullname_search:
            df_main_table
        
        elif fullname_search and not occupy_search and not type_of_trial_search:
            st.dataframe(df_main_table[df_main_table['Fullname']== fullname_search])

        elif occupy_search and not fullname_search and not type_of_trial_search:
            st.dataframe(df_main_table[df_main_table['Occupy']== occupy_search])

        elif type_of_trial_search and not fullname_search and not occupy_search:
            st.dataframe(df_main_table[df_main_table['Type of Trial']== type_of_trial_search])

        elif fullname_search and occupy_search and not type_of_trial_search:
            df_main_table[(df_main_table['Fullname'] == fullname_search) & (df_main_table['Occupy'] == occupy_search)]

        elif fullname_search and type_of_trial_search and not occupy_search:
            df_main_table[(df_main_table['Fullname'] == fullname_search) & (df_main_table['Type of Trial'] == type_of_trial_search)]
        
        elif occupy_search and type_of_trial_search:
            df_main_table[(df_main_table['Occupy'] == occupy_search) & (df_main_table['Type of Trial'] == type_of_trial_search)]
        
        elif fullname_search and occupy_search and type_of_trial_search:
            df_main_table[(df_main_table['Occupy'] == occupy_search) & (df_main_table['Fullname'] == fullname_search) & (df_main_table['Type of Trial'] == type_of_trial_search)]

        #url_id_number_input = st.number_input("Type the ID of the person you want to calculate results of the current trial.",value=0,step=1)


        # In this form, you type the id of the person to calculate speicific trial.
        
        with st.form("Type the ID of your link:",clear_on_submit=False):   
                url_id_number_input = st.number_input("Type the ID of your prerferred trial and Press Calculate Results:",value = 0,step= 1)
                id_submitted = st.form_submit_button("Calculate Results")
        # Querry to find the data row of specific ID
        if url_id_number_input:
            def select_filepath_from_specific_id():
                query=con.table("main_table").select("*").eq("id", url_id_number_input).execute()
                return query
            query = select_filepath_from_specific_id()  
            # Make a list with all values from database depending on the condition. 
            url_list =  query.data
            # List with values depending on the querry
            if url_list:
                url = url_list[0]['filepath'].replace(" ", "%20")
                st.write(url_list[0]['filepath'].replace(" ", "%20"))
            else:
                st.write("There is no entry with this ID")
    else:
        st.write("There are no entries in the database! Please insert first!")

#@st.cache(allow_output_mutation=True)
def get_data():
    if url_list:
        storage_options = {'User-Agent': 'Mozilla/5.0'}
        df = pd.read_csv(url_list[0]['filepath'].replace(" ", "%20"), storage_options=storage_options)
        # #Define Header columns
        columns_count = len(df.axes[1])
        
        #Define next columns 
        df['pre_pro_signal_EMG_1'] = 0
        df['pre_pro_signal_EMG_2'] = 0
        df['pre_pro_signal_EMG_3'] = 0
        df['RMS_1'] = float("nan")
        df['RMS_2'] = float("nan")
        df['RMS_3'] = float("nan")
        df['Acceleration'] = float("nan")
        df['Start_Velocity'] = float("nan")
        df['Velocity'] = float("nan")
        df['Rows_Count'] = df.index

        # Calculate the sum of all sensors Mass $ Weight
        #df['Mass_Sum'] = (df['Mass_1'] + df['Mass_2'] + df['Mass_3'] + df['Mass_4'])
        pm = df['Mass_Sum'].mean()

        # Calculate The Column Force
        df['Force'] = df['Mass_Sum'] * 9.81
        # Calculate Acceleration
        #if url_list[0]['type_of_trial'] == "CMJ":
        df['Acceleration'] = (df['Force'] / pm) - 9.81
        # Calculate Velocity
        df['Start_Velocity'] = df.Acceleration.rolling(window=2,min_periods=1).mean()*0.001
        df['Velocity'] = df.Start_Velocity.rolling(window=999999,min_periods=1).sum()

        low_cutoff = 10 # Hz
        high_cutoff = 450 # Hz
        frequency = 1000
        
        if 'Col_9' in df.columns:
            # THIS IS ALL FOR EMG TO RMS 1
            # [Baseline Removal] Convert Raw Data EMG to EMG
            df['Col_9_to_converted'] = (((df['Col_9']/ 2 ** 16) - 1/2 ) * 3 ) / 1000
            df['Col_9_to_converted'] = df['Col_9_to_converted'] *1000
            pre_pro_signal_1 = df['Col_9_to_converted'] - df["Col_9_to_converted"].mean()
            # Application of the signal to the filter. This is EMG1 after filtering
            pre_pro_signal_1= bsnb.aux_functions._butter_bandpass_filter(pre_pro_signal_1, low_cutoff, high_cutoff, frequency)
            df['pre_pro_signal_EMG_1'] = pre_pro_signal_1**2
            #This is RMS per 100
            df['RMS_1'] = df.pre_pro_signal_EMG_1.rolling(window=100,min_periods=100).mean()**(1/2)

            
        if 'Col_10' in df.columns:
            # THIS IS ALL FOR EMG TO RMS 2
            df['Col_10_to_converted'] = (((df['Col_10']/ 2 ** 16) - 1/2 ) * 3 ) / 1000
            df['Col_10_to_converted'] = df['Col_10_to_converted'] *1000
            pre_pro_signal_2 = df['Col_10_to_converted'] - df["Col_10_to_converted"].mean()
            # Application of the signal to the filter. This is EMG1 after filtering
            pre_pro_signal_2= bsnb.aux_functions._butter_bandpass_filter(pre_pro_signal_2, low_cutoff, high_cutoff, frequency)
            df['pre_pro_signal_EMG_2'] = pre_pro_signal_2**2
            #This is RMS per 100
            df['RMS_2'] = df.pre_pro_signal_EMG_2.rolling(window=100,min_periods=100).mean()**(1/2)

        # THIS IS ALL FOR EMG TO RMS 3
        if 'Col_11' in df.columns:
            df['Col_11_to_converted'] = (((df['Col_11']/ 2 ** 16) - 1/2 ) * 3 ) / 1000
            df['Col_11_to_converted'] = df['Col_11_to_converted'] *1000
            pre_pro_signal_3 = df['Col_11_to_converted'] - df["Col_11_to_converted"].mean()
            # Application of the signal to the filter. This is EMG1 after filtering
            pre_pro_signal_3= bsnb.aux_functions._butter_bandpass_filter(pre_pro_signal_3, low_cutoff, high_cutoff, frequency)
            df['pre_pro_signal_EMG_3'] = pre_pro_signal_3**2
            #This is RMS per 100
            df['RMS_3'] = df.pre_pro_signal_EMG_3.rolling(window=100,min_periods=100).mean()**(1/2)
        
        return pm, df


############################################################################################################                

if url_list:
    pm, df = get_data()

    ####### ###### #####THESE BLOCK IS ONLY FOR CMJ TRIAL ####### ######### #######
    if url_list[0]['type_of_trial'] == "CMJ":
        # Find Take Off Time: 
        for i in range (0, len(df.index)):
            if df.loc[i,'Force'] < 2:
                take_off_time = i
                break
        # Find Landing Time:
        for i in range (take_off_time, len(df.index)):
            if df.loc[i,'Force'] > 55:
                landing_time = i - 1
                break
        # Find Start Try Time
        for i in range(0,take_off_time):
            if df.loc[i,'Force'] < (df['Force'].mean() - 80):
                start_try_time = i
                break
        closest_to_zero_velocity = df.loc[start_try_time:take_off_time,'Velocity'].sub(0).abs().idxmin()
        closest_to_average_force_1st = (df.loc[start_try_time:closest_to_zero_velocity,'Force']-df['Force'].mean()).sub(0).abs().idxmin()
        closest_to_average_force_2nd = (df.loc[closest_to_zero_velocity:take_off_time,'Force']-df['Force'].mean()).sub(0).abs().idxmin()
    
    with st.expander(("Graph"), expanded=True):
        #### CREATE THE MAIN CHART #####
        fig = go.Figure()
        lines_to_hide = ["RMS_1","RMS_2","RMS_3"]
        # add x and y values for the 1st scatter
        # plot and name the yaxis as yaxis1 values
        fig.add_trace(go.Scatter(
            x=df['Rows_Count'],
            y=df['Force'],
            name="Force",
            line=dict(color="#290baf")
            
        ))
        # add x and y values for the 2nd scatter
        # plot and name the yaxis as yaxis2 values
        fig.add_trace(go.Scatter(
            x=df['Rows_Count'],
            y=df['Velocity'],
            name="Velocity",
            yaxis="y2",
            line=dict(color="#aa0022")
        ))
        
        # add x and y values for the 3rd scatter
        # plot and name the yaxis as yaxis3 values
        fig.add_trace(go.Scatter(
            x=df['Rows_Count'],
            y=df['RMS_1'],
            name="RMS_1",
            yaxis="y3"
        ))
        # add x and y values for the 4th scatter plot
        # and name the yaxis as yaxis4 values
        fig.add_trace(go.Scatter(
            x=df['Rows_Count'],
            y=df['RMS_2'],
            name="RMS_2",
            yaxis="y4",
            line=dict(color="#7b2b2a")
        ))
        fig.add_trace(go.Scatter(
            x=df['Rows_Count'],
            y=df['RMS_3'],
            name="RMS_3",
            yaxis="y5",
            
        ))
        # Create axis objects
        fig.update_layout(
            # split the x-axis to fraction of plots in
            # proportions
            autosize=False,
            title_text="5 y-axes scatter plot",
            #width=1420,
            height=550,
            title_x=0.3,
            margin=dict(
                l=50,
                r=50,
                b=100,
                t=100,
                pad=4
            ),
            hovermode='x',
            plot_bgcolor="#f9f9f9",
            paper_bgcolor='#f9f9f9',
            xaxis=dict(
                domain=[0.125, 0.92],
                linecolor="#BCCCDC",
                showspikes=True, # Show spike line for X-axis
                #Format spike
                spikethickness=2,
                spikedash="dot",
                spikecolor="#999999",
                spikemode="toaxis",
                
                #spikemode= 'toaxis' #// or 'across' or 'marker'      
            ),
            # pass the y-axis title, titlefont, color
            # and tickfont as a dictionary and store
            # it an variable yaxis
            yaxis=dict(
                title="Force",
                titlefont=dict(
                    color="#0000ff"
                ),
                tickfont=dict(
                    color="#0000ff"
                ),
                linecolor="#BCCCDC",
                showspikes=True,
                spikethickness=2,
                spikedash="dot",
                spikecolor="#999999",
                spikemode="toaxis",
                
            ),
            # pass the y-axis 2 title, titlefont, color and
            # tickfont as a dictionary and store it an
            # variable yaxis 2
            yaxis2=dict(
                title="Velocity",
                titlefont=dict(
                    color="#FF0000"
                ),
                tickfont=dict(
                    color="#FF0000"
                ),
                anchor="free",  # specifying x - axis has to be the fixed
                overlaying="y",  # specifyinfg y - axis has to be separated
                side="left",  # specifying the side the axis should be present
                position=0.06,  # specifying the position of the axis

                linecolor="#BCCCDC",
                showspikes=True,
                # spikethickness=2,
                # spikedash="dot",
                # spikecolor="#999999",
                # spikemode="toaxis",

                
                
            ),
            # pass the y-axis 3 title, titlefont, color and
            # tickfont as a dictionary and store it an
            # variable yaxis 3
            yaxis3=dict(
                title="RMS_1",
                titlefont=dict(
                    color="#006400"
                ),
                tickfont=dict(
                    color="#006400"
                ),
                anchor="x",     # specifying x - axis has to be the fixed
                overlaying="y",  # specifyinfg y - axis has to be separated
                side="right" # specifying the side the axis should be present
                #position=0.85
            ),
            
            # pass the y-axis 4 title, titlefont, color and
            # tickfont as a dictionary and store it an
            # variable yaxis 4
            yaxis4=dict(
                title="RMS_2",
                titlefont=dict(
                    color="#7b2b2a"
                ),
                tickfont=dict(
                    color="#7b2b2a"
                ),
                anchor="free",  # specifying x - axis has to be the fixed
                overlaying="y",  # specifyinfg y - axis has to be separated
                side="right",  # specifying the side the axis should be present
                position=0.98  # specifying the position of the axis
            ),
            yaxis5=dict(
                title="RMS_3",
                titlefont=dict(
                    color="#ffbb00"
                ),
                tickfont=dict(
                    color="#ffbb00"
                ),
                anchor="free",  # specifying x - axis has to be the fixed
                overlaying="y",  # specifyinfg y - axis has to be separated
                side="left",  # specifying the side the axis should be present
                position=0.00  # specifying the position of the axis
            )
        )
        # Update layout of the plot namely title_text, width
        # and place it in the center using title_x parameter
        # as shown
        large_rockwell_template = dict(
            layout=go.Layout(title_font=dict(family="Rockwell", size=24))
        )
        
        #     #template=large_rockwell_template
        #     # barmode='group',
        #     #hovermode='x',#paper_bgcolor="LightSteelBlue"   
        # )
        
        fig.update_xaxes(
            
            rangeslider_visible=True,
            # rangeselector=dict(
            #     buttons=list([
            #         dict(count=1, label="1m", step="month", stepmode="backward"),
            #         dict(count=4000, label="6m", step="month", stepmode="backward"),
            #         dict(count=6000, label="YTD", step="year", stepmode="todate"),
            #         dict(count=12000, label="1y", step="year", stepmode="backward"),
            #         dict(step="all")
            #     ])
            # )
        )
        # This is to hide by default some line
        fig.for_each_trace(lambda trace: trace.update(visible="legendonly") 
                        if trace.name in lines_to_hide else ())

        #def customAnnotations(df, anno_start_try_time, anno_take_off_time, yVal):
        # xStart = '2020-08-04'
        # xEnd = '2020-08-06'
        # xVal='date'
        # yVal='regression_sales'
        
            #fig = go.Figure(data=go.Scatter(x=df['Rows_Count'], y=df[yVal].values, marker_color='black'))
            #per_start = df[df.index==xStart]
            #per_end = df[df.index==xEnd]

            # fig.add_annotation(dict(font=dict(color='rgba(0,0,200,0.8)',size=12),
            #                                     x=closest_to_zero_velocity,
            #                                     #x = xStart
            #                                     y=df.loc[closest_to_zero_velocity,'Force'],
            #                                     showarrow=True,
            #                                     text="Velocity to Zero",
            #                                     textangle=0,
            #                                     xanchor='right',
            #                                     xref="x",
            #                                     yref="y"))

            # fig.add_annotation(dict(font=dict(color='rgba(0,0,200,0.8)',size=12),
            #                                     x=closest_to_average_force2,
                                                
            #                                     #x = xStart
            #                                     y=df.loc[closest_to_average_force2,'Force'],
            #                                     showarrow=True,
            #                                     text="Force to Average",
            #                                     textangle=0,
            #                                     xanchor='right',
            #                                     xref="x",
            #                                     yref="y"))

            # fig.add_annotation(dict(font=dict(color='rgba(0,0,200,0.8)',size=12),
            #                                     x=per_end.index[0],
            #                                     #x = xStart
            #                                     y=per_end[yVal].iloc[0],
            #                                     showarrow=False,
            #                                     text='Period end = ' + per_end.index[0] + '  ',
            #                                     #ax = -10,
            #                                     textangle=0,
            #                                     xanchor='right',
            #                                     xref="x",
            #                                     yref="y"))
            
           # fig.show()
            
        #customAnnotations(df=df, anno_start_try_time = start_try_time, anno_take_off_time = take_off_time,  yVal='Velocity')
        st.plotly_chart(fig,use_container_width=True)

    ###### ##### ##### Calculate the times for periods for the CMJ Trial: ##### ###### ######
    if url_list[0]['type_of_trial'] == 'CMJ':
        st.caption("Helpfull information about the times of the graph after the start of the CMJ trial:")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.write(" Velocity closest to zero is at:", closest_to_zero_velocity)
        with c2:
            st.write(" Take Off Time is at:", take_off_time)
        with c3:
            st.write(" Landing Time is at:", landing_time)

    
    col1, col2 = st.columns(2)
    r=0  
    with st.form("Select Graph Area", clear_on_submit=True):
        st.caption("Input these fields to calculate specific time period:")
        c1, c2= st.columns(2)
        with c1:        
            user_time_input_min_main_table = st.number_input("From Time", value=0, step=1 )#int(df.index.min()))
        with c2:
            user_time_input_max_main_table = st.number_input("Till Time", value=0, step=1 )#int(df.index.max()))
        brushed_submitted = st.form_submit_button("Calculate results", help="this is hover")
        
    df_brushed = df[(df.index >= user_time_input_min_main_table) & (df.index < user_time_input_max_main_table)]
    
    jump_depending_impluse = float("nan")
    
    if url_list[0]['type_of_trial'] == "CMJ":
        #vertical_take_off_velocity = st.number_input("Give the time of vertical take off velocity")
        jump_depending_take_off_velocity = (df.loc[take_off_time, 'Velocity'] ** 2) / (2 * 9.81)
        jump_depending_time_in_air = (1 / 2) * 9.81 * (((landing_time - take_off_time) / 1000 ) / 2 ) ** 2 

    ######### ###### ######### ######## BRUSHED AREA ########### ########## ###########
    if brushed_submitted:
        df_brushed = df[(df.index >= user_time_input_min_main_table) & (df.index <= user_time_input_max_main_table)]

        if url_list[0]['type_of_trial'] == "CMJ":
            ######### ######## ########## JUMP METHOD | ONLY FOR CMJ TRIAL ############ ########### ############
            #Find the Impluse GRF:
            df_brushed['Impulse_grf'] = df_brushed['Force'] * (1/1000)
            impulse_grf = df_brushed['Impulse_grf'].sum()
            #Find the Impulse BW:
            impulse_bw_duration = (user_time_input_max_main_table - user_time_input_min_main_table) / 1000
            impulse_bw = pm * 9.81 * impulse_bw_duration
            # Find the Velocity depeding on Impulse:
            velocity_momentum1 = (impulse_grf - impulse_bw) / pm
            # Find the Jump:
            jump_depending_impluse = (velocity_momentum1 ** 2) / (9.81 * 2)
            rsi_duration = (take_off_time - start_try_time) / 1000
            rsi = jump_depending_impluse / rsi_duration
            
        #Find the RFD linear igression
        l_rfd1=[] 
        # l_emg1=[] # l_emg2=[] # l_emg3=[]
        b_rfd1=[]
        b_rfd1=[]
        # l_emg1=[] # l_emg2=[] # l_emg3=[] # b_emg1=[] # b_emg2=[] # b_emg3=[]
        headers_list_rfd1=[]
        # headers_list_emg1=[] # headers_list_emg2=[] # headers_list_emg3=[]
        rfd_df1=pd.DataFrame()

        # The whole RFD:
        X_all = df_brushed['Rows_Count'] - df_brushed['Rows_Count'].mean()
        Y_all = df_brushed['Force'] - df_brushed['Force'].mean()
        b_rfd1_whole = (X_all*Y_all).sum() / (X_all ** 2).sum()
        
        RFP_Total = pd.Series(b_rfd1_whole)

        # emg_df1=pd.DataFrame() # emg_df2=pd.DataFrame() # emg_df3=pd.DataFrame()
        for i in range(int(user_time_input_min_main_table),int(user_time_input_max_main_table),50):  
            ###### FIND RFD on selected time period ######
            X = df_brushed.loc[user_time_input_min_main_table:i:1,'Rows_Count'] - df_brushed.loc[user_time_input_min_main_table:i:1,'Rows_Count'].mean()
            Y = df_brushed.loc[user_time_input_min_main_table:i:1,'Force'] - df_brushed.loc[user_time_input_min_main_table:i:1,'Force'].mean()
            b_rfd1 = (X*Y).sum() / (X ** 2).sum()
            headers_list_rfd1.append("RFD-"+str(i))
            l_rfd1.append(b_rfd1)
            
            #FIND R-EMG
            # X = df_brushed.loc[user_time_input_min_main_table:i:1,'Rows_Count'] - df_brushed.loc[user_time_input_min_main_table:i:1,'Rows_Count'].mean()

            # Y1 = df_brushed.loc[user_time_input_min_main_table:i:1,'pre_pro_signal_EMG_1'] - df_brushed.loc[user_time_input_min_main_table:i:1,'pre_pro_signal_EMG_1'].mean()
            # Y2 = df_brushed.loc[user_time_input_min_main_table:i:1,'pre_pro_signal_EMG_2'] - df_brushed.loc[user_time_input_min_main_table:i:1,'pre_pro_signal_EMG_2'].mean()
            # Y3 = df_brushed.loc[user_time_input_min_main_table:i:1,'pre_pro_signal_EMG_3'] - df_brushed.loc[user_time_input_min_main_table:i:1,'pre_pro_signal_EMG_3'].mean()

            # b_emg1 = (X*Y1).sum() / (X ** 2).sum()
            # b_emg2 = (X*Y2).sum() / (X ** 2).sum()
            # b_emg3 = (X*Y3).sum() / (X ** 2).sum()

            # headers_list_emg1.append("EMG_1-"+str(i))
            # headers_list_emg2.append("EMG_2-"+str(i))
            # headers_list_emg3.append("EMG_3-"+str(i))
            # l_emg1.append(b_emg1)
            # l_emg2.append(b_emg2)
            # l_emg3.append(b_emg3)

        # Create the final dataframe for RFD 
        if rfd_df1.empty:
            rfd_df1 = pd.DataFrame([l_rfd1])
            cols = len(rfd_df1.axes[1])
            rfd_df1.columns = [*headers_list_rfd1]
        else:
            to_append = l_rfd1
            rfd_df1_length = len(rfd_df1)
            rfd_df1.loc[rfd_df1_length] = to_append

        # #Dataframe for EMG1
        # if emg_df1.empty:
        #     emg_df1 = pd.DataFrame([l_emg1])
        #     cols = len(emg_df1.axes[1])
        #     emg_df1.columns = [*headers_list_emg1]
        # else:
        #     to_append = emg_df1
        #     emg_df1_length = len(emg_df1)
        #     emg_df1.loc[emg_df1_length] = to_append
        
        # #Dataframe for EMG2
        # if emg_df2.empty:
        #     emg_df2 = pd.DataFrame([l_emg2])
        #     cols = len(emg_df2.axes[1])
        #     emg_df2.columns = [*headers_list_emg2]
        # else:
        #     to_append = emg_df2
        #     emg_df2_length = len(emg_df2)
        #     emg_df2.loc[emg_df2_length] = to_append

        # #Dataframe for EMG3
        # if emg_df3.empty:
        #     emg_df3 = pd.DataFrame([l_emg3])
        #     cols = len(emg_df3.axes[1])
        #     emg_df3.columns = [*headers_list_emg3]
        # else:
        #     to_append = emg_df3
        #     emg_df3_length = len(emg_df3)
        #     emg_df3.loc[emg_df3_length] = to_append
        #Give Specific Results
        with st.expander('Show Specific Calculations' , expanded=True):
            st.write('Time Period: from', user_time_input_min_main_table, "to ", user_time_input_max_main_table)
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                    st.write('Force-Mean:', round(df_brushed["Force"].mean(),4))
                    st.write('Force-Min:', round(min(df_brushed['Force']),4))
                    st.write('Force-Max:', round(max(df_brushed['Force']),4))
            with col2:
                    st.write('RMS_1-Mean:', round(df_brushed["RMS_1"].mean(),4))
                    st.write('RMS_2-Mean:', round(df_brushed['RMS_2'].mean(),4))
                    st.write('RMS_3-Mean:', round(df_brushed['RMS_3'].mean(),4))
            if url_list[0]['type_of_trial'] == "CMJ":
                with col3:
                        st.write('Impulse GRF:', round(impulse_grf,4))
                        st.write('Impulse BW:', round(impulse_bw,4))
                        st.write('Net Impulse:', round(impulse_grf - impulse_bw,4))
                        #st.write('velocity_momentum:', round(velocity_momentum1,2))
                with col4:
                        st.write('Jump (Impluse):', round(jump_depending_impluse,4))
                        st.write('Jump (Take Off Velocity:', round(jump_depending_take_off_velocity,4))
                        st.write('Jump (Time in Air):', round(jump_depending_time_in_air,4), ', RSI:', round(rsi,4))
                        
            #output = my_formatter.format(pi)

        
        #Display Dataframe in Datatable
        with st.expander("Show Data Table", expanded=True):
            selected_filtered_columns = st.multiselect(
            label='What column do you want to display', default=('Time', 'Force', 'Acceleration', 'Velocity', 'RMS_1', 'RMS_2','RMS_3'), help='Click to select', options=df_brushed.columns)
            st.write(df_brushed[selected_filtered_columns])
            #Button to export results
            st.download_button(
                label="Export table dataset",
                data=df_brushed[selected_filtered_columns].to_csv(),
                file_name=url_list[0]['filename'] +'.csv',
                mime='text/csv',
            )

        st.write('Export All Metrics')
        specific_metrics = [""]
        specific_metrics = {#'Unit': ['results'],
                'Fullname' : url_list[0]['fullname'],
                'Occupy' : url_list[0]['occupy'],
                'Type of try' : url_list[0]['type_of_trial'],
                'Filename' : url_list[0]['filename'],
                'Body Mass (kg)': [pm],
                'Jump (m/s)' : [jump_depending_impluse],
                'RSI m/s' : [rsi],

                'RMS_1 Mean' : [df_brushed['RMS_1'].mean()],
                'RMS_2 Mean' : [df_brushed['RMS_2'].mean()],
                'RMS_3 Mean' : [df_brushed['RMS_3'].mean()],
                'Force Mean (N)' : [df_brushed['Force'].mean()],
                'Force Max (N)' : [max(df_brushed['Force'])],
                'RFD Total ' + str(user_time_input_min_main_table) + '-' + str(user_time_input_max_main_table) : [b_rfd1_whole]
                

                }
        
        specific_metrics_df = pd.DataFrame(specific_metrics)
        #Combine all dataframes to one , for the final export
        final_results_df = pd.concat([specific_metrics_df, rfd_df1], axis=1, join='inner')
        #final_results_df['Body Mass (kg)'] = final_results_df['Body Mass (kg)'].round(decimals = 2)
        final_results_df =np.round(final_results_df, decimals = 4)
        
        st.write(final_results_df)
       
        
       
        #st.write(specific_metrics)
        st.download_button(
            label="Export Final Results",
            data=final_results_df.to_csv(),
            file_name=url_list[0]['filename'] +'_final_results.csv',
            mime='text/csv',
                )

        #with st.form("Insert results to Database:"):   
            #verify_check_box_insert_final_results = st.text_input( "Please type Verify to insert the final results to database")

            #submitted_button_insert_final_results = st.form_submit_button("Insert Results")

        #if submitted_button_insert_final_results:
            # @st.experimental_singleton
            # def init_connection():
            #     url = st.secrets["supabase_url"]
            #     key = st.secrets["supabase_key"]
            #     #client = create_client(url, key)
            #     return create_client(url, key)
            # con = init_connection()

            #if verify_check_box_insert_final_results == "Verify":
    #     st.write("bika")
    #     def add_entries_to_final_results(supabase):
    #             value = {'id': url_id_number_input, 'fullname': url_list[0]['fullname'], 'age': url_list[0]['age'], 'height': url_list[0]['height'], 'weight':url_list[0]['weight'], 'type_of_trial': url_list[0]['type_of_trial'], 'filename': url_list[0]['filename'], 'filepath': url_list[0]['filepath'], 
    #                         'occupy': url_list[0]['occupy'], 'jump': round(jump_depending_impluse,4), 'rms_1_mean': df_brushed['RMS_1'].mean(), 'rms_2_mean': df_brushed['RMS_2'].mean(), 'rms_3_mean': df_brushed['RMS_3'].mean(), 'force_mean': round(df_brushed['Force'].mean(),4), 'force_max': round(max(df_brushed['Force']),4)}
    #             data = supabase.table('final_results').insert(value).execute()
    #     def main():
    #         new_entry = add_entries_to_final_results(con)
    #     main()
    #     st.success('Thank you! A new entry has been inserted to database!')

    #     def select_all_from_final_results():
    #         query=con.table("final_results").select("*").execute()
    #         return query
    #     query = select_all_from_final_results()


    #     df_final_results = pd.DataFrame(query.data)
    #     st.wri("The datatable with Final Results:", df_final_results)
    # #else:
       # st.write("Please verify the check box to insert final results to database!")

        # with st.form("Type the ID of your link:"):   

        #     submitted = st.form_submit_button("Insert Results")
        # # Querry to find the data row of specific ID
        # if submitted:
        #     def add_entries_to_final_results(supabase):
        #                     value = {'fullname': fullname, 'age': age, 'heigth': height, 'weight':weight, 'type_of_trial': type_of_trial, 'filename': filename, 'filepath': filepath, 'occupy': occupy, 'jump': jump, 'rms_1_mean': rms_1_mean, 'rms_2_mean': rms_2_mean, 'rms_3_mean': rms_3_mean, 'force_mean': force_mean, 'force_max': force_max}
        #                     data = supabase.table('final_results').insert(value).execute()
        #     def main():
        #         new_entry = add_entries_to_final_results(con)
            

        #     main()
        #     st.success('Thank you! A new entry has been inserted to database!')


        # def select_all_from_final_results():
        #     query=con.table("final_results").select("*").execute()
        #     return query
        # query = select_all_from_final_results()


        # df_final_results = pd.DataFrame(query.data)
        # df_final_results
    

                #url_id_number_input = st.number_input("Type the ID of your prerferred trial and Press Calculate Results:",value=0,step=1)
                


    ##################### ################### UN BRUSHED AREA ##################### ######################## ###################
    else:
        with st.expander("Show Specific Calculations", expanded=True):
            st.caption("Whole Time Period")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                    st.write('Force-Mean:', round(df["Force"].mean(),4))
                    st.write('Force-Min:', round(min(df['Force']),4))
                    st.write('Force-Max:', round(max(df['Force']),4))
            with col2:
                    st.write('RMS_1-Mean:', round(df["RMS_1"].mean(),4))
                    st.write('RMS_2-Mean:', round(df["RMS_2"].mean(),4))
                    st.write('RMS_3-Mean:', round(df["RMS_3"].mean(),4))   
            with col3:
                    st.write("")
            with col4:
                    st.write("")       
        
        #Display Dataframe in Datatable
        with st.expander("Show Data Table", expanded=True):
            selected_clear_columns = st.multiselect(
            label='What column do you want to display', default=('Time', 'Force', 'Acceleration', 'Velocity', 'RMS_1', 'RMS_2', 'RMS_3'), help='Click to select', options=df.columns)
            st.write(df[selected_clear_columns])
            #Button to export results
            st.download_button(
                label="Export table dataset",
                data=df[selected_clear_columns].to_csv(),
                file_name=url_list[0]['filename'] + '.csv',
                mime='text/csv',
            )
    #Values Sidebar
    
    with st.sidebar.expander(("Information about the Trial"), expanded=True):
        st.write('**Name**:', url_list[0]['fullname'])
        st.write('**Age**:', url_list[0]['age'])
        st.write('**Height**:', url_list[0]['height'])
        st.write('**Body mass is**:', round(pm,2), 'kg')
        st.write('**Type of try**:', url_list[0]['type_of_trial'])
        st.write('**File Name**:', url_list[0]['filename'])
        st.write('**Occupy:**', url_list[0]['occupy'])
        st.write('**Jump:**', jump_depending_impluse)
        if url_list[0]['type_of_trial'] == "CMJ":
            st.write('**Start Trial starts at**:', start_try_time, 'ms')
            st.write('**Take Off Time starts at**:', take_off_time, 'ms')
            st.write('**Landing Time at**:', landing_time, 'ms')
        
            
