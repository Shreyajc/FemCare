import plotly.express as px


def pain_distribution(df):

    fig = px.histogram(
        df,
        x="pain_level",
        title="Pain Level Distribution"
    )

    return fig


def cycle_length_distribution(df):

    fig = px.histogram(
        df,
        x="cycle_length_days",
        title="Cycle Length Distribution"
    )

    return fig


def stress_distribution(df):

    fig = px.histogram(
        df,
        x="stress_score_cycle",
        title="Stress Score Distribution"
    )

    return fig