import pandas as pd
import plotly.express as px
from pathlib import Path
from dash import Dash, Input, Output, callback, dcc, html

DATA_PATH = Path(__file__).resolve().parent / 'SuperMarket Analysis.csv'

df = pd.read_csv(DATA_PATH)
df['Date'] = pd.to_datetime(df['Date'])

def build_dashboard_data(filtered_df):
    branch_df = (
        filtered_df.groupby('Branch')['Sales']
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={'Sales': 'TotalSales'})
    )
    product_df = (
        filtered_df.groupby('Product line')['Sales']
        .sum()
        .sort_values(ascending=False)
        .head(8)
        .reset_index()
        .rename(columns={'Sales': 'TotalSales'})
    )
    payment_df = (
        filtered_df['Payment']
        .value_counts()
        .reset_index()
    )
    payment_df.columns = ['Payment', 'Transactions']
    monthly_df = (
        filtered_df.groupby(filtered_df['Date'].dt.to_period('M').astype(str))['Sales']
        .sum()
        .reset_index()
        .rename(columns={'Sales': 'TotalSales'})
    )
    monthly_df.columns = ['Month', 'TotalSales']
    metrics = {
        'Total sales': round(filtered_df['Sales'].sum(), 2),
        'Avg rating': round(filtered_df['Rating'].mean(), 2),
        'Transactions': int(filtered_df.shape[0]),
    }
    top_branch = branch_df.iloc[0]['Branch'] if not branch_df.empty else 'N/A'
    return branch_df, product_df, payment_df, monthly_df, metrics, top_branch

branch_options = [{'label': 'All branches', 'value': 'All'}] + [
    {'label': branch, 'value': branch} for branch in sorted(df['Branch'].unique())
]
product_options = [{'label': 'All product lines', 'value': 'All'}] + [
    {'label': product, 'value': product} for product in sorted(df['Product line'].unique())
]

app = Dash(__name__)
app.title = 'Supermarket Sales Dashboard'

app.layout = html.Div([
    html.Div([
        html.H1('Supermarket Sales Dashboard', style={'marginBottom': '0px'}),
        html.P('Explore sales performance by branch, product line, payment method, and month.'),
    ], style={'padding': '24px 24px 8px 24px'}),

    html.Div([
        html.Div([
            html.Label('Branch'),
            dcc.Dropdown(id='branch-filter', options=branch_options, value='All', clearable=False),
        ], style={'width': '48%', 'display': 'inline-block', 'paddingRight': '12px'}),
        html.Div([
            html.Label('Product line'),
            dcc.Dropdown(id='product-filter', options=product_options, value='All', clearable=False),
        ], style={'width': '48%', 'display': 'inline-block'}),
    ], style={'padding': '0 24px 24px 24px'}),

    html.Div([
        html.Div([
            html.H3('Total sales'),
            html.Div(id='metric-total-sales', style={'fontSize': '28px', 'fontWeight': '700'})
        ], style={'display': 'inline-block', 'width': '32%', 'padding': '10px', 'backgroundColor': '#f5f7fb', 'borderRadius': '12px', 'marginRight': '1%'}),
        html.Div([
            html.H3('Average rating'),
            html.Div(id='metric-average-rating', style={'fontSize': '28px', 'fontWeight': '700'})
        ], style={'display': 'inline-block', 'width': '32%', 'padding': '10px', 'backgroundColor': '#eef8ef', 'borderRadius': '12px', 'marginRight': '1%'}),
        html.Div([
            html.H3('Transactions'),
            html.Div(id='metric-transactions', style={'fontSize': '28px', 'fontWeight': '700'})
        ], style={'display': 'inline-block', 'width': '32%', 'padding': '10px', 'backgroundColor': '#fff4e5', 'borderRadius': '12px'}),
    ], style={'padding': '0 24px 16px 24px'}),

    html.Div([
        html.Div([
            html.H3('Sales by branch'),
            dcc.Graph(id='branch-graph'),
        ], style={'width': '48%', 'display': 'inline-block', 'paddingRight': '12px'}),
        html.Div([
            html.H3('Top product lines'),
            dcc.Graph(id='product-graph'),
        ], style={'width': '48%', 'display': 'inline-block'}),
    ], style={'padding': '0 24px 8px 24px'}),

    html.Div([
        html.Div([
            html.H3('Payment mix'),
            dcc.Graph(id='payment-graph'),
        ], style={'width': '48%', 'display': 'inline-block', 'paddingRight': '12px'}),
        html.Div([
            html.H3('Sales trend by month'),
            dcc.Graph(id='trend-graph'),
        ], style={'width': '48%', 'display': 'inline-block'}),
    ], style={'padding': '0 24px 24px 24px'}),

    html.Div([
        html.H3('Actionable insights'),
        html.Div(id='insight-summary', style={'fontSize': '16px', 'lineHeight': '1.6'})
    ], style={'padding': '0 24px 24px 24px'}),
])

@callback(
    Output('branch-graph', 'figure'),
    Output('product-graph', 'figure'),
    Output('payment-graph', 'figure'),
    Output('trend-graph', 'figure'),
    Output('metric-total-sales', 'children'),
    Output('metric-average-rating', 'children'),
    Output('metric-transactions', 'children'),
    Output('insight-summary', 'children'),
    Input('branch-filter', 'value'),
    Input('product-filter', 'value'),
)
def update_dashboard(branch, product):
    filtered_df = df.copy()
    if branch != 'All':
        filtered_df = filtered_df[filtered_df['Branch'] == branch]
    if product != 'All':
        filtered_df = filtered_df[filtered_df['Product line'] == product]

    branch_df, product_df, payment_df, monthly_df, metrics, top_branch = build_dashboard_data(filtered_df)

    branch_fig = px.bar(branch_df, x='Branch', y='TotalSales', color='Branch', title='Sales by branch')
    product_fig = px.bar(product_df, x='Product line', y='TotalSales', color='Product line', title='Top product lines')
    payment_fig = px.pie(payment_df, names='Payment', values='Transactions', title='Payment mix')
    trend_fig = px.line(monthly_df, x='Month', y='TotalSales', markers=True, title='Sales trend by month')

    insight = (
        f"{metrics['Transactions']} transactions were analyzed. "
        f"The strongest branch is {top_branch}, and the highest performing product line is {product_df.iloc[0]['Product line'] if not product_df.empty else 'N/A'}. "
        f"Use the filters to compare a single branch or product category for targeted action."
    )

    return (
        branch_fig,
        product_fig,
        payment_fig,
        trend_fig,
        f"${metrics['Total sales']:.2f}",
        f"{metrics['Avg rating']:.2f}",
        metrics['Transactions'],
        insight,
    )

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8050, debug=False)
