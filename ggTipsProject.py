import os
import pandas as pd
import streamlit as st
import altair as alt
from data.ggTipsData import load_data, uploadFilesPath
from ggtipsconfig import login, formatTimeIntervals
import folium
from streamlit_folium import folium_static


st.set_page_config(layout='wide')

authenticator = login()

def customInterval(df, days):
    df['Custom'] = df['Date'] - pd.to_timedelta(df['Date'].dt.dayofyear % days, unit='d')
    return df

if st.session_state['authentication_status']:
  
    data = load_data()
    
    companies = data['companies']
    tips = data['tips']
    defaultInputs = data['defaultInputs']
    ggTeammates = data['ggTeammates']
    
    filteredTips = tips.copy()
    filteredCompanies = companies.copy()
    if 'Working status' in filteredCompanies:
        filteredCompanies= filteredCompanies[filteredCompanies['Working status']]

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
            
        uploadedFiles = st.session_state['uploadedFiles']

        col1, col2 = st.columns(2)

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

        clearFolderButtonClicked = st.button("Delete all new files", key="clearFolderButton")

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

    st.title('ggTips')

    if 'tips' in data:
        options = {
            'companiesOptions': list(tips['Company'].unique()) if 'Company' in tips else ['All'],
            'partnersOptions': list(tips['Partner'].unique()) if 'Partner' in tips else ['All'],
            'paymentProcessorOptions': list(tips['Payment processor'].dropna().unique()) if 'Payment processor' in tips else ['All'],
            'statusOptions': list(tips['Status'].unique()) if 'Status' in tips else ['All'],
            'ggPayeersOptions': ['All', 'Without gg teammates', 'Only gg teammates']  # Исправление здесь
        }
        
        # Настройки боковой панели
        with st.sidebar:
            st.header('Settings')
            
            with st.expander('ggTips filters'):
                
                st.multiselect('Status', options['statusOptions'], key='Status')
                
                if st.session_state.get('ggPayeers') not in options['ggPayeersOptions']:
                    st.session_state['ggPayeers'] = 'All'
                    
                date_range = st.date_input("Select date range", [])
                
                if date_range:
                    start_date, end_date = date_range
                    filteredTips = filteredTips[(filteredTips['Date'] >= pd.to_datetime(start_date)) & (filteredTips['Date'] <= pd.to_datetime(end_date))]

                col1, col2 = st.columns(2)
                
                with col1:
                    st.selectbox('ggPayers', options['ggPayeersOptions'], key='ggPayeers')

                with col2:
                    st.multiselect('Payment Processor', options['paymentProcessorOptions'], key='paymentProcessor')

                col1, col2 = st.columns(2)

                with col1:
                    st.number_input('Min amount', step=1000, min_value=0, max_value=50000, key='amountFilterMin')

                with col2:
                    st.number_input('Max amount', step=1000, min_value=st.session_state['amountFilterMin'], max_value=50000, key='amountFilterMax')
                    
                timeIntervalOptions = ['Week', 'Month', 'Year', 'Week day', 'Day', 'Hour', 'Custom day']

                if st.session_state['timeInterval'] != 'Custom day':
                    st.selectbox('Time interval', timeIntervalOptions, key='timeInterval')
                else:
                    col1, col2 = st.columns(2)

                    with col1:
                        st.selectbox('Time interval', timeIntervalOptions, index=timeIntervalOptions.index("Custom day"), key='timeInterval')

                    with col2:
                        st.number_input('Custom', value=10, step=1, min_value=1, key='customInterval')

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
            filteredCompanies = filteredCompanies[filteredCompanies['Company'].isin(st.session_state['selectedCompanies'])]
        if 'selectedPartners' in st.session_state and st.session_state['selectedPartners']:
            filteredTips = filteredTips[filteredTips['Partner'].isin(st.session_state['selectedPartners'])]
        if 'Status' in st.session_state and st.session_state['Status']:
            filteredTips = filteredTips[filteredTips['Status'].isin(st.session_state['Status'])]
        if 'paymentProcessor' in st.session_state and st.session_state['paymentProcessor']:
            filteredTips = filteredTips[filteredTips['Payment processor'].isin(st.session_state['paymentProcessor'])]
        if 'Amount' in filteredTips and 'amountFilterMin' in st.session_state and 'amountFilterMax' in st.session_state:
            filteredTips = filteredTips[
                (filteredTips['Amount'] >= st.session_state['amountFilterMin']) &
                (filteredTips['Amount'] <= st.session_state['amountFilterMax'])
            ]
        if st.session_state['ggPayeers'] and 'ggPayer' in filteredTips.columns:
            if st.session_state['ggPayeers'] == 'Without gg teammates':
                filteredTips = filteredTips[~filteredTips['ggPayer'].isin(ggTeammates['id'])]
            elif st.session_state['ggPayeers'] == 'Only gg teammates':
                filteredTips = filteredTips[filteredTips['ggPayer'].isin(ggTeammates['id'])] 

        # Применение группировки по интервалу времени
        if st.session_state['timeInterval'] == 'Custom day':
            custom_days = st.session_state.get('customInterval', 10)
            filteredTips = customInterval(filteredTips, custom_days)
            time_interval = 'Custom'
        else:
            time_interval = st.session_state['timeInterval']

        groupedTips = filteredTips.groupby(time_interval).agg({
            'Amount': 'sum',
            'uuid': 'count',  
            'WeekStart': 'max',
            'WeekEnd': 'max'
        }).reset_index().rename(columns={'uuid': 'Count', 'Amount': 'ggTips'})

        if time_interval not in ['Week', 'Month', 'Year']:
            groupedTips['Period'] = groupedTips[time_interval].astype(str)
        else:
            groupedTips['Period'] = groupedTips['WeekStart'].dt.strftime('%Y-%m-%d') + ' - ' + groupedTips['WeekEnd'].dt.strftime('%Y-%m-%d')

        groupedTips = formatTimeIntervals(groupedTips, time_interval)

        with st.expander('stats'):
            col1, col2, col3 = st.columns(3)
            
            sumTips = groupedTips['ggTips'].sum()
            countTips = groupedTips['Count'].sum()
            connectionDays = filteredCompanies['Days'].max()
            
            if countTips !=0:
                averageTip = round(sumTips / countTips)
            else:
                averageTip = 0
            
            if pd.notna(connectionDays) and connectionDays != 0:
                oneDayTip = round(sumTips/connectionDays)
            else:
                oneDayTip = 0 
            
            with col1:
                st.write('Sum: ', sumTips)

            with col2:
                st.write('Count: ', countTips)
                
            with col3:
                st.write('One average tip', averageTip)
                
            col1, col2, col3 = st.columns(3)
            
            
            with col1:
                st.write('Activ days: ', connectionDays)
                
            with col2:
                st.write('Daily tips amount: ', oneDayTip)
                             
        # Создание графика с помощью Altair
        AllTipsTab, CompaniesTipsTab, TablesTab, MapTab = st.tabs(['Graph', 'Companies', 'Tables', 'map'])
        
        with AllTipsTab: 
                        
            st.header("All Tips Overview")
            
            with st.container():
                with st.expander('Sorting'):
                    sort_column = st.selectbox("Select column for sorting", ["ggTips", "Count", "Time"], key="sort_col_all")
                    sort_direction = st.selectbox("Select sort direction", ["Descending", 'Ascending'], key="sort_dir_all")

                    # Если выбрано сортировать по времени, выполняем сортировку по нужному интервалу времени
                    if sort_column == "Time":
                        # Преобразуем колонку времени в datetime, если это возможно
                        if time_interval in ['Week', 'Month', 'Year']:
                            groupedTips[time_interval] = pd.to_datetime(groupedTips['WeekStart'])  # Для недель, месяцев и годов
                        else:
                            groupedTips[time_interval] = pd.to_datetime(groupedTips[time_interval])  # Для дней или кастомных интервалов

                        # Сортируем данные по времени
                        groupedTips = groupedTips.sort_values(by=time_interval, ascending=(sort_direction == 'Ascending'))
                    else:
                        # Если сортировка по другим колонкам (например, ggTips или Count)
                        groupedTips = groupedTips.sort_values(by=sort_column, ascending=(sort_direction == 'Ascending'))
                # st.write(groupedTips)
                
                if sum_type != 'None' or count_type != 'None':
                    layers = []

                    x_axis = alt.X(f'{time_interval}:O',  # Указываем категориальную ось для строк или чисел (O), либо T для дат
                        axis=alt.Axis(title=f'{time_interval}', titleFontSize=14),
                        sort=groupedTips[time_interval].tolist())

                    if sum_type != 'None':
                        if sum_type == 'Column':
                            # Добавляем границу (stroke) и ширину границы (strokeWidth) для столбцов
                            sum_layer = alt.Chart(groupedTips).mark_bar(
                                size=20,  # Размер столбца
                                color=sum_color,  # Основной цвет столбца
                                stroke='white',  # Граница столбца
                                strokeWidth=1  # Толщина границы
                            )
                        elif sum_type == 'Line':
                            sum_layer = alt.Chart(groupedTips).mark_line(color=sum_color)
                        elif sum_type == 'Area':
                            sum_layer = alt.Chart(groupedTips).mark_area(color=sum_color)

                        sum_layer = sum_layer.encode(
                            x=x_axis,
                            y=alt.Y('ggTips:Q', axis=alt.Axis(title='Sum of Tips')),
                            tooltip=['Period', 'ggTips', 'Count']
                        ).properties(
                            width=chart_width,
                            height=chart_height
                        )
                        layers.append(sum_layer)

                    if count_type != 'None':
                        if count_type == 'Column':
                            # Аналогично добавляем границу для второго слоя
                            count_layer = alt.Chart(groupedTips).mark_bar(
                                size=20,  # Размер столбца
                                color=count_color,  # Основной цвет столбца
                                stroke='white',  # Граница столбца
                                strokeWidth=2  # Толщина границы
                            )
                        elif count_type == 'Line':
                            count_layer = alt.Chart(groupedTips).mark_line(color=count_color)
                        elif count_type == 'Area':
                            count_layer = alt.Chart(groupedTips).mark_area(color=count_color)

                        count_layer = count_layer.encode(
                            x=x_axis,
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
            with CompaniesTipsTab:
                
                companiesGroupedTips = filteredTips.groupby('Company').agg({
                    'Amount': 'sum',
                    'uuid': 'count',
                    'WeekStart': 'max',
                    'WeekEnd': 'max',
                }).reset_index().rename(columns={'uuid': 'Count', 'Amount': 'ggTips'})

                st.header("Companies Tips Overview")

                # Выбор колонок для сортировки и направления
                with st.container():
                    
                    with st.expander('Sorting'):
                        sort_column_companies = st.selectbox("Select column for sorting", ["ggTips", "Count"], key="sort_col_companies")
                        sort_direction_companies = st.selectbox("Select sort direction", ["Ascending", "Descending"], key="sort_dir_companies")

                        if sort_direction_companies == "Ascending":
                            companiesGroupedTips = companiesGroupedTips.sort_values(by=sort_column_companies, ascending=True)
                        else:
                            companiesGroupedTips = companiesGroupedTips.sort_values(by=sort_column_companies, ascending=False)
                            

                # if sort_column == "Date":
                #     groupedTips['Week'] = pd.to_datetime(groupedTips['Date'])

                st.write(companiesGroupedTips)
                    
                if sum_type != 'None' or count_type != 'None':
                    layers = []
                    
                    # Ось X для компаний (категориальная)
                    x_axis = alt.X('Company:N', axis=alt.Axis(title='Company Name'), sort=companiesGroupedTips['Company'].tolist())

                    if sum_type != 'None':
                        if sum_type == 'Column':
                            sum_layer = alt.Chart(companiesGroupedTips).mark_bar(
                                size=10,  # Уменьшаем размер столбцов для увеличения расстояния между ними
                                color=sum_color,
                                stroke='white',  # Добавляем белую границу вокруг каждого столбца
                                strokeWidth=1  # Толщина границы
                            )
                        elif sum_type == 'Line':
                            sum_layer = alt.Chart(companiesGroupedTips).mark_line(color=sum_color)
                        elif sum_type == 'Area':
                            sum_layer = alt.Chart(companiesGroupedTips).mark_area(color=sum_color)

                        sum_layer = sum_layer.encode(
                            x=x_axis,
                            y=alt.Y('ggTips:Q', axis=alt.Axis(title='Sum of Tips')),
                            tooltip=['Company', 'ggTips', 'Count']
                        ).properties(
                            width=chart_width,
                            height=chart_height
                        )
                        layers.append(sum_layer)

                    if count_type != 'None':
                        if count_type == 'Column':
                            count_layer = alt.Chart(companiesGroupedTips).mark_bar(
                                size=10,  # Аналогично уменьшаем размер столбцов для второго слоя
                                color=count_color,
                                stroke='white',  # Добавляем белую границу
                                strokeWidth=1
                            )
                        elif count_type == 'Line':
                            count_layer = alt.Chart(companiesGroupedTips).mark_line(color=count_color)
                        elif count_type == 'Area':
                            count_layer = alt.Chart(companiesGroupedTips).mark_area(color=count_color)

                        count_layer = count_layer.encode(
                            x=x_axis,
                            y=alt.Y('Count:Q', axis=alt.Axis(title='Count of Transactions', titleFontSize=14)),
                            tooltip=['Company', 'ggTips', 'Count']
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

        with TablesTab:
            st.write('Companies')
            st.dataframe(companies)
            
            st.write('Filtered Data')
            st.dataframe(filteredTips)
            
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
        
    else:
        st.write("import data about ggTips product for analyze")

    authenticator.logout()

elif st.session_state['authentication_status'] == False:
    st.error('Username/password is incorrect')

elif st.session_state['authentication_status'] == None:
    st.warning('Please enter your username and password')

