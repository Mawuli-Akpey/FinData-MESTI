import streamlit as st
import requests
import pandas as pd
import numpy as np
import re
import plotly.graph_objects as go
import plotly.express as px
import io

# Get the API URL from secrets
api_url = st.secrets["api"]["url"]

# Make the request to the API
response = requests.get(api_url)

# Check if the request was successful
if response.status_code == 200:
    # Load the CSV content into a pandas DataFrame
    df = pd.read_csv(io.StringIO(response.content.decode('utf-8')), delimiter=";")
else:
    st.error(f"Failed to retrieve data: {response.status_code}")

# Display the DataFrame
st.dataframe(df.head())

# Dictionary to substitute enumerator names
enumerator_dict = {
    'enuma002': 'Afishietu',
    'enuma003': 'Seidu',
    'enuma004': 'Zenabu',
    'enuma005': 'Sarah',
    'enuma006': 'Hilary',
    'enuma007': 'Zuwera',
    'enuma008': 'Adelaide',
    'enuma009': 'Razak',
    'enuma010': 'Joseph',
    'enuma011': 'Gifty'
}

# Replace the enumerator names
df['_submitted_by'] = df['_submitted_by'].replace(enumerator_dict)

# Convert start and end times to datetime
df['start'] = pd.to_datetime(df['start'], errors='coerce')
df['end'] = pd.to_datetime(df['end'], errors='coerce')

# Separate valid and invalid datetime entries
valid_df = df.dropna(subset=['start'])
invalid_df = df[df['start'].isna()]

# Date input from user
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2024-07-21"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2024-07-22"))

# Convert the input dates to datetime
start_datetime = pd.to_datetime(start_date)
end_datetime = pd.to_datetime(end_date) + pd.DateOffset(days=1) - pd.Timedelta(seconds=1)  # Include the entire end date

# Filter the valid DataFrame based on the selected date range
filtered_valid_df = valid_df[(valid_df['start'] >= start_datetime) & (valid_df['start'] <= end_datetime)]

# Concatenate the filtered valid entries with the invalid entries
df = pd.concat([filtered_valid_df, invalid_df])

# Calculate form completion time in minutes
df['form_complete_time'] = (df['end'] - df['start']).dt.total_seconds() / 60

# Calculate the required metrics
total_submissions = len(df)
average_form_complete_time = df['form_complete_time'].mean()
total_males = df['Participant Gender'].str.contains('Male', na=False).sum()
total_females = df['Participant Gender'].str.contains('Female', na=False).sum()

# Display metrics
st.write("### Metrics")
st.metric("Total Submissions", total_submissions)
st.metric("Avg. Form Complete Time (mins)", round(average_form_complete_time, 2))
st.metric("Total Males", total_males)
st.metric("Total Females", total_females)

# Count submissions by each enumerator
submission_counts = df['_submitted_by'].value_counts().reset_index()
submission_counts.columns = ['Enumerator', 'Number of Submissions']

# Plot submissions by each enumerator
fig = px.bar(submission_counts, x='Enumerator', y='Number of Submissions',
             title='Submissions by Each Enumerator',
             labels={'Number of Submissions': 'Number of Submissions'},
             text='Number of Submissions')
st.plotly_chart(fig)

# Calculate the average form complete time per enumerator
average_time_per_enumerator = df.groupby('_submitted_by')['form_complete_time'].mean().reset_index()
average_time_per_enumerator.columns = ['Enumerator', 'Average Form Complete Time (mins)']
average_time_per_enumerator['Average Form Complete Time (mins)'] = average_time_per_enumerator['Average Form Complete Time (mins)'].round(2)

# Plot average form complete time per enumerator
fig = px.bar(average_time_per_enumerator, x='Enumerator', y='Average Form Complete Time (mins)',
             title='Average Form Complete Time per Enumerator',
             labels={'Average Form Complete Time (mins)': 'Average Form Complete Time (mins)'},
             text='Average Form Complete Time (mins)')
st.plotly_chart(fig)

# Plot the distribution of ages
fig = px.histogram(df, x='Participant Age in years',
                   title='Age Distribution of Participants',
                   labels={'Participant Age in years': 'Age (years)'},
                   nbins=20,
                   marginal='box',
                   color_discrete_sequence=['skyblue'])
st.plotly_chart(fig)

