import pandas as pd

def load_data():

    file_path = "data/ggTips admin.xlsx"
    try:
        xls = pd.ExcelFile(file_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"{file_path} not found")

    sheets = xls.sheet_names

    # Dictionary to store DataFrame for each sheet
    sheetsData = {}
    for sheet in sheets:
        sheetsData[sheet] = pd.read_excel(xls, sheet_name=sheet)

    tips = sheetsData['allTipsNew']

    # Date configuration
    tips['Date'] = pd.to_datetime(tips['Date'])
    tips['weekNumber'] = tips['Date'].dt.isocalendar().week
    tips['month'] = tips['Date'].dt.month
    tips['year'] = tips['Date'].dt.year

    # Unique Company name
    tips['Company name'] = tips['Company name'].astype(str)
    tips['Partner name'] = tips['Partner name'].astype(str)
    tips["companyPartner"] = tips["Company name"] + "_" + tips["Partner name"]

    # Date filters
    filtered_tips = tips[tips['Amount'] > 100]
    filtered_tips = filtered_tips[filtered_tips['Date'].dt.year > 2023]

    defaultInputs = {
        "default_month": 0,
        "default_ggPayeers": 1,  # Update to index
        "default_payment_processor": 0,
        "default_amount_min": 110,
        "default_amount_max": 50000
    }

    data = {
        'tips': filtered_tips,
        'defaultInputs': defaultInputs
    }

    return data
