import pandas as pd
import os

def isExcelFile(file_path):
    _, file_extension = os.path.splitext(file_path)
    return file_extension.lower() in ['.csv', '.xlsx']

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
    
    Tips = pd.DataFrame()
    companies = pd.DataFrame()
    ggTeammates = pd.DataFrame()
    
    tablesKeyWords = {
        'Tips': ['uuid', 'Meta Data', 'Review comment', 'paymentStateId', 'error_desc', 'remote_order_id', 'Payment processor', 'status'],
        'Companies': ['helpercompanyname', 'Adress', 'Working status', 'Coordinate', 'Region']
    }
    
    columnsKeyWords = {
        'Company': ['company', 'company name', 'company_name'],
        'Partner': ['partner', 'partner name', 'partner_name'],
        'Date': ['date', 'createdat', 'created_at'],
        'Amount': ['amount'],
        'Payment processor': ['paymentprocessor', 'payment processor', 'processor', 'payment_processor'],
        'Status': ['status', 'paymentstateid'],
        'ggPayer': ['ggpayer', 'payer'],
        'ggPaye': ['ggpayee', 'paye'],
        'uuid': ['uuid', 'remote_order_id'],
        'ggPay': ['ggpay']
    }
        
    def ensure_columns_exist(df, columns):
        for column in columns:
            if column not in df.columns:
                df[column] = pd.NA
        return df

    def update_df(existing_df, new_df):
        for column in new_df.columns:
            if column in existing_df.columns:
                existing_df[column].fillna(new_df[column], inplace=True)
            else:
                existing_df[column] = new_df[column]
        return existing_df

    for file in os.listdir(uploadFilesPath):
        file_path = os.path.join(uploadFilesPath, file)
        if isExcelFile(file_path):
            newExcelFile = pd.ExcelFile(file_path)

            for sheet in newExcelFile.sheet_names:
                df_header = pd.read_excel(newExcelFile, sheet_name=sheet, nrows=0)

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

                                renamed_columns = {}
                                for column in df.columns:
                                    column_stripped = column.strip().lower()
                                    for key, keywords in columnsKeyWords.items():
                                        if column_stripped in keywords:
                                            renamed_columns[column] = key

                                df.rename(columns=renamed_columns, inplace=True)
                                df = replace_values(df)

                                if 'Date' in df.columns:
                                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

                                # Проверка наличия столбца 'uuid'
                                if 'uuid' in df.columns:
                                    df.set_index('uuid', inplace=True)

                                    df = df[~df.index.duplicated(keep='last')]

                                    if Tips.empty:
                                        Tips = df.copy()
                                    else:
                                        Tips = ensure_columns_exist(Tips, df.columns)
                                        Tips.update(df)
                                        new_rows = df.loc[~df.index.isin(Tips.index)]
                                        Tips = pd.concat([Tips, new_rows], ignore_index=False)
                                        Tips.reset_index(inplace=True)
                                else:
                                    print(f"'uuid' column not found in the sheet {sheet}")
                        elif table == 'Companies':
                            df_companies = pd.read_excel(newExcelFile, sheet_name=sheet, engine='openpyxl')
                            companies = pd.concat([companies, df_companies])

                    elif sheet.lower() == 'gg teammates' or sheet.lower() == 'gg_teammates':
                        print('We in ggTeammates sheet')
                        df_teammates = pd.read_excel(newExcelFile, sheet_name=sheet, engine='openpyxl')

                        if 'ID' in df_teammates.columns and 'NUMBER' in df_teammates.columns:
                            ggTeammates['id'] = df_teammates['ID']
                            ggTeammates['number'] = df_teammates['NUMBER']
                        else:
                            print(f"'ID' or 'NUMBER' column not found in the sheet {sheet}")
                    else:
                        print('Not found ggTeammates sheet')


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
