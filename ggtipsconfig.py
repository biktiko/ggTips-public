import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities.exceptions import LoginError
import yaml
from yaml.loader import SafeLoader
import psutil

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

    # Creating a login widget
    try:
        authenticator.login()
    except LoginError as e:
        st.error(e)

    return authenticator


def closeFile(file_path):
    for proc in psutil.process_iter():
        try:
            for item in proc.open_files():
                if file_path == item.path:
                    proc.terminate()
                    proc.wait()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass