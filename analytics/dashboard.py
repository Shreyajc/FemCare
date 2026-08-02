import pandas as pd
import plotly.express as px


def load_data():
    return pd.read_csv("data/cleaned_dataset.csv")


def get_metrics(df):

    metrics = {
        "Total Records": len(df),
        "Unique Users": df["user_id"].nunique(),
        "Average Age": round(df["age"].mean(), 1),
        "Average BMI": round(df["bmi"].mean(), 1),
        "Average Cycle Length": round(df["cycle_length_days"].mean(), 1),
        "Average Pain": round(df["pain_level"].mean(), 1),
        "Average Stress": round(df["stress_score_cycle"].mean(), 1),
        "PCOS Cases": int(df["pcos_diagnosed"].sum())
    }

    return metrics


def cycle_chart(df):

    fig = px.histogram(
        df,
        x="cycle_length_days",
        title="Cycle Length Distribution"
    )

    return fig


def pain_chart(df):

    fig = px.histogram(
        df,
        x="pain_level",
        title="Pain Level Distribution"
    )

    return fig


def stress_chart(df):

    fig = px.histogram(
        df,
        x="stress_score_cycle",
        title="Stress Score Distribution"
    )

    return fig


def flow_chart(df):

    fig = px.histogram(
        df,
        x="flow_level",
        title="Flow Level Distribution"
    )

    return fig