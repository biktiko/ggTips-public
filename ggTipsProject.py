import os
import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit_plotly_events import plotly_events
from data.ggTipsData import load_data, uploadFilesPath
from ggtipsconfig import login

st.set_page_config(layout='wide')

authenticator = login()

if st.session_state['authentication_status']:
  
    data = load_data()
    
    if 'tips' in data:
        tips = data['tips']
    else:
        tips = pd.DataFrame()

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

        uploadedFiles = st.session_state['uploadedFiles']

        col1, col2 = st.columns(2)

        importedFilesDetails = st.checkbox("Imported Files details")

        if importedFilesDetails and uploadedFiles:
            for file in uploadedFiles:
                st.write(f"File: {os.path.basename(file)}")
                st.write(f"Size: {os.path.getsize(file) / 1024:.2f} KB")
                if file.endswith('.xlsx'):
                    df = pd.read_excel(file)
                else:
                    df = pd.read_csv(file)
                st.write(f"Number of rows: {len(df)}")
                st.write(f"Columns: {', '.join(df.columns)}")
                st.write("---")

        clearFolderButtonClicked = st.button("Delete all new files", key="clearFolderButton")

        if clearFolderButtonClicked:
                for file in os.listdir(uploadFilesPath):
                    file_path = os.path.join(uploadFilesPath, file)
                    if os.path.isfile(file_path):
                        try:
                            os.remove(file_path)
                            st.session_state['uploadedFiles'] = []
                            st.success("Imported data cleared")
                        except PermissionError as e:
                            st.error(f"Failed to delete {file_path}: {e}")
                        except Exception as e:
                            st.error(f"Unexpected error when deleting {file_path}: {e}")

    defaultInputs = data['defaultInputs']

    for setting in defaultInputs.keys():
        if setting not in st.session_state:
            st.session_state[setting] = defaultInputs[setting]

    st.title('ggTips')

    if 'tips' in data:
        months = {
            'January': 1,
            'February': 2,
            'March': 3,
            'April': 4,
            'May': 5,
            'June': 6,
            'July': 7,
            'August': 8,
            'September': 9,
            'October': 10,
            'November': 11,
            'December': 12,
        }
        
        options = {
            'companiesOptions' : list(tips['Company'].unique()) if 'Company' in tips else ['All'],
            'partnersOptions' : list(tips['Partner'].unique()) if 'Partner' in tips else ['All'],
            'paymentProcessorOptions': list(tips['Payment processor'].unique()) if 'Payment processor' in tips else ['All'],
            'StatusOptions' : list(tips['Status'].unique()) if 'Status' in tips else ['All'],
            'ggPayeersOptions' : ['All', 'Wihout gg teammates', 'Only gg teammates']
        }

        col1, col2 = st.columns(2)

        with col1:
            st.multiselect('Select companies', options['companiesOptions'], key='selectedCompanies')

        with col2:
            st.multiselect('Select partners', options['partnersOptions'], key='selectedPartners')

        st.multiselect('Select month', list(months.keys()), key='selectedMonth')

        timeIntervalOptions = ['All', 'Week', 'Month', 'Year', 'Week day', 'Day', 'Hour', 'Custom day']

        if st.session_state['timeInterval'] != 'Custom day':
            st.selectbox('Time interval', timeIntervalOptions, key='timeInterval')
        else:

            col1, col2 = st.columns(2)

            with col1:
                st.selectbox('Time interval', timeIntervalOptions, index=timeIntervalOptions.index("Custom day"), key='timeInterval')

            with col2:
                st.number_input('Custom', value=10, step=1, min_value=1)  # set max value

        with st.expander('More filters'):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.selectbox('ggPayers', options['ggPayeersOptions'], key='ggPayeers')

            with col2:
                st.multiselect('Payment Processor', options['paymentProcessorOptions'], default=st.session_state['paymentProcessor'], key='paymentProcessor')

            with col3:
                st.multiselect('Payment Status', options['StatusOptions'], default=st.session_state['Status'], key='Status')

            col1, col2 = st.columns(2)

            with col1:
                st.number_input('Min amount', value=st.session_state['amountFilterMin'], step=1000, min_value=0, max_value=50000, key='amountFilterMin')

            with col2:
                st.number_input('Max amount', value=st.session_state['amountFilterMax'], step=1000, min_value=st.session_state['amountFilterMin'], max_value=50000, key='amountFilterMax')


        def setFilters():
            filteredTips = tips.copy()

            if 'selectedCompanies' in st.session_state and st.session_state['selectedCompanies']:
                filteredTips = filteredTips[filteredTips['Company'].isin(st.session_state['selectedCompanies'])]
            if 'selectedMonth' in st.session_state and st.session_state['selectedMonth']:
                month_indices = [months[month] for month in st.session_state['selectedMonth']]
                filteredTips = filteredTips[filteredTips['month'].isin(month_indices)]
            if 'Status' in st.session_state and st.session_state['Status']:
                filteredTips = filteredTips[filteredTips['Status'].isin(st.session_state['Status'])]
            if 'paymentProcessor' in st.session_state and st.session_state['paymentProcessor']:
                filteredTips = filteredTips[filteredTips['Payment Processor'].isin(st.session_state['paymentProcessor'])]
            if  'Amount' in filteredTips and 'amountFilterMin' in st.session_state and 'amountFilterMax' in st.session_state:
                filteredTips = filteredTips[
                    (filteredTips['Amount'] >= st.session_state['amountFilterMin']) &
                    (filteredTips['Amount'] <= st.session_state['amountFilterMax'])
                ]

            return filteredTips
        
        filteredTips = setFilters()        

        def tipsGroupBy(tips, timeInterval):
            groupedTips = tips.groupby(timeInterval).agg({
                'Amount': 'sum',
                'companyPartner': 'count'
            }).reset_index().rename(columns={'Amount': 'Sum of amount', 'companyPartner': 'Count'})

            return groupedTips
        
        if st.session_state['timeInterval'] == 'Hour':
            groupedTips = tipsGroupBy(filteredTips, 'hour')
        if st.session_state['timeInterval'] == 'Week day':
            groupedTips = tipsGroupBy(filteredTips, 'weekday')
        if st.session_state['timeInterval'] == 'Day':
            groupedTips = tipsGroupBy(filteredTips, 'day')
        if st.session_state['timeInterval'] == 'Week':
            groupedTips = tipsGroupBy(filteredTips, 'weekNumber')
        elif st.session_state['timeInterval'] == 'Month':
            groupedTips = tipsGroupBy(filteredTips, 'month')
        elif st.session_state['timeInterval'] == 'Year':
            groupedTips = tipsGroupBy(filteredTips, 'year')  # TO OPTIMIZE THIS

        if st.button('Clear Filters'):
            for setting in defaultInputs.keys():
                st.session_state[setting] = defaultInputs[setting]
            st.experimental_rerun()

        st.header('Chart')

        graph = px.bar(groupedTips, x=groupedTips.columns[0], y='Sum of amount',
                                title='Count',
                                color_discrete_sequence=['green'],
                        )
        
        graph.update_traces(
            texttemplate='%{y:․0f}',
            textposition='outside',
            hovertemplate='<b>Week Number:</b> %{x}<br><b>Sum of Amount:</b> %{y}<extra></extra>',
            hoverlabel=dict(
                bgcolor='black',
                font_size=15
                # font_family='Rockwell'
            )
        )

        graph.update_layout({
            'plot_bgcolor': 'rgba(0, 0, 0, 0)',
            'paper_bgcolor': 'rgba(0, 0, 0, 0)',
            'font': {'color': 'white'},  # Change font color to white
            'width': 1200,  # Set the width
            'height': 420,  # Set the height
        })

        click_event = plotly_events(graph)

        if click_event:
            week_num = click_event[0]['x']
            filtered_data = tips[tips['weekNumber'] == week_num]
            st.write(f'Transactions for week {week_num}')
            # selectedColumns = ['Company', 'Partner', 'Date', 'Amount', 'PaymentProcessor', 'ggPayer']
            st.dataframe(filtered_data)
               
    else:
        st.write("import data about ggTips product for analyze")
    
    authenticator.logout()

elif st.session_state['authentication_status'] == False:
    st.error('Username/password is incorrect')
    
elif st.session_state['authentication_status'] == None:
    st.warning('Please enter your username and password')


    
