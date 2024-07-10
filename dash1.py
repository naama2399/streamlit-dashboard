import plotly.express as px

def plot_map(df, col, pal):
    # Create choropleth map using Plotly Express
    fig = px.choropleth(df, locations="Country", locationmode='country names',
                        color=col, hover_name="Country",
                        title='ART Coverage by Country', color_continuous_scale=pal)
    
    # Update layout to adjust the size of the map itself
    fig.update_layout(
        autosize=False,
        width=1200,  # Increase the width
        height=800,  # Increase the height
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

# Assuming hiv_df is your dataframe and 'Reported number of people receiving ART' is the column you want to plot
fig_art_coverage = plot_map(hiv_df, 'Reported number of people receiving ART', 'matter')
fig_art_coverage.show()
