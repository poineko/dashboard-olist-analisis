import pandas as pd
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px

# ---------- LOAD DATA ----------
master = pd.read_csv("master_dashboard.csv")

master["order_purchase_timestamp"] = pd.to_datetime(master["order_purchase_timestamp"], errors="coerce")
master["order_delivered_customer_date"] = pd.to_datetime(master["order_delivered_customer_date"], errors="coerce")
master["order_estimated_delivery_date"] = pd.to_datetime(master["order_estimated_delivery_date"], errors="coerce")

daftar_state = sorted(master["customer_state"].dropna().unique())
daftar_kategori = sorted(master["product_category_name_english"].dropna().unique())
daftar_payment = sorted(master["payment_type"].dropna().unique())
tanggal_min = master["order_purchase_timestamp"].min()
tanggal_max = master["order_purchase_timestamp"].max()

# ---------- APP ----------
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server  # dibutuhkan untuk deployment (gunicorn/hosting)

app.title = "Dashboard Analisis Olist E-Commerce"

# ---------- LAYOUT ----------
app.layout = dbc.Container([
    html.H1("Dashboard Analisis Olist E-Commerce", className="text-center my-4"),
    html.P(
        "Portofolio Uji Kompetensi BNSP - Skema Analis Data (Data Analyst) - BPVP Padang",
        className="text-center text-muted mb-4"
    ),

    dbc.Card(dbc.CardBody([
        dbc.Row([
            dbc.Col([
                html.Label("Wilayah Pelanggan"),
                dcc.Dropdown(
                    id="filter-state",
                    options=[{"label": "Semua Wilayah", "value": "ALL"}] +
                            [{"label": s.upper(), "value": s} for s in daftar_state],
                    value="ALL", clearable=False
                ),
            ], md=3),
            dbc.Col([
                html.Label("Rentang Tanggal Order"),
                dcc.DatePickerRange(
                    id="filter-tanggal",
                    min_date_allowed=tanggal_min, max_date_allowed=tanggal_max,
                    start_date=tanggal_min, end_date=tanggal_max,
                    display_format="DD-MM-YYYY"
                ),
            ], md=3),
            dbc.Col([
                html.Label("Kategori Produk"),
                dcc.Dropdown(
                    id="filter-kategori",
                    options=[{"label": k, "value": k} for k in daftar_kategori],
                    value=[], multi=True, placeholder="Semua kategori"
                ),
            ], md=3),
            dbc.Col([
                html.Label("Metode Pembayaran"),
                dcc.Dropdown(
                    id="filter-payment",
                    options=[{"label": "Semua Metode", "value": "ALL"}] +
                            [{"label": p, "value": p} for p in daftar_payment],
                    value="ALL", clearable=False
                ),
            ], md=3),
        ])
    ]), className="mb-4"),

    dbc.Row(id="kpi-cards", className="mb-4"),

    dbc.Tabs([
        dbc.Tab(label="1. Efisiensi Pengiriman", children=[
            dbc.Row([
                dbc.Col(dcc.Graph(id="grafik-durasi-wilayah"), md=6),
                dbc.Col(dcc.Graph(id="grafik-keterlambatan-wilayah"), md=6),
            ], className="mt-3"),
            dbc.Row([
                dbc.Col(dcc.Graph(id="grafik-estimasi-vs-aktual"), md=12),
            ]),
        ]),
        dbc.Tab(label="2. Performa Penjualan", children=[
            dbc.Row([
                dbc.Col(dcc.Graph(id="grafik-top-kategori"), md=6),
                dbc.Col(dcc.Graph(id="grafik-bottom-kategori"), md=6),
            ], className="mt-3"),
            dbc.Row([
                dbc.Col(dcc.Graph(id="grafik-top-seller"), md=6),
                dbc.Col(dcc.Graph(id="grafik-bottom-seller"), md=6),
            ]),
        ]),
        dbc.Tab(label="3. Kepuasan Pelanggan", children=[
            dbc.Row([
                dbc.Col(dcc.Graph(id="grafik-durasi-vs-review"), md=6),
                dbc.Col(dcc.Graph(id="grafik-review-per-kategori"), md=6),
            ], className="mt-3"),
            dbc.Row([
                dbc.Col(dcc.Graph(id="grafik-review-per-payment"), md=6),
                dbc.Col(dcc.Graph(id="grafik-review-vs-harga"), md=6),
            ]),
        ]),
    ]),

    html.Footer(
        "Dibuat dengan Python (Dash) - Analisis Data Olist Brazilian E-Commerce Public Dataset",
        className="text-center text-muted my-4"
    ),
], fluid=True)


