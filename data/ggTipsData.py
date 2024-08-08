import streamlit as st
import pandas as pd
import os

def load_data():

    mainFilePath = 'data/default/ggTips admin.xlsx'

    try:
        xls = pd.ExcelFile(mainFilePath)
    except FileNotFoundError:
        raise FileNotFoundError(f'{mainFilePath} not found')

    sheets = xls.sheet_names

    # Dictionary to store DataFrame for each sheet
    sheetsData = {}
    for sheet in sheets:
        sheetsData[sheet] = pd.read_excel(xls, sheet_name=sheet)

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

    data = {
        'tips': filtered_tips,
        'defaultInputs': defaultInputs
    }

    return data
