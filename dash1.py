import streamlit as st
import pandas as pd
import plotly.express as px

# Load the dataset
hiv_df = pd.read_csv('art_coverage_by_country_clean.csv')

# Clean column names by replacing non-breaking spaces with regular spaces
hiv_df.columns = hiv_df.columns.str.replace('\xa0', ' ')

# Define the function to plot the map
def plot_map(df, col, pal):
    # Convert col to numeric type if necessary
    df[col] = pd.to_numeric(df[col], errors='coerce')

    # Create choropleth map using Plotly Express
    fig = px.choropleth(df, locations="Country", locationmode='country names',
                        color=col, hover_name="Country",
                        title='ART Coverage by Country', color_continuous_scale=pal)
    
    # Update layout to adjust the size of the map itself
    fig.update_layout(
        autosize=False,
        width=1600,  # Increase the width
        height=1000,  # Increase the height
        margin={"r":0, "t":0, "l":0, "b":0},
        coloraxis_colorbar=dict(
            title="Reported number of people receiving ART",
            thicknessmode="pixels", thickness=15,
            lenmode="pixels", len=300,
            yanchor="middle", y=0.5,
            ticks="outside"
        )
    )
    return fig

# Streamlit app
st.title("Analyzing the Impact of ART Protocols on AIDS Progression")
st.header("ART Coverage by Country")

fig_art_coverage = plot_map(hiv_df, 'Reported number of people receiving ART', 'matter')
st.plotly_chart(fig_art_coverage)
