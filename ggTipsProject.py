import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit_plotly_events import plotly_events
from data.ggTipsData import load_data

# Read data
data = load_data()
tips = data["tips"]
defaultInputs = data['defaultInputs']

# Initialize session state for filters
if 'selected_month' not in st.session_state:
    st.session_state['selected_month'] = defaultInputs['default_month']
if 'ggPayeers' not in st.session_state:
    st.session_state['ggPayeers'] = defaultInputs['default_ggPayeers']
if 'Payment_processor' not in st.session_state:
    st.session_state['Payment_processor'] = defaultInputs['default_payment_processor']
if 'amountFilterMin' not in st.session_state:
    st.session_state['amountFilterMin'] = defaultInputs['default_amount_min']
if 'amountFilterMax' not in st.session_state:
    st.session_state['amountFilterMax'] = defaultInputs['default_amount_max']

# Function to reset filters
def reset_filters():
    st.session_state['selected_month'] = str(defaultInputs['default_month'])
    st.session_state['ggPayeers'] = defaultInputs['default_ggPayeers']
    st.session_state['Payment_processor'] = defaultInputs['default_payment_processor']
    st.session_state['amountFilterMin'] = defaultInputs['default_amount_min']
    st.session_state['amountFilterMax'] = defaultInputs['default_amount_max']
    st.experimental_rerun()

# Create Streamlit app
st.set_page_config(layout="wide")
st.title("ggTips")

# Add month selection
months = ["All", 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
selected_month = st.selectbox("Select month", months, index=months.index(st.session_state['selected_month']), key='selected_month')

col1, col2 = st.columns(2)

ggPayeersOptions = ["All", "Wihout gg teammates", "Only gg teammates"]
paymentProcessorOptions = ["All"] + list(tips["PaymentProcessor"].unique())

with col1:
    ggPayeers = st.selectbox("ggPayers", ggPayeersOptions, index=ggPayeersOptions.index(st.session_state['ggPayeers']), key='ggPayeers')

with col2:
    Payment_processor = st.selectbox("Payment Processor", paymentProcessorOptions, index=paymentProcessorOptions.index(st.session_state['Payment_processor']), key='Payment_processor')

with st.expander("More filters"):
    col3, col4 = st.columns(2)

    with col3:
        amountFilterMin = st.number_input("Min amount", value=st.session_state['amountFilterMin'], step=1000, min_value=100, max_value=50000, key='amountFilterMin')

    with col4:
        amountFilterMax = st.number_input("Max amount", value=st.session_state['amountFilterMax'], step=1000, min_value=amountFilterMin, max_value=50000, key='amountFilterMax')

# Add Reset Filters button
if st.button('Reset Filters'):
    reset_filters()

# Filter data based on selected month

if selected_month != "All":
    month_index = months.index(selected_month)
    tips = tips[tips['month'] == month_index]

weeklyTips = tips.groupby("weekNumber").agg({
    "Amount": "sum",
    "companyPartner": "count"
}).reset_index().rename(columns={"Amount": "Sum of amount", "companyPartner": "Count"})



st.header("ggTips")

# Create bar chart for sum of amount
fig_sum = px.bar(weeklyTips, x='weekNumber', y='Sum of amount',
                    title='Weekly Sum of Amount',
                    labels={'value': 'Values', 'variable': 'Metrics'},
                    color_discrete_sequence=['green'],
                    )  # Change colors here

fig_sum.update_traces(
    texttemplate="%{y:․0f}",
    textposition='outside',
    hovertemplate="<b>Week Number:</b> %{x}<br><b>Sum of Amount:</b> %{y}<extra></extra>",
    hoverlabel=dict(
        bgcolor="black",
        font_size=15
        # font_family="Rockwell"
    )
)

fig_sum.update_layout({
    'plot_bgcolor': 'rgba(0, 0, 0, 0)',
    'paper_bgcolor': 'rgba(0, 0, 0, 0)',
    'font': {'color': 'white'},  # Change font color to white
    'width': 1000,  # Set the width
    'height': 400,  # Set the height
})

# Create bar chart for count
fig_count = px.bar(weeklyTips, x='weekNumber', y='Count',
                    title='Weekly Transaction Count',
                    labels={'value': 'Values', 'variable': 'Metrics'},
                    color_discrete_sequence=['blue'])  # Change colors here

fig_count.update_layout({
    'plot_bgcolor': 'rgba(0, 0, 0, 0)',
    'paper_bgcolor': 'rgba(0, 0, 0, 0)',
    'font': {'color': 'white'},  # Change font color to white
    'width': 800,  # Set the width
    'height': 400  # Set the height
})

click_event_sum = plotly_events(fig_sum)
click_event_count = plotly_events(fig_count)

if click_event_sum:
    week_num = click_event_sum[0]['x']
    filtered_data = tips[tips['weekNumber'] == week_num]
    st.write(f"Transactions for week {week_num}")
    selectedColumns = ["Company name", "Partner name", "Date", "Amount", "PaymentProcessor", "ggPayer"]
    st.dataframe(filtered_data[selectedColumns])
elif click_event_count:
    week_num = click_event_count[0]['x']
    filtered_data = tips[tips['weekNumber'] == week_num]
    st.write(f"Transactions for week {week_num}")
    selectedColumns = ["Company name", "Partner name", "Date", "Amount", "PaymentProcessor", "ggPayer"]
    st.dataframe(filtered_data[selectedColumns])

# Add Scroll to Top button
scroll_to_top = """
<script>
    window.onscroll = function() {
        var scrollButton = document.getElementById("scrollToTop");
        if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
            scrollButton.style.display = "block";
        } else {
            scrollButton.style.display = "none";
        }
    };
    function scrollToTop() {
        document.body.scrollTop = 0;
        document.documentElement.scrollTop = 0;
    }
</script>
<button onclick="scrollToTop()" id="scrollToTop" title="Go to top" style="display:none;position:fixed;bottom:20px;right:20px;z-index:99;font-size:18px;border:none;outline:none;background-color:red;color:white;cursor:pointer;padding:15px;border-radius:10px;">Top</button>
"""
st.markdown(scroll_to_top, unsafe_allow_html=True)
