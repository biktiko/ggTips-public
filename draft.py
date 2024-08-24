import pandas as pd
import os

def isExcelFile(file_path):
    # Получаем расширение файла
    _, file_extension = os.path.splitext(file_path)
    
    # Проверяем, является ли расширение файла CSV или Excel
    if file_extension.lower() in ['.csv', '.xlsx']:
        return True
    else:
        return False

uploadFilesPath = 'data/uploads/'

def replace_values(df):
    replacements = {
        'Status': {
            'transferred': 'finished',
            'fail': 'failed',
            '2' : 'finished',
            2: 'finished',
            '3': 'failed',
            3: 'failed',
            '1': 'success',
            1: 'success',
            'failure': 'failed'
        },
        'Payment processor': {
            # Добавьте здесь другие замены
        }
    }
    
    for column, replace_dict in replacements.items():
        if column in df.columns:
            df[column] = df[column].replace(replace_dict)
    
    return df

def load_data():
    if not os.path.exists(uploadFilesPath):
        os.makedirs(uploadFilesPath)

    allData = []
    allSheets = []

    for file in os.listdir(uploadFilesPath):
        file_path = os.path.join(uploadFilesPath, file)
        if isExcelFile(file_path):
            try:
                newExcelFile = pd.ExcelFile(file_path)
                allData.append(newExcelFile)
                allSheets.extend(newExcelFile.sheet_names)  # Добавляем имена листов в allSheets
            except Exception as e:  # Ловим любое исключение
                print(f'{file} is not an excel file: {e}')
                
    # Словарь для хранения DataFrame для каждого листа
    Tips = pd.DataFrame()
    companies = pd.DataFrame()
    ggTeammates = pd.DataFrame()
    
    tablesKeyWords = {
        'Tips': ['uuid', 'Meta Data', 'Review comment', 'amount', 'paymentStateId', 'error_desc', 'remote_order_id', 'Payment processor', 'status'],
        'Companies': ['helpercompanyname', 'adress', 'working status', 'coordinate', 'region', 'status']
    }
    
    columnsKeyWords = {
        'Company': ['company', 'company name', 'company_name'],
        'Partner': ['partner', 'partner name', 'partner_name'],
        'Date': ['date', 'createdat', 'created_at'],
        'Amount': ['amount'],
        'Payment processor': ['paymentprocessor', 'processor', 'payment_processor'],
        'Status': ['status', 'paymentstateid'],
        'ggPayer': ['ggpayer', 'payer'],
        'ggPaye': ['ggpayee', 'paye'],
        'uuid': ['uuid', 'remote_order_id'],
    }
     
    for file in os.listdir(uploadFilesPath):
        file_path = os.path.join(uploadFilesPath, file)
        if isExcelFile(file_path):
            newExcelFile = pd.ExcelFile(file_path)

            for sheet in newExcelFile.sheet_names:
                df_header = pd.read_excel(newExcelFile, sheet_name=sheet, nrows=0)
                df_header.columns = [col.strip().lower() for col in df_header.columns]  # Приведение всех заголовков к нижнему регистру и убирание пробелов

                # Проверка наличия хотя бы одного ключевого слова в заголовках столбцов для Tips и других таблиц
                for table, keywords in tablesKeyWords.items():
                    if any(keyword.lower() in df_header.columns for keyword in keywords):
                        columns_to_load = [col for col in df_header.columns if any(col in keywords for keyword in columnsKeyWords.values())]
                        if columns_to_load:
                            df = pd.read_excel(newExcelFile, sheet_name=sheet, usecols=columns_to_load, engine='openpyxl')
                            df.columns = df.columns.str.strip().str.lower()  # Приведение всех заголовков к нижнему регистру

                            if table == 'Tips':
                                # Переименование столбцов
                                renamed_columns = {}
                                for column in df.columns:
                                    for key, keywords in columnsKeyWords.items():
                                        if column in keywords:
                                            renamed_columns[column] = key

                                df.rename(columns=renamed_columns, inplace=True)
                                df = replace_values(df)

                                # Обработка времени
                                if 'date' in df.columns:
                                    df['date'] = pd.to_datetime(df['date'], errors='coerce')

                                # Проверка и объединение данных по uuid
                                if 'uuid' in df.columns:
                                    df.set_index('uuid', inplace=True)
                                    df = df[~df.index.duplicated(keep='last')]

                                    if not Tips.empty:
                                        Tips.set_index('uuid', inplace=True)
                                        Tips.update(df)
                                        new_rows = df.loc[~df.index.isin(Tips.index)]
                                        Tips = pd.concat([Tips, new_rows], ignore_index=False)
                                        Tips.reset_index(inplace=True)
                                    else:
                                        Tips = pd.concat([Tips, df.reset_index()], ignore_index=True)
                                else:
                                    print(f"'uuid' column not found in the sheet {sheet}")
                            
                            elif table == 'Companies':
                                df_companies = pd.read_excel(newExcelFile, sheet_name=sheet, engine='openpyxl')
                                df_companies.columns = df_companies.columns.str.strip().str.lower()  # Приведение всех заголовков к нижнему регистру
                                companies = pd.concat([companies, df_companies], ignore_index=True)
                    
                    # Обработка листа с данными о ggTeammates
                    elif sheet.lower() == 'gg teammates':  # Проверка имени листа без учета регистра
                        df_teammates = pd.read_excel(newExcelFile, sheet_name=sheet, engine='openpyxl')

                        if 'id' in df_teammates.columns and 'number' in df_teammates.columns:
                            ggTeammates['id'] = df_teammates['id']
                            ggTeammates['number'] = df_teammates['number']
                        else:
                            print(f"'id' or 'number' column not found in the sheet {sheet}")

    # Обработка временных меток и создание дополнительных столбцов
    if 'Date' in Tips.columns:
        Tips['Date'] = pd.to_datetime(Tips['Date'], errors='coerce')
        Tips = Tips[Tips['Date'].dt.year > 2023]
        Tips['Week'] = Tips['Date'].dt.isocalendar().week
        Tips['Hour'] = Tips['Date'].dt.hour
        Tips['Day'] = Tips['Date'].dt.day
        Tips['Month'] = Tips['Date'].dt.month
        Tips['Year'] = Tips['Date'].dt.year
        Tips['Weeday'] = Tips['Date'].dt.weekday
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
        'selectedPartner': [],
        'aggretation': 'count'
    }

    data = {
        'tips': Tips,
        'companies': companies,
        'defaultInputs': defaultInputs,
        'ggTeammates': ggTeammates
    }
  
    return data
