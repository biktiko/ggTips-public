import os
import pandas as pd
import streamlit as st
import altair as alt
from data.ggTipsData import load_data, uploadFilesPath
from ggtipsconfig import login

st.set_page_config(layout='wide')

authenticator = login()

if st.session_state['authentication_status']:
  
    data = load_data()
    
    companies = data['companies']
    tips = data['tips']
    defaultInputs = data['defaultInputs']
    ggTeammates = data['ggTeammates']
    
    filteredTips = tips.copy()

    for setting in defaultInputs.keys():
        if setting not in st.session_state:
            st.session_state[setting] = defaultInputs[setting]

    os.makedirs(uploadFilesPath, exist_ok=True)

    with st.expander('Import new data'):
        if 'uploadedFiles' not in st.session_state:
            st.session_state['uploadedFiles'] = [os.path.join(uploadFilesPath, file) for file in os.listdir(uploadFilesPath)]

        uploadedFile = st.file_uploader("New data", type=["csv", 'xlsx'])
        if uploadedFile:
            newFilePath = os.path.join(uploadFilesPath, uploadedFile.name)
            with open(newFilePath, "wb") as f:
                f.write(uploadedFile.getbuffer())
            st.success('New data added')
            st.session_state['uploadedFiles'].append(newFilePath)

    st.title('ggTips')
    

    if 'tips' in data:
        options = {
            'companiesOptions' : list(tips['Company'].unique()) if 'Company' in tips else ['All'],
            'partnersOptions' : list(tips['Partner'].unique()) if 'Partner' in tips else ['All'],
            'paymentProcessorOptions': list(tips['Payment processor'].unique()) if 'Payment processor' in tips else ['All'],
            'StatusOptions' : list(tips['Status'].unique()) if 'Status' in tips else ['All'],
            'ggPayeersOptions' : ['All', 'Wihout gg teammates', 'Only gg teammates']
        }

        # Настройки боковой панели
        with st.sidebar:
            st.header('Settings')
            
            with st.expander('ggTips filters'):
                        
                date_range = st.date_input("Select date range", [])
                
                if date_range:
                    start_date, end_date = date_range
                    filteredTips = filteredTips[(filteredTips['Date'] >= pd.to_datetime(start_date)) & (filteredTips['Date'] <= pd.to_datetime(end_date))]

                col1, col2 = st.columns(2)

                with col1:
                    st.selectbox('ggPayers', options['ggPayeersOptions'], key='ggPayeers')

                with col2:
                    st.multiselect('Payment Processor', options['paymentProcessorOptions'], default=st.session_state['paymentProcessor'], key='paymentProcessor')

                col1, col2 = st.columns(2)

                with col1:
                    st.number_input('Min amount', value=st.session_state['amountFilterMin'], step=1000, min_value=0, max_value=50000, key='amountFilterMin')

                with col2:
                    st.number_input('Max amount', value=st.session_state['amountFilterMax'], step=1000, min_value=st.session_state['amountFilterMin'], max_value=50000, key='amountFilterMax')
                        
            with st.expander('**Graph values**'):
                sum_type = st.selectbox('Sum Chart Type', ['Column', 'Line', 'Area', 'None'])
                count_type = st.selectbox('Count Chart Type', ['Line', 'Column', 'Area', 'None'])
                
            with st.expander('**Graph Customize**'):
                
                col1, col2 = st.columns(2)
                with col1:
                    sum_color = st.color_picker('Sum Color', '#00FF00')
                with col2:
                    count_color = st.color_picker('Count Color', '#0000FF')
                    
                text_color = st.color_picker('Text Color', '#FFFFFF')
                chart_width = st.slider('Chart Width', 600, 1200, 1000)
                chart_height = st.slider('Chart Height', 400, 800, 500)
                reset_button = st.button('Reset Settings')

            # Если нажата кнопка сброса
            if reset_button:
                st.session_state['chart_type'] = 'Column'
                st.session_state['show_table'] = False
                st.session_state['sum_color'] = '#00FF00'
                st.session_state['count_color'] = '#0000FF'
                st.session_state['text_color'] = '#FFFFFF'
                st.session_state['chart_width'] = 1000
                st.session_state['chart_height'] = 500
                st.rerun()  # Перезапуск приложения для применения сброса настроек

        col1, col2 = st.columns(2)

        with col1:
            st.multiselect('Select companies', options['companiesOptions'], key='selectedCompanies')

        with col2:
            st.multiselect('Select partners', options['partnersOptions'], key='selectedPartners')
        
        if 'selectedCompanies' in st.session_state and st.session_state['selectedCompanies']:
            filteredTips = filteredTips[filteredTips['Company'].isin(st.session_state['selectedCompanies'])]
        if 'selectedPartners' in st.session_state and st.session_state['selectedPartners']:
            filteredTips = filteredTips[filteredTips['Partner'].isin(st.session_state['selectedPartners'])]
        if 'Status' in st.session_state and st.session_state['Status']:
            filteredTips = filteredTips[filteredTips['Status'].isin(st.session_state['Status'])]
        if 'paymentProcessor' in st.session_state and st.session_state['paymentProcessor']:
            filteredTips = filteredTips[filteredTips['Payment processor'].isin(st.session_state['paymentProcessor'])]
        if  'Amount' in filteredTips and 'amountFilterMin' in st.session_state and 'amountFilterMax' in st.session_state:
            filteredTips = filteredTips[
                (filteredTips['Amount'] >= st.session_state['amountFilterMin']) &
                (filteredTips['Amount'] <= st.session_state['amountFilterMax'])
            ]
        if st.session_state['ggPayeers'] and 'ggPayer' in filteredTips.columns:
            if st.session_state['ggPayeers'] == 'Wihout gg teammates':
                filteredTips = filteredTips[~filteredTips['ggPayer'].isin(ggTeammates['id'])]
            elif st.session_state['ggPayeers'] == 'Only gg teammates':
                filteredTips = filteredTips[filteredTips['ggPayer'].isin(ggTeammates['id'])]   
                
        groupedTips = filteredTips.groupby('Week').agg({
            'Amount': 'sum',
            'uuid': 'count',  
            'WeekStart' : 'max',
            'WeekEnd': 'max'
        }).reset_index().rename(columns={'uuid': 'Count', 'Amount': 'ggTips'})

        groupedTips['Period'] = groupedTips['WeekStart'].dt.strftime('%Y-%m-%d') + ' - ' + groupedTips['WeekEnd'].dt.strftime('%Y-%m-%d')

        with st.expander('stats'):
            col1, col2, col3 = st.columns(3)
            sumTips = groupedTips['ggTips'].sum()
            countTips = groupedTips['Count'].sum()
            averageTip = sumTips / countTips
            
            with col1:
                st.write('Sum: ', sumTips)

            with col2:
                st.write('Count: ', countTips)
                
            with col3:
                st.write('One average tip', averageTip)
                
        # Создание графика с помощью Altair
        tab1, tab2 = st.tabs(['Graph', 'Tables'])
        
        with tab1: 
            
            if sum_type!='None' or count_type!='None':
                layers = []
                if sum_type!='None':
                    if sum_type == 'Column':
                        sum_layer = alt.Chart(groupedTips).mark_bar(size=20, color=sum_color)
                    elif sum_type == 'Line':
                        sum_layer = alt.Chart(groupedTips).mark_line(color=sum_color)
                    elif sum_type == 'Area':
                        sum_layer = alt.Chart(groupedTips).mark_area(color=sum_color)

                    sum_layer = sum_layer.encode(
                        x=alt.X('WeekStart:T', axis=alt.Axis(title='Week Start Date')),
                        y=alt.Y('ggTips:Q', axis=alt.Axis(title='Sum of Tips')),
                        tooltip=['Period', 'ggTips', 'Count']
                    ).properties(
                        width=chart_width,
                        height=chart_height
                    )
                    layers.append(sum_layer)

                if count_type!='None':
                    if count_type == 'Column':
                        count_layer = alt.Chart(groupedTips).mark_bar(size=20, color=count_color)
                    elif count_type == 'Line':
                        count_layer = alt.Chart(groupedTips).mark_line(color=count_color)
                    elif count_type == 'Area':
                        count_layer = alt.Chart(groupedTips).mark_area(color=count_color)

                    count_layer = count_layer.encode(
                        x=alt.X('WeekStart:T', axis=alt.Axis(title='Week Start Date', titleFontSize=14)),
                        y=alt.Y('Count:Q', axis=alt.Axis(title='Count of Transactions', titleFontSize=14)),
                        tooltip=['Period', 'ggTips', 'Count']
                    ).properties(
                        width=chart_width,
                        height=chart_height
                    )
                    layers.append(count_layer)

                # Комбинирование графиков
                chart = alt.layer(*layers).resolve_scale(
                    y='independent'
                ).configure_axis(
                    labelColor='white',
                    titleColor='white'
                )
                st.altair_chart(chart, use_container_width=True)

        with tab2:
            st.write('Companies')
            st.dataframe(companies)
            
            st.write('Filtered Data')
            st.dataframe(filteredTips)

    else:
        st.write("import data about ggTips product for analyze")

    authenticator.logout()

elif st.session_state['authentication_status'] == False:
    st.error('Username/password is incorrect')

elif st.session_state['authentication_status'] == None:
    st.warning('Please enter your username and password')
