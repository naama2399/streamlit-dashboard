import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px

# Set the page layout to wide
st.set_page_config(layout="wide")

# Load the datasets
hiv_df = pd.read_csv('art_coverage_by_country_clean.csv')
missing_values_count = hiv_df['Reported number of people receiving ART'].isna().sum()
print(missing_values_count)

df = pd.read_csv('AIDS_Classification.csv')
print(df.isna().sum())

# Clean column names by replacing non-breaking spaces with regular spaces
hiv_df.columns = hiv_df.columns.str.replace('\xa0', ' ')

# Get a list of all countries from Plotly's gapminder dataset
all_countries = px.data.gapminder()['country'].unique()
all_countries_df = pd.DataFrame({'Country': all_countries})

# Ensure all countries are included
hiv_df = pd.merge(all_countries_df, hiv_df, on='Country', how='left').fillna(0)

# Create binary columns for each treatment type
df = pd.concat([df, pd.get_dummies(df['trt'], prefix='protocol').astype(int)], axis=1)

# Define treatment names
treatment_names = {
    0: 'ZDV only',
    1: 'ZDV + ddI',
    2: 'ZDV + Zal',
    3: 'ddI only'
}

def plot_map(df, col, pal):
    # Convert col to numeric type if necessary
    df[col] = pd.to_numeric(df[col], errors='coerce')

    # Create choropleth map using Plotly Express
    fig = px.choropleth(df, locations="Country", locationmode='country names',
                        color=col, hover_name="Country",
                        title='ART Coverage by Country', color_continuous_scale=pal)
    fig.update_layout(
        autosize=False,
        margin={"r":0,"t":0,"l":0,"b":0},
        coloraxis_colorbar=dict(
            title="Reported number of people receiving ART",
            thicknessmode="pixels", thickness=15,
            lenmode="pixels", len=300,
            yanchor="middle", y=0.5,
            ticks="outside"
        )
    )
    return fig

def update_cumulative_incidence_curve():
    fig_cumulative_incidence_curve = go.Figure()

    # Calculate cumulative incidence for each treatment group
    for treatment in df['trt'].unique():
        treatment_data = df[df['trt'] == treatment]
        sorted_times = sorted(treatment_data['time'].unique())
        cumulative_incidence = []
        num_patients = len(treatment_data)

        # Calculate cumulative incidence for each time point
        cumulative_prob = 0.0
        for t in sorted_times:
            patients_at_time_t = treatment_data[treatment_data['time'] >= t]
            num_patients_at_time_t = len(patients_at_time_t)
            num_events_at_time_t = sum(patients_at_time_t['infected'])
            cumulative_prob += num_events_at_time_t / num_patients
            cumulative_incidence.append(cumulative_prob)

        # Add cumulative incidence curve to the plot
        fig_cumulative_incidence_curve.add_trace(go.Scatter(
            x=sorted_times,
            y=cumulative_incidence,
            mode='lines',
            name=f'Treatment {treatment}: {treatment_names[treatment]}'
        ))

    # Update layout of the figure
    fig_cumulative_incidence_curve.update_layout(title='Cumulative Incidence Curves by ART Protocol',
                                                 xaxis_title='Time (days)',
                                                 yaxis_title='Cumulative Proportion of Deaths',
                                                 autosize=False)
    return fig_cumulative_incidence_curve

# Streamlit app
# Add a title for your project
st.title("Analyzing the Impact of ART Protocols on AIDS Progression")

# Center the main image
st.image("picture_vizu.jpeg", width=1000, use_column_width='always')

fig_art_coverage = plot_map(hiv_df, 'Reported number of people receiving ART', 'matter')
st.plotly_chart(fig_art_coverage, use_container_width=True)

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
    "Choose a type of white blood cell",
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
    hovermode='closest',
    autosize=False
)

scatter_fig = go.Figure(data=scatter_traces, layout=scatter_layout)

# Display the scatter plot
st.plotly_chart(scatter_fig, use_container_width=True)

# Display cumulative incidence curve
st.header("Cumulative Incidence Analysis")
fig_cumulative_incidence_curve = update_cumulative_incidence_curve()
st.plotly_chart(fig_cumulative_incidence_curve, use_container_width=True)

# Add a selectbox for clinical variables
clinical_variable = st.selectbox(
    "Select Clinical Variable",
    options=[
        {'label': 'hemophilia', 'value': 'hemo'},
        {'label': 'Homosexuality', 'value': 'homo'},
        {'label': 'Drug Use', 'value': 'drugs'},
        {'label': 'Gender', 'value': 'gender'},
        {'label': 'Race', 'value': 'race'}
    ],
    format_func=lambda x: x['label']
)['value']

# Display explanation based on the selected variable
if clinical_variable == 'hemo':
    st.write("0: Not with hemophilia")
    st.write("1: With hemophilia")
elif clinical_variable == 'homo':
    st.write("0: Not homosexual")
    st.write("1: Homosexual")
elif clinical_variable == 'drugs':
    st.write("0: Not a drug user")
    st.write("1: Drug user")
elif clinical_variable == 'gender':
    st.write("0: Female")
    st.write("1: Male")
elif clinical_variable == 'race':
    st.write("0: Other")
    st.write("1: White")

# Update bar plot
def update_bar_plot(selected_protocol, variable):
    filtered_df = df[df['trt'] == selected_protocol]

    bar_fig = go.Figure()

    bar_fig.add_trace(go.Bar(
        x=filtered_df[variable],
        y=filtered_df['infected'],
        name=f'Infected vs {variable.capitalize()}',
    ))

    bar_fig.update_layout(
        barmode='group',
        title=f'Infection Rate vs {variable.capitalize()}',
        xaxis_title=variable.capitalize(),
        yaxis_title='Number of People Infected with AIDS',
        autosize=False
    )

    return bar_fig

bar_plot_fig = update_bar_plot(protocol, clinical_variable)
st.plotly_chart(bar_plot_fig, use_container_width=True)

# Add footer
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown("<center>Created by Naama Maimon & Stav Barak</center>", unsafe_allow_html=True)