# Plot the distribution of ages by gender
fig = px.histogram(df, x='Participant Age in years', color='Participant Gender',
                   title='Age Distribution of Participants by Gender',
                   labels={'Participant Age in years': 'Age (years)', 'Participant Gender': 'Gender'},
                   nbins=20,
                   marginal='box',
                   opacity=0.3,
                   color_discrete_sequence=px.colors.qualitative.Set1)
st.plotly_chart(fig)

# Plot the registration on Agritech e-commerce platforms
platform_registration_counts = df['Are you registered on any Agritech e-commerce platform?'].value_counts().reset_index()
platform_registration_counts.columns = ['Response', 'Count']
fig = px.bar(platform_registration_counts, x='Response', y='Count',
             title='Registration on Agritech E-commerce Platforms',
             labels={'Response': 'Registered on Agritech E-commerce Platform?', 'Count': 'Number of Participants'},
             text='Count')
st.plotly_chart(fig)

# Plot average form completion time by e-commerce platform registration
grouped_df = df.groupby(['_submitted_by', 'Are you registered on any Agritech e-commerce platform?'])['form_complete_time'].mean().reset_index()
grouped_df['form_complete_time'] = grouped_df['form_complete_time'].round(2)
grouped_df.columns = ['Enumerator', 'Registered on E-commerce Platform', 'Average Form Complete Time (mins)']
fig = px.bar(grouped_df, x='Enumerator', y='Average Form Complete Time (mins)',
             color='Registered on E-commerce Platform',
             barmode='group',
             title='Average Form Completion Time by Enumerator and E-commerce Platform Registration',
             labels={'Average Form Complete Time (mins)': 'Average Form Complete Time (mins)', 'Enumerator': 'Enumerator'},
             text='Average Form Complete Time (mins)')
st.plotly_chart(fig)

# Plot the count of different crops cultivated
df['<span style="display:none">row-Crop Type</span>'] = df['<span style="display:none">row-Crop Type</span>'].apply(lambda s: re.sub(r'\s+', '', s).title() if pd.notnull(s) else s)
crop_counts = df['<span style="display:none">row-Crop Type</span>'].value_counts().reset_index()
crop_counts.columns = ['Crop Type', 'Count']
fig = px.bar(crop_counts, x='Crop Type', y='Count',
             title='Count of Different Crops Cultivated',
             labels={'Crop Type': 'Crop Type', 'Count': 'Number of Cultivations'},
             text='Count')
st.plotly_chart(fig)

# Function to extract and count unique financial services
def extract_financial_services(df, column):
    services = {
        'Mobile Money': 0,
        'Bank Account': 0,
        'Personal Susu': 0,
        'Group savings': 0,
        'None': 0,
        'Other (Please specify)': 0
    }

    for entry in df[column].dropna():
        for service in services.keys():
            if service in entry:
                services[service] += 1

    return pd.DataFrame(list(services.items()), columns=['Financial Service', 'Count'])

# Extract the column with financial services registrations
financial_services_column = 'Which of the following financial services have you registered for? (Select all that apply)'
services_counts = extract_financial_services(df, financial_services_column)
fig = px.bar(services_counts, x='Financial Service', y='Count',
             title='Total Number of Different Financial Services Registered',
             labels={'Financial Service': 'Financial Service', 'Count': 'Number of Registrations'},
             text='Count')
st.plotly_chart(fig)

# Plot average yearly income from farming activities
income_column = 'What is your average yearly income from farming activities?'
income_counts = df[income_column].value_counts().reset_index()
income_counts.columns = ['Income Range', 'Count']
fig = px.bar(income_counts, x='Income Range', y='Count',
             title='Average Yearly Income from Farming Activities',
             labels={'Income Range': 'Income Range', 'Count': 'Number of Participants'},
             text='Count')
st.plotly_chart(fig)

# Plot the geographic location of entries by enumerator
geo_columns = ['_submitted_by', '_start-geopoint_latitude', '_start-geopoint_longitude']
df_geo = df[geo_columns].dropna(subset=['_start-geopoint_latitude', '_start-geopoint_longitude'])
df_geo['_submitted_by'] = df_geo['_submitted_by'].replace(enumerator_dict)
fig = px.scatter_mapbox(df_geo, lat='_start-geopoint_latitude', lon='_start-geopoint_longitude',
                        color='_submitted_by', title='Geographic Location of Entries by Enumerator',
                        mapbox_style='open-street-map', zoom=5, height=600)
fig.update_layout(
    legend_title_text='Enumerator',
    margin={'r': 0, 't': 0, 'l': 0, 'b': 0}
)
st.plotly_chart(fig)
