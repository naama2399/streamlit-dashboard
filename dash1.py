import streamlit as st
import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go

# Load the datasets
hiv_df = pd.read_csv('art_coverage_by_country_clean.csv')
df = pd.read_csv('AIDS_Classification.csv')

# Clean column names by replacing non-breaking spaces with regular spaces
hiv_df.columns = hiv_df.columns.str.replace('\xa0', ' ')

# Sort the DataFrame
hiv_df = hiv_df.sort_values(by='Reported number of people receiving ART', ascending=False)

# Create binary columns for each treatment type
df = pd.concat([df, pd.get_dummies(df['trt'], prefix='protocol').astype(int)], axis=1)

def plot_map(df, col, pal):
    # Convert col to numeric type if necessary
    df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop rows where col is NaN
    df = df.dropna(subset=[col])

    # Filter data where the specified column has values greater than 0
    df = df[df[col] > 0]

    # Create choropleth map using Plotly Express
    fig = px.choropleth(df, locations="Country", locationmode='country names',
                        color=col, hover_name="Country",
                        title='ART Coverage by Country', color_continuous_scale=pal, width=1500)
    return fig

# Streamlit app
st.title("ART Coverage and AIDS Progression Analysis")

# Display ART coverage map
st.header("ART Coverage by Country")
fig_art_coverage = plot_map(hiv_df, 'Reported number of people receiving ART', 'matter')
st.plotly_chart(fig_art_coverage)

# AIDS Progression Analysis
st.header("AIDS Progression Analysis")

# Create a selectbox for selecting ART protocol
protocol = st.selectbox(
    "Select ART Protocol",
    options=[
        {'label': 'ZDV only', 'value': 0},
        {'label': 'ZDV + ddI', 'value': 1},
        {'label': 'ZDV + Zal', 'value': 2},
        {'label': 'ddI only', 'value': 3}
    ],
    format_func=lambda x: x['label']
)['value']

# Filter the dataframe based on the selected protocol
filtered_df = df[df['trt'] == protocol]

# Create traces for CD4 and CD8 at baseline and after 20 weeks
traces = []

traces.append(go.Scatter(
    x=filtered_df.index,
    y=filtered_df['cd40'],
    mode='lines+markers',
    name='CD4 Baseline'
))

traces.append(go.Scatter(
    x=filtered_df.index,
    y=filtered_df['cd420'],
    mode='lines+markers',
    name='CD4 at 20 weeks'
))

traces.append(go.Scatter(
    x=filtered_df.index,
    y=filtered_df['cd80'],
    mode='lines+markers',
    name='CD8 Baseline'
))

traces.append(go.Scatter(
    x=filtered_df.index,
    y=filtered_df['cd820'],
    mode='lines+markers',
    name='CD8 at 20 weeks'
))

layout = go.Layout(
    title=f'Changes in CD4 and CD8 for Protocol {protocol}',
    xaxis={'title': 'Patient Index'},
    yaxis={'title': 'Count'},
    hovermode='closest'
)

fig = go.Figure(data=traces, layout=layout)

# Display the plot
st.plotly_chart(fig)

# Additional dropdowns and graphs
# Create a selectbox for selecting patient demographic
demographic = st.selectbox(
    "Select Patient Demographic",
    options=[
        {'label': 'Gender', 'value': 'gender'},
        {'label': 'Race', 'value': 'race'}
    ],
    format_func=lambda x: x['label']
)['value']

# Create a selectbox for selecting clinical marker
marker = st.selectbox(
    "Select Clinical Marker",
    options=[
        {'label': 'CD4 Count at Baseline', 'value': 'cd40'},
        {'label': 'CD4 Count at 20 Weeks', 'value': 'cd420'},
        {'label': 'CD8 Count at Baseline', 'value': 'cd80'},
        {'label': 'CD8 Count at 20 Weeks', 'value': 'cd820'}
    ],
    format_func=lambda x: x['label']
)['value']

# Update demographic outcomes graph
demographic_fig = px.box(df, x=demographic, y=marker, title=f'{marker} by {demographic}',
                         labels={demographic: 'Demographic', marker: 'Clinical Marker'},
                         color='trt',  # Add color based on ART protocols
                         color_discrete_sequence=px.colors.qualitative.Set1)
st.plotly_chart(demographic_fig)

# Update survival curve
def update_survival_curve(selected_protocol):
    fig_survival_curve = go.Figure()

    # Calculate survival curves for each treatment group
    for treatment in df['trt'].unique():
        treatment_data = df[df['trt'] == treatment]
        sorted_times = sorted(treatment_data['time'].unique())
        survival_prob = []
        num_patients = len(treatment_data)

        # Calculate survival probability for each time point
        current_prob = 1.0
        for t in sorted_times:
            patients_at_time_t = treatment_data[treatment_data['time'] >= t]
            num_patients_at_time_t = len(patients_at_time_t)
            num_events_at_time_t = sum(patients_at_time_t['infected'])
            current_prob *= (1.0 - 1.0 * num_events_at_time_t / num_patients_at_time_t)
            survival_prob.append(current_prob)

        # Add survival curve to the plot
        fig_survival_curve.add_trace(go.Scatter(x=sorted_times, y=survival_prob,
                                                mode='lines', name=f'Treatment {treatment}'))

    # Update layout of the figure
    fig_survival_curve.update_layout(title='Kaplan-Meier Survival Curves by ART Protocol',
                                     xaxis_title='Time (days)', yaxis_title='Survival Probability')

    return fig_survival_curve

survival_curve_fig = update_survival_curve(protocol)
st.plotly_chart(survival_curve_fig)

# Update bar plot
def update_bar_plot(selected_protocol):
    filtered_df = df[df['trt'] == selected_protocol]

    bar_fig = go.Figure()

    variables = ['hemo', 'homo', 'drugs']
    for var in variables:
        bar_fig.add_trace(go.Bar(
            x=filtered_df[var],
            y=filtered_df['infected'],
            name=f'Infected vs {var.capitalize()}',
        ))

    bar_fig.update_layout(
        barmode='group',
        title='Infection Rate vs Clinical Factors',
        xaxis_title='Clinical Factors',
        yaxis_title='Infected'
    )

    return bar_fig

bar_plot_fig = update_bar_plot(protocol)
st.plotly_chart(bar_plot_fig)
