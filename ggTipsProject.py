import os
import pandas as pd
import streamlit as st
import altair as alt
from data.ggTipsData import load_data, uploadFilesPath
from ggtipsconfig import login  # Удалите импорт formatTimeIntervals из ggtipsconfig, если он определён в основном коде
import folium
from streamlit_folium import folium_static
import calendar

st.set_page_config(layout='wide')

def formatTimeIntervals(df, time_interval):
    if time_interval == 'Weekday':
        # Преобразуем числовой день недели в его название
        df['Week day'] = pd.to_datetime(df['Period']).dt.weekday
        df['Week day'] = pd.Categorical(
            df['Week day'].apply(lambda x: calendar.day_name[x]),
            categories=list(calendar.day_name),
            ordered=True
        )
    elif time_interval == 'Day':
        df['Period'] = pd.to_datetime(df['Period']).dt.strftime('%Y-%m-%d')
    elif time_interval == 'Hour':
        df['Period'] = pd.to_datetime(df['Period']).dt.strftime('%Y-%m-%d %H:00')
    elif time_interval == 'All':
        df['Period'] = pd.to_datetime(df['Period']).dt.strftime('%Y-%m-%d')
    elif time_interval == 'Custom day':
        df['Period'] = pd.to_datetime(df['Period']).dt.floor(f'{df["Custom"].iloc[0]}D')
    # Добавьте другие интервалы по необходимости
    return df

def customInterval(df, days):
    df['Custom'] = df['Date'] - pd.to_timedelta(df['Date'].dt.dayofyear % days, unit='d')
    return df

authenticator = login()

