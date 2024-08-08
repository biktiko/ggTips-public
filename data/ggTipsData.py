import streamlit as st
import pandas as pd
import os

uploadFilesPath = 'data/uploads/'

def load_data():

    allData = []
    allSheets = []

    for file in os.listdir(uploadFilesPath):
        file_path = os.path.join(uploadFilesPath, file)
        if os.path.isfile(file_path):
            try:
                newExcelFile = pd.ExcelFile(file_path)
                allData.append(newExcelFile)
                allSheets.extend(newExcelFile.sheet_names)  # Добавляем имена листов в allSheets
            except Exception as e:  # Ловим любое исключение
                print(f'{file} is not an excel file: {e}')

    # Словарь для хранения DataFrame для каждого листа
    sheetsData = {}
    for file in allData:
        for sheet in file.sheet_names:  # Используем имена листов из текущего файла
            sheetsData[sheet] = pd.read_excel(file, sheet_name=sheet)

    if 'allTipsNew' in sheetsData:
        tips = sheetsData['allTipsNew']

        # Date configuration
        tips['Date'] = pd.to_datetime(tips['Date'])
        tips['weekNumber'] = tips['Date'].dt.isocalendar().week
        tips['hour'] = tips['Date'].dt.hour
        tips['day'] = tips['Date'].dt.day
        tips['month'] = tips['Date'].dt.month
        tips['year'] = tips['Date'].dt.year
        tips['weekday'] = tips['Date'].dt.weekday

        # Unique Company name
        tips['Company name'] = tips['Company name'].astype(str)
        tips['Partner name'] = tips['Partner name'].astype(str)
        tips['companyPartner'] = tips['Company name'] + '_' + tips['Partner name']

        # Date filters
        filtered_tips = tips[tips['Amount'] > 100]
        filtered_tips = filtered_tips[filtered_tips['Date'].dt.year > 2023]

    defaultInputs = {
        'selectedMonth': [],
        'ggPayeers': 'Wihout gg teammates',
        'amountFilterMin': 110,
        'amountFilterMax': 50000,
        'timeInterval': 'Week',
        'paymentProcessor': [],
        'paymentStatus': ['finished'],
        'selectedCompanies': [],
        'selectedPartner': []
    }

    try:
        data = {
            'tips': filtered_tips,
            'defaultInputs': defaultInputs
        }
    except:
        data = {
             'defaultInputs': defaultInputs 
        }

    return data
