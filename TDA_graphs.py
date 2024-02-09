# -*- coding: utf-8 -*-
"""
Created on Thu Feb  8 17:50:39 2024

@author: AzevedoB
"""

import streamlit as st
import pandas as pd
import cx_Oracle
import altair as alt

st.set_page_config(layout="wide")
col1,col2 = st.columns(2)

@st.cache_data  # 👈 Add the caching decorator
def alarms_occurences():
    #filter by probecard/test_program first. Show a list of the most frequent probecard + test_program combination
    df = pd.read_csv(r'/home/spyder/space_spyder/testdata/files/AlarmsOccurences.csv')
    return df

table = alarms_occurences()

with col1:
    st.title('TDA graphs')
    st.table(table.iloc[:7,1:])
@st.cache_data  # 👈 Add the caching decorator
def inputs():
    df1 = pd.read_csv(r'/home/spyder/space_spyder/testdata/files/allAlarms.csv')
    df1['FILE_DATE'] = pd.to_datetime(df1['FILE_DATE'])
    #drop NaN values from SITE, CARDID columns
    df1.dropna(axis=0, inplace=True)
    df1.reset_index()
    return df1
    
df = inputs()

@st.cache_data  # 👈 Add the caching decorator
def date():
    dsn_tns = cx_Oracle.makedsn('portsl228', '1535', service_name='dwhdev')
    con = cx_Oracle.connect(user='lao1report', password='LAO1REPORT_DEV', dsn=dsn_tns)
    cur = con.cursor()
    cur.execute("""SELECT TRUNC (f.file_date)
                FROM load_tests_files f
                WHERE id IN (SELECT file_id FROM load_tests_data_stats)
                ORDER BY f.file_date ASC
                """)
    datestart = cur.fetchone()
    cur.execute("""SELECT TRUNC (f.file_date)
                FROM load_tests_files f
                WHERE id IN (SELECT file_id FROM load_tests_data_stats)
                ORDER BY f.file_date DESC
                """)
    dateend = cur.fetchone()
    cur.close()
    con.close()
    return datestart,dateend
    
dates = date()

# INPUTS
with col2:
    st.divider()
    productnickname = st.selectbox('Product Nickname:',df['PRODUCT_NICKNAME'].unique())
    cardid = st.selectbox('Select Cardid:',df[df['PRODUCT_NICKNAME']==productnickname]['CARDID'].unique())
    testprogram = st.selectbox('Select Testprogram',df[df['CARDID']==cardid]['TEST_PROGRAM'].unique())
    site = st.selectbox('Select site',df[df['CARDID']==cardid]['SITE'].unique())
    st.markdown(f"**FROM** {dates[0][0].strftime('%B %d, %Y')} **TO** {dates[1][0].strftime('%B %d, %Y')}")

df_filtered = df.loc[(df['CARDID'] == cardid) & (df['TEST_PROGRAM'] == testprogram) & (df['SITE'] == site)]
tests = df_filtered['TEST_NUMBER'].unique()

@st.cache_data  # 👈 Add the caching decorator
def graphs(testes):
    for test in testes:
        df_graphs = df.loc[(df['TEST_NUMBER'] == test) & (df['CARDID'] == cardid) & (df['TEST_PROGRAM'] == testprogram) & (df['SITE'] == site)]
        df_graphs = df_graphs.sort_values(by='FILE_DATE')
        df_graphs.reset_index(drop = True,inplace = True)
        df_graphs['FILE_DATE'] = df_graphs['FILE_DATE'].dt.strftime('%Y-%m-%d %H:%M:%S')
        # Select relevant columns
        columns_to_plot = ['FILE_DATE', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
                           '11', '12', '13', '14', '15', 'G_AVG_PLUS_3STD', 'G_AVG_MINUS_3STD', 'G_AVG']
        
        # Melt the DataFrame to long format
        df_long = pd.melt(df_graphs, id_vars=['FILE_DATE'], value_vars=columns_to_plot[1:], var_name='Variable', value_name='Value')
        
        # graph caption
        st.write(f"""**TNO:** {test}   **TEST_NAME:** {df_graphs['TEST_NAME'][0].split(',')[0]}  **CARDID:** {cardid}     **TEST PROGRAM:** {testprogram}      **DEVIATED SITE:** {site}""")
        
        # Create Altair chart
        chart = alt.Chart(df_long).mark_line().encode(
            x='FILE_DATE:N',
            y=alt.Y('Value:Q', scale=alt.Scale(zero=False), axis = alt.Axis(title=f'Value {[df_graphs["TEST_UNIT"].iloc[0]]}')),
            color=alt.Color('Variable:N'),
            size=alt.Size(
                'Variable:N',
                scale=alt.Scale(range = [4,4], domain=['G_AVG_PLUS_3STD', 'G_AVG_MINUS_3STD', 'G_AVG'])
            ),
            tooltip=['Variable:N', 'Value:Q']
        ).properties(
            autosize=alt.AutoSizeParams(contains='padding', type='fit-y'),
            width=800,
            height=400
        )
        
        # Display the chart using Streamlit
        st.altair_chart(chart, use_container_width=True)
        
if st.button("Rerun"):
    tests_graphs = tests
    graphs(tests_graphs)