if st.session_state['authentication_status']:
    # Настройки боковой панели
    with st.sidebar:

        st.header('Settings')

        if st.session_state.get('demo_mode', False):
            demo_file_path = 'data/randomData/randomggTipsData.xlsx'
            data = load_data(file_path=demo_file_path)
            st.markdown("<h2 style='text-align: center; color: white;'>You are working in demo mode.<br> Import of new files is not available..</h2>", unsafe_allow_html=True)
        else:
            data = load_data()
            
            with st.expander('Import new data', data['tips'].empty):
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
                
                importedFilesDetails = st.checkbox("Imported Files details")
                
                if importedFilesDetails and st.session_state['uploadedFiles']:
                    for file in st.session_state['uploadedFiles']:
                        st.write(f"File: {os.path.basename(file)}")
                        st.write(f"Size: {os.path.getsize(file) / 1024:.2f} KB")
                        if file.endswith('.xlsx'):
                            df = pd.read_excel(file)
                        else:
                            df = pd.read_csv(file)
                        st.write(f"Columns: {', '.join(df.columns)}")
                        st.write(f"Number of rows: {len(df)}")
                        st.write("---")

                clearFolderButtonClicked = st.button("Delete all files", key="clearFolderButton")

                if clearFolderButtonClicked:
                    # Обновляем состояние до удаления файлов
                    st.session_state['uploadedFiles'] = []
                    for file in os.listdir(uploadFilesPath):
                        file_path = os.path.join(uploadFilesPath, file)
                        if os.path.isfile(file_path):
                            try:
                                os.remove(file_path)
                                st.success("Imported data cleared")
                            except PermissionError as e:
                                st.error(f"Failed to delete {file_path}: {e}")
                            except Exception as e:
                                st.error(f"Unexpected error when deleting {file_path}: {e}")

        companies = data['companies']
        tips = data['tips']
        if 'Amount' in tips.columns:
            tips = tips[tips['Amount'] > 100]
        ggTeammates = data['ggTeammates']
        defaultInputs = data['defaultInputs']

        for setting in defaultInputs.keys():
            if setting not in st.session_state:
                st.session_state[setting] = defaultInputs[setting]

        filteredTips = tips.copy()
        filteredCompanies = companies.copy()

        if not tips.empty:
            with st.expander('ggTips filters', True):

                options = {
                    'companiesOptions': list(tips['Company'].unique()) if 'Company' in tips else ['All'],
                    'partnersOptions': list(tips['Partner'].unique()) if 'Partner' in tips else ['All'],
                    'paymentProcessorOptions': list(tips['Payment processor'].dropna().unique()) if 'Payment processor' in tips else ['All'],
                    'statusOptions': list(tips['Status'].unique()) if 'Status' in tips else ['All'],
                    'ggPayeersOptions': ['All', 'Without gg teammates', 'Only gg teammates']
                }
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.multiselect('Status', options['statusOptions'], key='Status')
                
                with col2:    
                    date_range = st.date_input("Select date range", [])
                    
                    if date_range:
                        if len(date_range) != 2:
                            st.warning("Please select a start and end date.")
                        else:
                            start_date, end_date = date_range
                            filteredTips = filteredTips[(filteredTips['Date'] >= pd.to_datetime(start_date)) & (filteredTips['Date'] <= pd.to_datetime(end_date))]

                col1, col2 = st.columns(2)
                    
                with col1:
                    if st.session_state.get('ggPayeers') not in options['ggPayeersOptions']:
                        st.session_state['ggPayeers'] = 'All'
                        
                    st.selectbox('ggPayers', options['ggPayeersOptions'], key='ggPayeers')

                with col2:
                    st.multiselect('Payment Processor', options['paymentProcessorOptions'], key='paymentProcessor')

                col1, col2 = st.columns(2)

                with col1:
                    st.number_input('Min amount', value=st.session_state['amountFilterMin'], step=1000, min_value=0, max_value=50000, key='amountFilterMin')

                with col2:
                    st.number_input('Max amount', value=st.session_state['amountFilterMax'], step=1000, min_value=0, max_value=50000, key='amountFilterMax')
                    
                timeIntervalOptions = ['Week', 'Month', 'Year', 'Week day', 'Day', 'Hour', 'Custom day', 'All']

                if 'timeInterval' in st.session_state: 
                    if st.session_state['timeInterval'] != 'Custom day':
                        st.selectbox('Time interval', timeIntervalOptions, key='timeInterval')
                    else:
                        col1, col2 = st.columns(2)

                        with col1:
                            st.selectbox('Time interval', timeIntervalOptions, index=timeIntervalOptions.index("Custom day"), key='timeInterval')

                        with col2:
                            st.number_input('Custom', value=10, step=1, min_value=1, key='customInterval')

                    if st.session_state['timeInterval'] == 'Custom day':
                        custom_days = st.session_state.get('customInterval', 10)
                        filteredTips = customInterval(filteredTips, custom_days)
                        time_interval = 'Custom day'
                    else:
                        time_interval = st.session_state['timeInterval']
                else:
                    st.write("Problem with time Interval")
        
            with st.expander('**Graph values**', True):
                
                sum_type = st.selectbox('Sum Chart', ['Column', 'Line', 'Area', 'None'])
                count_type = st.selectbox('Count Chart', ['Line', 'Column', 'Area', 'None'])
                scope_type = st.selectbox('Scope Chart', ['Line', 'Column', 'Area', 'None'])

            with st.expander('**Graph Customize**'):
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    sum_color = st.color_picker('Sum Color', '#00FF00')
                with col2:
                    count_color = st.color_picker('Count Color', '#0000FF')
                with col3:
                    scope_color = st.color_picker('Scope Color', '#A020F0')
                    
                text_color = st.color_picker('Text Color', '#FFFFFF')
                column_size = st.slider('Column Size', 3, 30, 15)
                reset_button = st.button('Reset Settings')

        if 'Working status' in filteredCompanies:
            filteredCompanies = filteredCompanies[filteredCompanies['Working status']]

        os.makedirs(uploadFilesPath, exist_ok=True)
        
        if st.session_state.get('authentication_status'):
            if 'demo_mode' in st.session_state and st.session_state['demo_mode']:
                # Логаут в демо-режиме
                if st.button('Logout'):
                    # Сброс состояния для демо-версии
                    st.session_state['authentication_status'] = False
                    st.session_state['demo_mode'] = False
                    st.experimental_rerun()  # Перезагружаем страницу после выхода
            else:
                if 'authenticator' in globals() and authenticator is not None:
                    authenticator.logout('Logout', 'sidebar')
                else:
                    if st.button('Logout'):
                        st.session_state['authentication_status'] = False
                        st.experimental_rerun()
        else:
            st.warning("Please enter your username and password")

    if not tips.empty:
            
        # Словарь для хранения информации о фильтрах
        filters = {
            'selectedCompanies': ('Company', st.session_state.get('selectedCompanies', [])),
            'selectedPartners': ('Partner', st.session_state.get('selectedPartners', [])),
            'Status': ('Status', st.session_state.get('Status', [])),
            'paymentProcessor': ('Payment processor', st.session_state.get('paymentProcessor', [])),
        }

        # Применение фильтров
        for key, (column, values) in filters.items():
            if values:  # Проверяем, что фильтр не пуст
                filteredTips = filteredTips[filteredTips[column].isin(values)]
                if key == 'selectedCompanies':
                    filteredCompanies = filteredCompanies[filteredCompanies['Company'].isin(values)]

        # Фильтрация по Amount
        if 'amountFilterMin' in st.session_state and 'amountFilterMax' in st.session_state:
            filteredTips = filteredTips[
                (filteredTips['Amount'] >= st.session_state['amountFilterMin']) &
                (filteredTips['Amount'] <= st.session_state['amountFilterMax'])
            ]

        # Фильтрация по ggPayeers
        if st.session_state.get('ggPayeers') and 'ggPayer' in filteredTips.columns:
            if st.session_state['ggPayeers'] == 'Without gg teammates':
                filteredTips = filteredTips[~filteredTips['ggPayer'].isin(ggTeammates['id'])]
            elif st.session_state['ggPayeers'] == 'Only gg teammates':
                filteredTips = filteredTips[filteredTips['ggPayer'].isin(ggTeammates['id'])]

        # Применение группировки по интервалу времени

        if time_interval == 'All':
            groupedTips = filteredTips.groupby(filteredTips['Date'].dt.date).agg({
                'Amount': 'sum',
                'uuid': 'count',
            }).reset_index().rename(columns={'Date': 'Period', 'uuid': 'Count', 'Amount': 'Amount'})
        elif time_interval == 'Day':
            groupedTips = filteredTips.groupby(filteredTips['Date'].dt.date).agg({
                'Amount': 'sum',
                'uuid': 'count',
            }).reset_index().rename(columns={'Date': 'Period', 'uuid': 'Count', 'Amount': 'Amount'})
        elif time_interval == 'Hour':
            groupedTips = filteredTips.groupby(filteredTips['Date'].dt.hour).agg({
                'Amount': 'sum',
                'uuid': 'count',
            }).reset_index().rename(columns={'Date': 'Period', 'uuid': 'Count', 'Amount': 'Amount'})
        elif time_interval == 'Weekday':
            # Убедитесь, что столбец 'Week day' существует
            if 'Week day' not in filteredTips.columns:
                filteredTips['Week day'] = filteredTips['Date'].dt.weekday
            groupedTips = filteredTips.groupby('Week day').agg({
                'Amount': 'sum',
                'uuid': 'count',
            }).reset_index().rename(columns={'uuid': 'Count', 'Amount': 'Amount'})
        else:
            # Существующая логика для других интервалов
            groupedTips = filteredTips.groupby(time_interval).agg({
                'Amount': 'sum',
                'uuid': 'count',
                'WeekStart': 'max',
                'WeekEnd': 'max'
            }).reset_index().rename(columns={'uuid': 'Count', 'Amount': 'Amount'})
            
            if time_interval in ['Week', 'Month', 'Year']:
                groupedTips['Period'] = groupedTips['WeekStart']  # Используем только начальную дату
            else:
                groupedTips['Period'] = groupedTips[time_interval].astype(str)

        # Форматирование интервалов
        groupedTips = formatTimeIntervals(groupedTips, time_interval)
                        
        with st.expander('stats'):
            
            # st.write( data['oneAverageTip'])
            
            sumTips = int(groupedTips['Amount'].sum())
            countTips = groupedTips['Count'].sum()
            connectionDays = filteredCompanies['Days'].max()
            companiesCount = int(companies.groupby('HELPERcompanyName')['Working status'].max().sum())
            branchesCount = companies['Working status'].sum() 

            if countTips !=0:
                averageTip = round(sumTips / countTips)
            else:
                averageTip = 0
            
            if pd.notna(connectionDays) and connectionDays != 0:
                oneDayTip = round(sumTips / connectionDays)
                timeIntervalTip = round(connectionDays / countTips, 1)
            else:
                oneDayTip = 0
                timeIntervalTip = '-'
                
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write('Companies: ', companiesCount)

            with col2:
                st.write('Branches: ', branchesCount)
                
            # with col3:
            #     st.write('Partners', partnersCount)
                            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write('Amount: ', sumTips)

            with col2:
                st.write('Count: ', countTips)
                
            with col3:
                st.write('One average tip', averageTip)
                
            # st.write(oneAver)
                
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write('Tip time interval days: ', timeIntervalTip)
                
            with col2:
                st.write('Daily tips amount: ', oneDayTip)
                
            with col3:
                st.write('Activ days: ', connectionDays)

        median_all_data = tips.groupby('Company')['Amount'].median().reset_index()
        median_all_data.columns = ['Company', 'Median_MAD']

            # Создание графика с помощью Altair
        AllTipsTab, CompaniesTipsTab, CompaniesActivactions, CompanyConnectionsTab, TablesTab, MapTab, UsersTab = st.tabs(['ggTips', 'Top companies', 'Companies activations', 'Company connections', 'Tables', 'Map', 'Users'])
        
        with AllTipsTab: 

            col1, col2 = st.columns(2)
                    
            with col1:
                st.multiselect('Select companies', options['companiesOptions'], key='selectedCompanies')

            with col2:
                st.multiselect('Select partners', options['partnersOptions'], key='selectedPartners')

            with st.container():
                with st.expander('Sorting'):
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        sort_column = st.selectbox("Select column for sorting", [ "Time", "Amount", "Count"], key="sort_col_all")
                    with col2:
                        sort_direction = st.selectbox("Select sort direction", ["Descending", 'Ascending'], key="sort_dir_all")

                    # Если выбрано сортировать по времени, выполняем сортировку по нужному интервалу времени
                    if sort_column == "Time":
                        # Преобразуем колонку времени в datetime, если это возможно
                        if time_interval in ['Week', 'Month', 'Year']:
                            groupedTips['Period'] = pd.to_datetime(groupedTips['Period'])  # Для недель, месяцев и годов
                        else:
                            groupedTips['Period'] = pd.to_datetime(groupedTips['Period'])  # Для дней или кастомных интервалов

                        # Сортируем данные по времени
                        groupedTips = groupedTips.sort_values(by='Period', ascending=(sort_direction == 'Ascending'))
                        x_axis_type = 'T'  # Тип данных для оси x - временной
                    else:
                        # Если сортировка по другим колонкам (например, Amount или Count)
                        groupedTips = groupedTips.sort_values(by=sort_column, ascending=(sort_direction == 'Ascending'))
                        x_axis_type = 'O'  # Тип данных для оси x - категориальный (номинальный)
                
                # Построение графика
                if sum_type != 'None' or count_type != 'None':
                    layers = []
                    
                    if time_interval == 'Hour':
                        x_axis = alt.X('Period:O',  # Категориальный тип
                                    axis=alt.Axis(title='Hour of Day', titleFontSize=14),
                                    sort=sorted(groupedTips['Period'].unique()))
                    else:
                        x_axis = alt.X('Period:T' if x_axis_type == 'T' else 'Period:N',  # Указываем тип оси динамически: T для времени, O для других колонок
                            axis=alt.Axis(title=f'{time_interval}', titleFontSize=14),
                            sort='x' if x_axis_type == 'T' else groupedTips['Period'].tolist())

                    if sum_type != 'None':
                        if sum_type == 'Column':
                            sum_layer = alt.Chart(groupedTips).mark_bar(
                                size=column_size,
                                color=sum_color,
                                stroke='white',
                                strokeWidth=1
                            )
                        elif sum_type == 'Line':
                            sum_layer = alt.Chart(groupedTips).mark_line(color=sum_color)
                        elif sum_type == 'Area':
                            sum_layer = alt.Chart(groupedTips).mark_area(color=sum_color)

                        sum_layer = sum_layer.encode(
                            x=x_axis,
                            y=alt.Y('Amount:Q', axis=alt.Axis(title='Sum of Tips')),
                            tooltip=['Period', 'Amount', 'Count']
                        )
                        layers.append(sum_layer)

                    if count_type != 'None':
                        if count_type == 'Column':
                            count_layer = alt.Chart(groupedTips).mark_bar(
                                size=column_size,
                                color=count_color,
                                stroke='white',
                                strokeWidth=2
                            )
                        elif count_type == 'Line':
                            count_layer = alt.Chart(groupedTips).mark_line(color=count_color,  size=4)
                        elif count_type == 'Area':
                            count_layer = alt.Chart(groupedTips).mark_area(color=count_color)

                        count_layer = count_layer.encode(
                            x=x_axis,
                            y=alt.Y('Count:Q', axis=alt.Axis(title='Count of Transactions', titleFontSize=14)),
                            tooltip=['Period', 'Amount', 'Count']
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

                    if 'groupedTips' in locals():
                        with st.expander('Table', True):
                            st.write(groupedTips[['Week', 'Amount', 'WeekStart', 'WeekEnd']])

        with CompaniesTipsTab:
                
            companiesGroupedTips = filteredTips[filteredTips['Status'] == 'finished'].groupby('Company').agg({
                'Amount': 'sum',
                'uuid': 'count',
                'WeekStart': 'max',
                'WeekEnd': 'max'
            }).reset_index().rename(columns={'uuid': 'Count', 'Amount': 'Amount'})
            
            # companiesGroupedTips['Median'] = tips.groupby('Company')['Amount'].median().reset_index(drop=True)
            
        # Присоединяем колонку с медианой к отфильтрованным данным
            companiesGroupedTips = companiesGroupedTips.merge(median_all_data, on='Company', how='left')
            
            companiesGroupedTips['Scope'] = companiesGroupedTips.apply(
                lambda row: round((row['Amount'] / row['Median_MAD']) + (row['Amount'] / data['oneAverageTip']), 1) 
                if pd.notna(row['Median_MAD']) and row['Median_MAD'] != 0 else 0, axis=1)
            companiesGroupedTips['Scope'] = companiesGroupedTips['Scope'].fillna(0)     
            
            lastTransaction = tips.groupby('Company')['Date'].max().reset_index()
            lastTransaction.columns = ['Company', 'Last transaction']
            lastTransaction['Last Transaction'] = lastTransaction['Last transaction'].fillna(pd.Timestamp.max)

            companiesGroupedTips = companiesGroupedTips.merge(lastTransaction, on='Company', how='left')
            
            today = pd.to_datetime('today')
            companiesGroupedTips['Days since last transaction'] = (today - companiesGroupedTips['Last transaction']).dt.days
            
            with st.container():
                
                with st.expander('Config'):
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        sort_column_companies = st.selectbox("Select column for sorting", ["Scope", "Amount", "Count"], key="sort_col_companies")
                    
                    with col2:
                        sort_direction_companies = st.selectbox("Select sort direction", ["Descending", "Ascending"], key="sort_dir_companies")

                    if sort_direction_companies == "Ascending":
                        companiesGroupedTips = companiesGroupedTips.sort_values(by=sort_column_companies, ascending=True)
                    else:
                        companiesGroupedTips = companiesGroupedTips.sort_values(by=sort_column_companies, ascending=False)
                        
                    topN = st.number_input('Top N companies', value=15, step=1, min_value=1, key='topN')
                    allcompaniesGroupedTips = companiesGroupedTips.copy()
                    companiesGroupedTips = companiesGroupedTips.head(topN)
                
                
            if sum_type != 'None' or count_type != 'None' or scope_type != 'None':
                layers = []
                
                # Ось X для компаний (категориальная)
                x_axis = alt.X('Company:N', axis=alt.Axis(title='Company Name', labelOverlap=True), sort=companiesGroupedTips['Company'].tolist())

                if sum_type != 'None':
                    if sum_type == 'Column':
                        sum_layer = alt.Chart(companiesGroupedTips).mark_bar(
                            size=column_size,  
                            color=sum_color,
                            stroke='white',  
                            strokeWidth=1  
                        )
                    elif sum_type == 'Line':
                        sum_layer = alt.Chart(companiesGroupedTips).mark_line(color=sum_color)
                    elif sum_type == 'Area':
                        sum_layer = alt.Chart(companiesGroupedTips).mark_area(color=sum_color)

                    sum_layer = sum_layer.encode(
                        x=x_axis,
                        y=alt.Y('Amount:Q', axis=alt.Axis(title='Sum of Tips', titleFontSize=14), scale=alt.Scale(domain=[0, companiesGroupedTips['Amount'].max()])),  # Отдельная ось для Amount
                        tooltip=['Company', 'Amount', 'Count', 'Scope']
                    )
                    layers.append(sum_layer)

                if count_type != 'None':
                    if count_type == 'Column':
                        count_layer = alt.Chart(companiesGroupedTips).mark_bar(
                            size=column_size,  
                            color=count_color,
                            stroke='white',  
                            strokeWidth=1
                        )
                    elif count_type == 'Line':
                        count_layer = alt.Chart(companiesGroupedTips).mark_line(color=count_color)
                    elif count_type == 'Area':
                        count_layer = alt.Chart(companiesGroupedTips).mark_area(color=count_color)

                    count_layer = count_layer.encode(
                        x=x_axis,
                        y=alt.Y('Count:Q', axis=alt.Axis(title='Count & Scope', titleFontSize=14), scale=alt.Scale(domain=[0, companiesGroupedTips['Count'].max()])),  # Общая ось для Count и Scope
                        tooltip=['Company', 'Amount', 'Count', 'Scope']
                    )
                    layers.append(count_layer)
                    
                if scope_type != 'None':
                    if scope_type == 'Column':
                        scope_layer = alt.Chart(companiesGroupedTips).mark_bar(
                            size=column_size,
                            color=scope_color,
                            stroke='white',
                            strokeWidth=1
                        )
                    elif scope_type == 'Line':
                        scope_layer = alt.Chart(companiesGroupedTips).mark_line(color=scope_color, size=3)
                    elif scope_type == 'Area':
                        scope_layer = alt.Chart(companiesGroupedTips).mark_area(color=scope_color)

                    scope_layer = scope_layer.encode(
                        x=x_axis,
                        y=alt.Y('Scope:Q', axis=alt.Axis(title='Count & Scope', titleFontSize=14), scale=alt.Scale(domain=[0, companiesGroupedTips['Scope'].max()])),  # Совместная ось Y с Count
                        tooltip=['Company', 'Amount', 'Count', 'Scope']
                    )
                    layers.append(scope_layer)

                # Комбинирование графиков с разными осями Y
                chart = alt.layer(*layers).resolve_scale(
                    y='independent'  # Разделяем оси Y
                ).configure_axis(
                    labelColor='white',
                    titleColor='white'
                )
                st.altair_chart(chart, use_container_width=True)

                if 'companiesGroupedTips' in locals():
                    with st.expander('Table', True):
                        mode = st.selectbox('Mode', ['All', 'Top N'])
                        columns = ['Company', 'Amount', 'Count', 'Scope', 'Median_MAD', 'Days since last transaction']
                        st.write(allcompaniesGroupedTips[columns]) if mode=='All' else st.write(companiesGroupedTips[columns])
                    
        with CompaniesActivactions:

            cleverTips = tips.copy()

            if 'format_data' in st.session_state:
                if st.session_state['format_data'] == 'Half':
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        format_option = st.selectbox('Different format', ('Numbers', 'Percentage'))
                
                    with col2:
                        format_data_period = st.selectbox('Period format', ('Half', 'Custom'), key='format_data')
                else:
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        format_option = st.selectbox('Different format', ('Numbers', 'Percentage'))
                
                    with col2:
                        format_data_period = st.selectbox('Period format', ('Half', 'Custom'), key='format_data')

                    with col3:
                        period = st.number_input('Period', value=7, step=1, min_value=1, key='PeriodValue')
            else:
                col1, col2, col3 = st.columns(3)

                with col1:
                    format_option = st.selectbox('Different format', ('Numbers', 'Percentage'))
            
                with col2:
                    format_data_period = st.selectbox('Period format', ('Half', 'Custom'), key='format_data')

                with col3:
                    period = st.number_input('Period', value=7, step=1, min_value=1, key='PeriodValue')

            # Подготовка DataFrame
            companyActiveDays = companies.groupby('Company')['Days'].max().reset_index()
            companyActiveDays['Company_cleaned'] = companyActiveDays['Company'].str.lower().str.replace(' ', '')
            companyActiveDays = companyActiveDays[['Company_cleaned', 'Days']]

            if format_data_period == 'Custom':
                companyActiveDays = companyActiveDays[companyActiveDays['Days'] > period]

            # Подготовка DataFrame 'cleverTips'
            cleverTips = cleverTips.reset_index(drop=True)

            if 'ggPayer' in cleverTips.columns:
                cleverTips = cleverTips[~cleverTips['ggPayer'].isin(ggTeammates['id'])]

            if 'Status' in cleverTips.columns:
                cleverTips = cleverTips[cleverTips['Status'] == 'finished']

            # Создание 'Company_cleaned' в 'cleverTips'
            cleverTips['Company_cleaned'] = cleverTips['Company'].str.lower().str.replace(' ', '')

            # Слияние с 'companyActiveDays'
            cleverTips = cleverTips.merge(
                companyActiveDays,
                on='Company_cleaned',
                how='left'
            )
            cleverTips['Date'] = pd.to_datetime(cleverTips['Date'])

            today = pd.to_datetime('today')

            if format_data_period == 'Half':
                # Добавление столбца 'date_threshold'
                cleverTips['date_threshold'] = today - pd.to_timedelta(cleverTips['Days'] / 2, unit='D')
                
                # Первый период
                totalPeriodTips = cleverTips[cleverTips['Date'] < cleverTips['date_threshold']]
                
                # Второй период
                lastPeriodTips = cleverTips[cleverTips['Date'] >= cleverTips['date_threshold']]
            else:
                # Заданный период
                period_timedelta = pd.Timedelta(days=period)
                totalPeriodTips = cleverTips[
                    (cleverTips['Date'] < today - period_timedelta)
                ]
                lastPeriodTips = cleverTips[
                    (cleverTips['Date'] >= today - period_timedelta)
                ]

            # Группировка 'totalPeriodTips'
            totalPeriodScopes = totalPeriodTips.groupby('Company').agg({
                'Amount': 'sum',
                'uuid': 'count'
            }).reset_index().rename(columns={'uuid': 'Count', 'Amount': 'Amount'})

            totalPeriodScopes['Company_cleaned'] = totalPeriodScopes['Company'].str.lower().str.replace(' ', '')


            # Слияние с 'median_all_data'
            totalPeriodScopes = totalPeriodScopes.merge(
                median_all_data[['Company', 'Median_MAD']],
                on='Company',
                how='left'
            )

            # Слияние с 'companyActiveDays'
            totalPeriodScopes = totalPeriodScopes.merge(
                companyActiveDays,
                on='Company_cleaned',
                how='left'
            )

            # Удаление 'Company_cleaned'
            totalPeriodScopes.drop(columns=['Company_cleaned'], inplace=True)

            # Группировка 'lastPeriodTips'
            lastPeriodTips = lastPeriodTips.groupby('Company').agg({
                'Amount': 'sum',
                'uuid': 'count'
            }).reset_index().rename(columns={'uuid': 'Count', 'Amount': 'Amount'})

            lastPeriodTips['Company_cleaned'] = lastPeriodTips['Company'].str.lower().str.replace(' ', '')

            # Слияние с 'median_all_data'
            lastPeriodTips = lastPeriodTips.merge(
                median_all_data[['Company', 'Median_MAD']],
                on='Company',
                how='left'
            )

            # Слияние с 'companyActiveDays'
            lastPeriodTips = lastPeriodTips.merge(
                companyActiveDays,
                on='Company_cleaned',
                how='left'
            )

            # Удаление 'Company_cleaned'
            lastPeriodTips.drop(columns=['Company_cleaned'], inplace=True)

            def calculate_scope(row, period_length):
                if pd.notna(row['Median_MAD']) and row['Median_MAD'] != 0 and period_length > 0 and row['Days'] > period_length:
                    return round(
                        (
                            (row['Amount'] / row['Median_MAD']) +
                            (row['Amount'] / data['oneAverageTip'])
                        ) / period_length,
                        1
                    )
                else:
                    return 0
                
            if format_data_period == "Custom":
                totalPeriodScopes['Scope'] = totalPeriodScopes.apply(
                    lambda row: calculate_scope(row, row['Days'] - period),
                    axis=1
                )
            else:
                totalPeriodScopes['Scope'] = totalPeriodScopes.apply(
                    lambda row: calculate_scope(row, row['Days'] / 2),
                    axis=1
                )

            # Расчёт 'Scope' для последнего периода
            if format_data_period == "Custom":
                lastPeriodTips['Scope'] = lastPeriodTips.apply(
                    lambda row: calculate_scope(row, period),
                    axis=1
                )
            else:
                lastPeriodTips['Scope'] = lastPeriodTips.apply(
                    lambda row: calculate_scope(row, row['Days'] / 2),
                    axis=1
                )

            # Объединение данных
            mergedScopes = pd.merge(
                totalPeriodScopes[['Company', 'Scope']],
                lastPeriodTips[['Company', 'Scope']],
                on='Company',
                how='outer',
                suffixes=('_first_period', '_second_period')
            )

            # Заполнение отсутствующих значений
            mergedScopes.fillna(0, inplace=True)

            # Вычисление differentScope
            mergedScopes['differentScopeNumbers'] = mergedScopes['Scope_second_period'] - mergedScopes['Scope_first_period'] 

            def calculate_percentage(row):
                if row['Scope_first_period'] != 0:
                    return ((row['Scope_second_period'] - row['Scope_first_period']) / row['Scope_first_period']) * 100
                else:
                    if row['Scope_second_period'] != 0:
                        return 300
                    else:
                        return 0
            mergedScopes['differentScopePercentage'] = mergedScopes.apply(calculate_percentage, axis=1)

            # Ограничение значений и установка цветов
            def set_color(value):
                if value >= 300:
                    return 'blue'
                elif value >= 0:
                    return 'green'
                elif value > (-100):
                    return 'orange'
                else:
                    return 'red'

            mergedScopes['color'] = mergedScopes['differentScopePercentage'].apply(set_color)

            mergedScopes['differentScopePercentageAtChar'] = mergedScopes['differentScopePercentage'].apply(
                lambda x: x if x <= 300 else 300
            )

            # Сортировка данных
            differentScopeFormat = 'differentScopeNumbers' if format_option == 'Numbers' else 'differentScopePercentageAtChar'
            differentScopeFormatWihoutLimit = 'differentScopeNumbers' if format_option == 'Numbers' else 'differentScopePercentage'
            
            mergedScopes = mergedScopes.sort_values(by=f'{differentScopeFormatWihoutLimit}', ascending=False)

            chart_data = mergedScopes[
                (mergedScopes[differentScopeFormat] != 0) |
                (
                    (mergedScopes[differentScopeFormat] == 0) &
                    (
                        (mergedScopes['Scope_first_period'] != 0) |
                        (mergedScopes['Scope_second_period'] != 0)
                    )
                )
            ]

            # Данные для таблицы
            table_data = mergedScopes[
                (mergedScopes['Scope_first_period'] == 0) &
                (mergedScopes['Scope_second_period'] == 0)
            ]

            # Убедимся, что differentScope не содержит NaN
            chart_data[differentScopeFormat] = chart_data[differentScopeFormat].fillna(0)

            # Список компаний для оси X
            company_list = chart_data['Company'].tolist()

            # Настройка оси X
            x_axis = alt.X('Company:N', sort=company_list, axis=alt.Axis(
                title='Company',
                labelFontSize=10,      # Уменьшение размера шрифта меток
                labelOverlap='greedy'  # Предотвращение перекрытия меток
            ))

            # Определение минимального и максимального значения для оси Y
            min_y = chart_data[differentScopeFormat].min()
            max_y = chart_data[differentScopeFormat].max()

            # Добавление диапазона, если min_y и max_y равны
            if min_y == max_y:
                min_y -= 1
                max_y += 1

            # Настройка оси Y
            y_axis = alt.Y(f'{differentScopeFormat}:Q', 
                        axis=alt.Axis(title='Different Scope'),
                        scale=alt.Scale(domain=[min_y, max_y]))

            # Базовый график
            base_chart = alt.Chart(chart_data).encode(
                x=x_axis,
                tooltip=['Company', differentScopeFormatWihoutLimit, 'Scope_first_period', 'Scope_second_period']
            )

            # Столбцы для differentScope != 0
            bar_chart = base_chart.transform_filter(
                alt.datum.differentScopeNumbers != 0
            ).mark_bar().encode(
                y=y_axis,
                color=alt.Color('color:N', scale=None, legend=None)
            )

            # Точки для differentScope == 0
            zero_chart = base_chart.transform_filter(
                alt.datum.differentScopeNumbers == 0
            ).mark_point(size=150, color='blue', stroke='black', strokeWidth=2).encode(
                y=f'{differentScopeFormat}:Q'
            )

            # Комбинирование графиков
            final_chart = alt.layer(bar_chart, zero_chart).resolve_scale(
                y='shared'
            )

            # Слияние с 'companyActiveDays'
            mergedScopes['Company_cleaned'] = mergedScopes['Company'].str.lower().str.replace(' ', '')
            mergedScopesWithDays = mergedScopes.merge(
                companyActiveDays[['Company_cleaned', 'Days']],
                on='Company_cleaned',
                how='left'
            )

            with st.expander('stats'):
                growCompaniesCount = mergedScopesWithDays[mergedScopesWithDays['differentScopeNumbers'] > 0]['Company'].count()
                decreaseCompaniesCount = mergedScopesWithDays[mergedScopesWithDays['differentScopeNumbers'] < 0]['Company'].count()
                sameStatusCompaniesCount = mergedScopesWithDays[mergedScopesWithDays['differentScopeNumbers'] == 0]['Company'].count()
                activeCompanies = mergedScopesWithDays[mergedScopesWithDays['Scope_second_period'] > 0]['Company'].count()
                passiveCompanies = mergedScopesWithDays[mergedScopesWithDays['Scope_second_period'] == 0]['Company'].count()

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write('Growth companies: ', growCompaniesCount)
                
                with col2:
                    st.write('Decrease companies: ', decreaseCompaniesCount)

                with col3:
                    st.write('Same status companies: ', sameStatusCompaniesCount)

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write('At last one tip: ', activeCompanies, 'companies')

                with col2:
                    st.write('Zero tip: ', passiveCompanies, 'companies')
            
            # Отображение графика
            st.altair_chart(final_chart, use_container_width=True)

            # Отображение таблицы
            if format_data_period == 'Custom':
                st.dataframe(mergedScopesWithDays.loc[mergedScopesWithDays['Days'] > period, ['Company', 'Scope_first_period', 'Scope_second_period', 'differentScopeNumbers', 'differentScopePercentage', 'Days']])
            else:
                st.dataframe(mergedScopesWithDays[['Company', 'Scope_first_period', 'Scope_second_period', 'differentScopeNumbers', 'differentScopePercentage', 'Days']])

        with CompanyConnectionsTab:
            if not date_range:
                start_date = pd.to_datetime('2024-01-01')
                end_date = pd.to_datetime('today')

            # Преобразование колонок Start и End в datetime
            companies['Start'] = pd.to_datetime(companies['Start'], errors='coerce')
            companies['End'] = pd.to_datetime(companies['End'], errors='coerce')

            # Генерация диапазона дат
            date_range = pd.date_range(start=start_date, end=end_date)

            # Подсчёт активных бренчей и уникальных компаний
            active_companies_per_day = []

            for date in date_range:
                active_branches = companies[
                    (companies['Start'].notna()) & 
                    ((companies['End'].isna()) | (companies['End'] >= date)) & 
                    (companies['Start'] <= date)
                ]
                
                active_branches_count = active_branches.shape[0]
                unique_active_companies_count = active_branches['HELPERcompanyName'].nunique()
                
                active_companies_per_day.append({
                    'Date': date, 
                    'Active Branches': active_branches_count, 
                    'Active Companies': unique_active_companies_count
                })

            # Преобразование в DataFrame
            active_companies_df = pd.DataFrame(active_companies_per_day)

            # Рассчёт изменений по дням
            active_companies_df['Branches Change'] = active_companies_df['Active Branches'].diff().fillna(0)
            active_companies_df['Companies Change'] = active_companies_df['Active Companies'].diff().fillna(0)

            # Применение фильтра по timeInterval
            if st.session_state['timeInterval'] == 'Week':
                active_companies_df['Date'] = active_companies_df['Date'].dt.to_period('W').apply(lambda r: r.start_time)
            elif st.session_state['timeInterval'] == 'Month':
                active_companies_df['Date'] = active_companies_df['Date'].dt.to_period('M').apply(lambda r: r.start_time)
            elif st.session_state['timeInterval'] == 'Year':
                active_companies_df['Date'] = active_companies_df['Date'].dt.to_period('Y').apply(lambda r: r.start_time)
            elif st.session_state['timeInterval'] == 'Day':
                active_companies_df['Date'] = active_companies_df['Date'].dt.to_period('D').apply(lambda r: r.start_time)
            elif st.session_state['timeInterval'] == 'Custom day':
                custom_interval = st.session_state.get('customInterval', 10)
                active_companies_df['Date'] = active_companies_df['Date'] - pd.to_timedelta(active_companies_df['Date'].dt.dayofyear % custom_interval, unit='D')

            # Группировка данных
            grouped_data = active_companies_df.groupby('Date').agg({
                'Active Branches': 'max',
                'Active Companies': 'max',
                'Branches Change': 'sum',
                'Companies Change': 'sum'
            }).reset_index()

            # Линейные графики
            line_chart = alt.Chart(grouped_data).mark_line(color='green').encode(
                x=alt.X('Date:T', title='Date'),
                y=alt.Y('Active Branches:Q', title='Active Branches/Companies'),
                tooltip=['Date:T', 'Active Branches:Q']
            )

            companies_line_chart = alt.Chart(grouped_data).mark_line(color='blue').encode(
                x=alt.X('Date:T', title='Date'),
                y=alt.Y('Active Companies:Q', title='Active Branches/Companies'),
                tooltip=['Date:T', 'Active Companies:Q']
            )

            combined_line_chart = alt.layer(line_chart, companies_line_chart).configure_axis(
                labelColor='white',
                titleColor='white'
            )

            st.altair_chart(combined_line_chart, use_container_width=True)

            # Столбчатые графики
            bar_chart_branches = alt.Chart(grouped_data).mark_bar(color='green').encode(
                x=alt.X('Date:T', title='Date'),
                y=alt.Y('Branches Change:Q', title='Daily Change'),
                tooltip=['Date:T', 'Branches Change:Q']
            )

            bar_chart_companies = alt.Chart(grouped_data).mark_bar(color='blue').encode(
                x=alt.X('Date:T', title='Date'),
                y=alt.Y('Companies Change:Q', title='Daily Change'),
                tooltip=['Date:T', 'Companies Change:Q']
            )

            combined_bar_chart = alt.layer(bar_chart_branches, bar_chart_companies).configure_axis(
                labelColor='white',
                titleColor='white'
            )

            st.altair_chart(combined_bar_chart, use_container_width=True)

            with st.expander('Table', True):
                st.write(grouped_data)

        with MapTab:
            st.write('Companies')
            
            # Функция для разделения координат
            def split_coordinates(coord):
                if isinstance(coord, str):  # Проверяем, является ли значение строкой
                    try:
                        lat, lon = map(float, coord.split(', '))
                        return lat, lon
                    except ValueError:
                        return None, None  # Возвращаем None, если не удается преобразовать строку в числа
                else:
                    return None, None

            # Создаем базовую карту
            first_coordinate = filteredCompanies['Coordinate'].iloc[0]
            initial_lat, initial_lon = split_coordinates(first_coordinate)
            if initial_lat is not None and initial_lon is not None:
                m = folium.Map(location=[initial_lat, initial_lon], zoom_start=12)
            else:
                m = folium.Map(location=[40.1792, 44.4991], zoom_start=12)  # В случае ошибки, ставим координаты Еревана как центр

            # Добавляем маркеры для каждой компании
            for index, row in filteredCompanies.iterrows():
                lat, lon = split_coordinates(row['Coordinate'])
                if lat is not None and lon is not None:
                    folium.Marker([lat, lon], 
                                popup=f"{row['Company']} ({row['Adress']})").add_to(m)

            # Отображаем карту в Streamlit
            st.title('Map of Company Locations')
            folium_static(m)         
            
        with UsersTab:
            
            valueTypeSelectBox = st.selectbox('Value type', ['Count', 'Amount'])
            
            if valueTypeSelectBox == 'Count':
                valueType = 'count'
            else:
                valueType = 'sum'
            
            pivot_table = pd.pivot_table(
            filteredTips, 
            values='Amount',  # Используем UUID как значение для подсчета повторений
            index='ggPayer',  # Строки по пользователям
            columns='Company',  # Столбцы по компаниям
            aggfunc=valueType,  # Подсчитываем количество чаевых
            margins=True,  # Добавляем суммы по строкам и столбцам
            margins_name='Total'  # Имя для итоговых строк и столбцов
        ).fillna(0)  # Заменяем NaN на 0
            
            pivot_table.index = pivot_table.index.map(lambda x: int(x) if x!='Total' else x)

 
            st.dataframe(pivot_table)

        with TablesTab:
            
            with st.expander('All tips'):
                st.dataframe(tips)
            
            with st.expander('Filtered data'):
                st.dataframe(filteredTips)
            
            with st.expander('Companies'):
                st.dataframe(companies)

            # Интеграция iframe с SharePoint
            if not('demo_mode' in st.session_state and st.session_state['demo_mode']):
                with st.expander('<ggtips admin> excel file'):
                    st.components.v1.iframe(
                        src="https://infoggtaxi-my.sharepoint.com/personal/tigran_badalyan_team_gg/_layouts/15/Doc.aspx?sourcedoc={619709ab-e384-4781-bd49-6fecfa2a3787}&action=embedview&wdHideGridlines=True&wdHideHeaders=True&wdDownloadButton=True&wdInConfigurator=True&wdInConfigurator=True&edaebf=cc",
                        width=1000,
                        height=346,
                        scrolling=False
                    )
    else:
        st.markdown("<h2 style='text-align: center; color: white;'>Import data to get started</h2>", unsafe_allow_html=True)

elif st.session_state['authentication_status'] == False:
    st.error('Username/password is incorrect')

elif st.session_state['authentication_status'] == None:
    st.warning('Please enter your username and password')

