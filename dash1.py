import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px

# Load the datasets
hiv_df = pd.read_csv('art_coverage_by_country_clean.csv')
df = pd.read_csv('AIDS_Classification.csv')

# Clean column names by replacing non-breaking spaces with regular spaces
hiv_df.columns = hiv_df.columns.str.replace('\xa0', ' ')

# Get a list of all countries from Plotly's gapminder dataset
all_countries = px.data.gapminder()['country'].unique()
all_countries_df = pd.DataFrame({'Country': all_countries})

# Ensure all countries are included
hiv_df = pd.merge(all_countries_df, hiv_df, on='Country', how='left').fillna(0)

# Create binary columns for each treatment type
df = pd.concat([df, pd.get_dummies(df['trt'], prefix='protocol').astype(int)], axis=1)


def plot_map(df, col, pal):
    # Convert col to numeric type if necessary
    df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop rows where col is NaN
    df = df.dropna(subset=[col])

    # Create choropleth map using Plotly
    fig = go.Figure(data=go.Choropleth(
        locations=df['Country'],
        locationmode='country names',
        z=df[col],
        colorscale=pal,
        text=df['Country'],
        marker_line_color='darkgray',
        marker_line_width=0.5,
    ))

    fig.update_layout(
        title_text='ART Coverage by Country',
        title_x=0.5,
        geo=dict(
            showframe=False,
            showcoastlines=False,
            projection_type='equirectangular'
        )
    )
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

# Add a selectbox for CD4 or CD8
marker_type = st.selectbox(
    "Select Marker Type",
    options=[
        {'label': 'CD4', 'value': 'CD4'},
        {'label': 'CD8', 'value': 'CD8'}
    ],
    format_func=lambda x: x['label']
)['value']

# Create scatter plots for the selected marker type
if marker_type == 'CD4':
    x_data = filtered_df['cd40']
    y_data = filtered_df['cd420']
    marker_name = 'CD4'
else:
    x_data = filtered_df['cd80']
    y_data = filtered_df['cd820']
    marker_name = 'CD8'

scatter_traces = []

scatter_traces.append(go.Scatter(
    x=x_data,
    y=y_data,
    mode='markers',
    name=marker_name,
    marker=dict(color='blue'),
    text=[f"Baseline: {format(int(x), ',')}, 20 Weeks: {format(int(y), ',')}" for x, y in zip(x_data, y_data)]
))

scatter_layout = go.Layout(
    title=f'Baseline vs 20 Weeks {marker_name} for Protocol {protocol}',
    xaxis={
        'title': f'Baseline {marker_name} Count',
        'tickformat': ','
    },
    yaxis={
        'title': f'{marker_name} Count at 20 Weeks',
        'tickformat': ','
    },
    hovermode='closest'
)

scatter_fig = go.Figure(data=scatter_traces, layout=scatter_layout)

# Display the scatter plot
st.plotly_chart(scatter_fig)

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
demographic_fig = go.Figure(data=go.Box(
    x=df[demographic],
    y=df[marker],
    name=f'{marker} by {demographic}'
))

demographic_fig.update_layout(
    title=f'{marker} by {demographic}',
    xaxis_title='Demographic',
    yaxis_title='Clinical Marker',
    yaxis=dict(tickformat=',')
)

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
    fig_survival_curve.update_layout(
        title='Kaplan-Meier Survival Curves by ART Protocol',
        xaxis_title='Time (days)',
        yaxis_title='Survival Probability',
        xaxis=dict(tickformat=','),
        yaxis=dict(tickformat=',')
    )

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
        yaxis_title='Infected',
        xaxis=dict(tickformat=','),
        yaxis=dict(tickformat=',')
    )

    return bar_fig


bar_plot_fig = update_bar_plot(protocol)
st.plotly_chart(bar_plot_fig)
