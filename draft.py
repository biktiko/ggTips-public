def load_data():
    # ... предыдущий код ...

    # Загрузка файлов и обработка листов
    for file in os.listdir(uploadFilesPath):
        file_path = os.path.join(uploadFilesPath, file)
        if isExcelFile(file_path):
            newExcelFile = pd.ExcelFile(file_path)

            for sheet in newExcelFile.sheet_names:
                df_header = pd.read_excel(newExcelFile, sheet_name=sheet, nrows=0)

                # Проверка наличия хотя бы одного ключевого слова в заголовках столбцов для Tips
                for table in tablesKeyWords.keys():
                    if any(keyword in df_header.columns for keyword in tablesKeyWords[table]):
                        if table == "Tips":
                            columns_to_load = []
                            for column in df_header.columns:
                                column_stripped = column.lower()
                                for key, keywords in columnsKeyWords.items():
                                    if column_stripped in keywords:
                                        columns_to_load.append(column)

                            if columns_to_load:
                                df = pd.read_excel(newExcelFile, sheet_name=sheet, usecols=columns_to_load, engine='openpyxl')
                                df = df.copy()

                                # Переименование столбцов
                                renamed_columns = {}
                                for column in df.columns:
                                    column_stripped = column.strip().lower()
                                    for key, keywords in columnsKeyWords.items():
                                        if column_stripped in keywords:
                                            renamed_columns[column] = key

                                df.rename(columns=renamed_columns, inplace=True)
                                df = replace_values(df)

                                # Обработка времени
                                if 'Date' in df.columns:
                                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

                                # Проверка и объединение данных по uuid
                                if 'uuid' in df.columns:
                                    df.set_index('uuid', inplace=True)

                                    # Удаление дубликатов внутри одного листа
                                    df = df[~df.index.duplicated(keep='last')]

                                    # Проверка инициализации DataFrame Tips
                                    if Tips.empty:
                                        Tips = df.copy()
                                    else:
                                        # Убедиться, что в Tips есть все столбцы из df
                                        Tips = ensure_columns_exist(Tips, df.columns)

                                        # Объединение данных, не перезаписывая существующие
                                        Tips.set_index('uuid', inplace=True, drop=False)
                                        Tips.update(df)
                                        new_rows = df.loc[~df.index.isin(Tips.index)]
                                        Tips = pd.concat([Tips, new_rows], ignore_index=False)
                                        Tips.reset_index(inplace=True)
                                else:
                                    print(f"'uuid' column not found in the sheet {sheet}")
                            elif table == 'Companies':
                                print("Company sheet is ", sheet)
                                df_companies = pd.read_excel(newExcelFile, sheet_name=sheet, engine='openpyxl')
                                companies = pd.concat([companies, df_companies])

                    # Обработка листа с данными о ggTeammates
                    elif sheet.lower() == 'gg teammates':  # Проверка имени листа без учета регистра
                        df_teammates = pd.read_excel(newExcelFile, sheet_name=sheet, engine='openpyxl')

                        if 'ID' in df_teammates.columns and 'NUMBER' in df_teammates.columns:
                            ggTeammates['id'] = df_teammates['ID']
                            ggTeammates['number'] = df_teammates['NUMBER']
                        else:
                            print(f"'ID' or 'NUMBER' column not found in the sheet {sheet}")

    # Обработка временных меток и создание дополнительных столбцов
    if 'Date' in Tips.columns:
        Tips['Date'] = pd.to_datetime(Tips['Date'], errors='coerce')
        Tips = Tips[Tips['Date'].dt.year > 2023]
        Tips['Week'] = Tips['Date'].dt.isocalendar().week
        Tips['Hour'] = Tips['Date'].dt.hour
        Tips['Day'] = Tips['Date'].dt.day
        Tips['Month'] = Tips['Date'].dt.month
        Tips['Year'] = Tips['Date'].dt.year
        Tips['Week day'] = Tips['Date'].dt.weekday
        Tips['WeekStart'] = pd.to_datetime(Tips['Year'].astype(str) + Tips['Week'].astype(str) + '1', format='%Y%W%w')
        Tips['WeekEnd'] = Tips['WeekStart'] + pd.Timedelta(days=6)
    
    if 'Company' in Tips.columns and 'Partner' in Tips.columns:
        Tips['Company'] = Tips['Company'].astype(str)
        Tips['Partner'] = Tips['Partner'].astype(str)
        Tips['companyPartner'] = Tips['Company'] + '_' + Tips['Partner']

    defaultInputs = {
        'selectedMonth': [],
        'ggPayeers': 'Wihout gg teammates',
        'amountFilterMin': 110,
        'amountFilterMax': 50000,
        'timeInterval': 'Week',
        'paymentProcessor': [],
        'Status': ['finished'] if not Tips.empty and 'Status' in Tips.columns and 'finished' in Tips['Status'].values else [],
        'selectedCompanies': [],
        'selectedPartner': []
    }

    data = {
        'tips': Tips,
        'companies': companies,
        'defaultInputs': defaultInputs,
        'ggTeammates': ggTeammates
    }

    return data
