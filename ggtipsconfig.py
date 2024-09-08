import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities.exceptions import LoginError
import yaml
from yaml.loader import SafeLoader
import calendar
import pandas as pd

# passwords = ['verch@ _T', 'some_other_password']
# hashed_passwords = stauth.Hasher(passwords).generate()
# print(hashed_passwords)

def login():

    with open('config.yaml', 'r', encoding='utf-8') as file:
        config = yaml.load(file, Loader=SafeLoader)

    # Creating the authenticator object
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
    )
    
    st.title('ggTips Analyze')

    try:
        authenticator.login()
    except LoginError as e:
        st.error(e)

    if not st.session_state.get('authentication_status', False):
        # Кнопка демо-режима показывается только при отсутствии аутентификации
        demo_mode = st.button("See how the program works with random data")

        if demo_mode:
            st.session_state['authentication_status'] = True
            st.session_state['demo_mode'] = True
            st.session_state['username'] = "demo_user"  # Временно присваиваем имя демо-пользователя
            st.rerun()  # Перезапуск страницы для загрузки демо-режима

    return authenticator
def formatTimeIntervals(df, time_interval):
    if time_interval == 'Month':
        df['Month'] = pd.Categorical(df['Month'].apply(lambda x: calendar.month_name[x]), 
                                     categories=calendar.month_name[1:], 
                                     ordered=True)
    elif time_interval == 'Week day':
        df['Week day'] = pd.Categorical(df['Week day'].apply(lambda x: calendar.day_name[x]), 
                                        categories=calendar.day_name, 
                                        ordered=True)
    return df