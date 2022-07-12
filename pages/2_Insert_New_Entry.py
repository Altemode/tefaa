
import os
import streamlit as st
import pandas as pd
from supabase import create_client, Client
import ftplib
import tempfile
from pathlib import Path


############# ############## PAGE 2 INSERT TO DATABASE USER+TRIAL ############## ############ #############################
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


st.sidebar.info("Hello, lets try to insert a new entry to database!")
st.sidebar.info("- Give the full name of the person!")
st.sidebar.info("- Give the email adress of the person!")
st.sidebar.info("- Give the occupy of the person!")
st.sidebar.info("- Choose the proper kind of trial!")
st.sidebar.info("- Choose the file of the trial. Please use only undescrores, not spaces in the file name!")
st.sidebar.info("- Click on Show All Entries to check the database!")

st.title("Import Entry to Database!")

# filepath1 = st.file_uploader("Choose a file1")
# #filepath2 =os.path.basename(fileitem.filepath1)
# #fil = pathlib.Path(filepath1.name)
# filepath1.name


#Create the Form to submit data to database:
with st.form("Create a new entry"):
    fullname = st.text_input("Fullname")
    age = st.number_input("Age", value=0, step=1)
    height = st.number_input("Height in cm", value=0, step=1)
    weight = st.number_input("Weight in gr")
    email = st.text_input("Email address")
    occupy = st.text_input("Occupy")
    type_of_trial = st.selectbox("Kind of Trial", ('-','CMJ', 'SJ','DJ','ISO' ))
    filepath = st.file_uploader("Choose a file", type="csv")
    #checkbox_val = st.checkbox("Form checkbox")
    submitted = st.form_submit_button("Submit values")
    
    if submitted:
        
        if fullname and age and height and weight and occupy and type_of_trial !='-' and filepath:
            
            filename_with_extension = filepath.name
            # Filename without extension
            filename = os.path.splitext(filename_with_extension)[0]

            def storage_connection():
                hostname = st.secrets["hostname"]
                username = st.secrets["username"]
                password = st.secrets["password"]
                
                return hostname,username,password
            hostname,username,password = storage_connection()
            
            ftp = ftplib.FTP(hostname,username,password)
            
            
            # This is the method to take the temporary path of the uploaded file and the value in bytes of it.
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                fp_PosixPath = Path(tmp_file.name)
                fp_PosixPath.write_bytes(filepath.getvalue())
            # This is to take the str of PosixPath.
            fp_str = str(fp_PosixPath)
            # This is our localfile's path in str.
            localfile = fp_str
            # This is the remote path of the server to be stored.
            remotefile='/sportsmetrics.geth.gr/storage/' + filename_with_extension

            # This is the method to store the localfile in remote server through ftp.
            with open(localfile, "rb") as file:
                ftp.storbinary('STOR %s' % remotefile, file)
            ftp.quit()
            
            filepath="https://sportsmetrics.geth.gr/storage/" + filename_with_extension
                     
            list = (fullname,email,occupy,type_of_trial,filename)
            def add_entries_to_main_table(supabase):
                value = {'fullname': fullname, 'email': email, 'occupy': occupy, 'type_of_trial': type_of_trial,
                        'filename': filename, "filepath": filepath, "height": height, "weight": weight, "age": age }
                data = supabase.table('main_table').insert(value).execute()
            def main():
                new_entry = add_entries_to_main_table(con)
            main()
            st.success('Thank you! A new entry has been inserted to database!')
            st.write(list)
        else:
            st.error("One of the field values is missing")
#@st.experimental_memo(ttl=600)
def select_all_from_main_table():
    query=con.table("main_table").select("*").execute()
    return query
main_table_all = select_all_from_main_table()
df_all_from_main_table = pd.DataFrame(main_table_all.data)


# url = st.text_input("Paste the desire url")
#
# if url:
#     storage_options = {'User-Agent': 'Mozilla/5.0'}
#     df = pd.read_csv(url,storage_options=storage_options)
#     st.write(df)