# ---------- CALLBACK ----------
@app.callback(
    [Output("kpi-cards", "children"),
     Output("grafik-durasi-wilayah", "figure"),
     Output("grafik-keterlambatan-wilayah", "figure"),
     Output("grafik-estimasi-vs-aktual", "figure"),
     Output("grafik-top-kategori", "figure"),
     Output("grafik-bottom-kategori", "figure"),
     Output("grafik-top-seller", "figure"),
     Output("grafik-bottom-seller", "figure"),
     Output("grafik-durasi-vs-review", "figure"),
     Output("grafik-review-per-kategori", "figure"),
     Output("grafik-review-per-payment", "figure"),
     Output("grafik-review-vs-harga", "figure")],
    [Input("filter-state", "value"),
     Input("filter-tanggal", "start_date"),
     Input("filter-tanggal", "end_date"),
     Input("filter-kategori", "value"),
     Input("filter-payment", "value")]
)
def update_dashboard(state, tgl_mulai, tgl_akhir, kategori, payment):
    df = master.copy()
    if state != "ALL":
        df = df[df["customer_state"] == state]
    df = df[(df["order_purchase_timestamp"] >= tgl_mulai) & (df["order_purchase_timestamp"] <= tgl_akhir)]
    if kategori:
        df = df[df["product_category_name_english"].isin(kategori)]
    if payment != "ALL":
        df = df[df["payment_type"] == payment]

    df_valid = df[df["flag_tanggal_invalid"] == False].copy()

    # ---- KPI ----
    total_revenue = df["price"].sum()
    total_order = df["order_id"].nunique()
    avg_review = df["review_score"].mean()
    avg_durasi = df_valid["durasi_pengiriman_hari"].mean()

    def kpi_card(judul, nilai, warna):
        return dbc.Col(dbc.Card(dbc.CardBody([
            html.H6(judul, className="text-muted"),
            html.H3(nilai)
        ]), color=warna, inverse=True, className="text-center"), md=3)

    kpi = [
        kpi_card("Total Penjualan", f"R$ {total_revenue:,.0f}", "primary"),
        kpi_card("Total Order", f"{total_order:,}", "info"),
        kpi_card("Rata-rata Review", f"{avg_review:.2f} / 5" if not pd.isna(avg_review) else "N/A", "success"),
        kpi_card("Rata-rata Durasi Kirim", f"{avg_durasi:.1f} hari" if not pd.isna(avg_durasi) else "N/A", "warning"),
    ]

    # ---- 1. EFISIENSI PENGIRIMAN ----
    durasi_wilayah = df_valid.groupby("customer_state")["durasi_pengiriman_hari"].mean().sort_values(ascending=False).head(10)
    fig1 = px.bar(durasi_wilayah, title="Rata-rata Durasi Pengiriman per Wilayah (Top 10 Terlama)",
                  labels={"value": "Hari", "customer_state": "Wilayah"}, color_discrete_sequence=["#E74C3C"])
    fig1.update_layout(showlegend=False)

    df_valid["terlambat"] = df_valid["order_delivered_customer_date"] > df_valid["order_estimated_delivery_date"]
    keterlambatan_wilayah = df_valid.groupby("customer_state")["terlambat"].mean().sort_values(ascending=False).head(10) * 100
    fig2 = px.bar(keterlambatan_wilayah, title="Persentase Keterlambatan per Wilayah (Top 10)",
                  labels={"value": "% Terlambat", "customer_state": "Wilayah"}, color_discrete_sequence=["#C0392B"])
    fig2.update_layout(showlegend=False)

    df_valid["selisih_estimasi"] = (df_valid["order_estimated_delivery_date"] - df_valid["order_delivered_customer_date"]).dt.days
    fig3 = px.histogram(df_valid, x="selisih_estimasi", title="Selisih Estimasi vs Aktual Pengiriman (hari, positif = lebih cepat)",
                         color_discrete_sequence=["#3498DB"])

    # ---- 2. PERFORMA PENJUALAN ----
    penjualan_kategori = df.groupby("product_category_name_english")["price"].sum().sort_values(ascending=False)
    fig4 = px.bar(penjualan_kategori.head(10), title="Top 10 Kategori Terbaik (Total Penjualan)",
                  labels={"value": "Total Penjualan (R$)"}, color_discrete_sequence=["#27AE60"])
    fig4.update_layout(showlegend=False)

    fig5 = px.bar(penjualan_kategori.tail(10), title="Bottom 10 Kategori Terburuk (Total Penjualan)",
                  labels={"value": "Total Penjualan (R$)"}, color_discrete_sequence=["#E67E22"])
    fig5.update_layout(showlegend=False)

    penjualan_seller = df.groupby("seller_id")["price"].sum().sort_values(ascending=False)
    fig6 = px.bar(penjualan_seller.head(10), title="Top 10 Seller Terbaik (Total Penjualan)",
                  labels={"value": "Total Penjualan (R$)"}, color_discrete_sequence=["#27AE60"])
    fig6.update_layout(showlegend=False)

    fig7 = px.bar(penjualan_seller.tail(10), title="Bottom 10 Seller Terburuk (Total Penjualan)",
                  labels={"value": "Total Penjualan (R$)"}, color_discrete_sequence=["#E67E22"])
    fig7.update_layout(showlegend=False)

    # ---- 3. KEPUASAN PELANGGAN ----
    durasi_review = df_valid.groupby("review_score")["durasi_pengiriman_hari"].mean()
    fig8 = px.bar(durasi_review, title="Rata-rata Durasi Pengiriman per Skor Review",
                  labels={"value": "Hari", "review_score": "Skor Review"}, color_discrete_sequence=["#9B59B6"])
    fig8.update_layout(showlegend=False)

    top10_kat = penjualan_kategori.head(10).index
    fig9 = px.box(df[df["product_category_name_english"].isin(top10_kat)],
                  x="product_category_name_english", y="review_score",
                  title="Distribusi Skor Review per Kategori (Top 10)", color_discrete_sequence=["#8E44AD"])
    fig9.update_xaxes(tickangle=45)

    review_payment = df.groupby("payment_type")["review_score"].mean().sort_values(ascending=False)
    fig10 = px.bar(review_payment, title="Rata-rata Skor Review per Metode Pembayaran",
                   labels={"value": "Rata-rata Skor"}, color_discrete_sequence=["#2980B9"])
    fig10.update_layout(showlegend=False)

    df["kelompok_harga"] = pd.cut(df["price"], bins=[0, 50, 100, 200, 500, float("inf")],
                                    labels=["<R$50", "R$50-100", "R$100-200", "R$200-500", ">R$500"])
    review_harga = df.groupby("kelompok_harga", observed=True)["review_score"].mean()
    fig11 = px.bar(review_harga, title="Rata-rata Skor Review per Kelompok Harga Produk",
                   labels={"value": "Rata-rata Skor"}, color_discrete_sequence=["#16A085"])
    fig11.update_layout(showlegend=False)

    return kpi, fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8, fig9, fig10, fig11


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
