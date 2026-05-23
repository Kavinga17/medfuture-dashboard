import dash
from dash import dcc, html, dash_table, Input, Output, callback
import requests
import pandas as pd
from datetime import datetime, timedelta, date

# ── App ─────────────────────────────────────────────────────────────────────
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # for gunicorn

# ── API URLs ─────────────────────────────────────────────────────────────────
JOB_API       = "https://stage.medfuture.com.au/medadminapi/public/api/web/job-order-api"
PROSPECT_API  = "https://stage.medfuture.com.au/medadminapi/public/api/web/client-prospect-report-api"
CANDIDATE_API = "https://stage.medfuture.com.au/medadminapi/public/api/web/candidate-report-api"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

# ── Colours ──────────────────────────────────────────────────────────────────
NAVY   = "#1F4E79"
BLUE   = "#2E75B6"
TEAL   = "#1D9E75"
AMBER  = "#BA7517"
PURPLE = "#7F77DD"
RED    = "#A32D2D"
LIGHT_BLUE   = "#E6F1FB"
LIGHT_GREEN  = "#E1F5EE"
LIGHT_AMBER  = "#FAEEDA"
LIGHT_PURPLE = "#EEEDFE"
LIGHT_RED    = "#FCEBEB"
WHITE  = "#FFFFFF"
BG     = "#F4F6F9"
BORDER = "#D9E2EC"

# ── Data fetchers ─────────────────────────────────────────────────────────────
def fetch_jobs():
    try:
        r = requests.get(JOB_API, headers=HEADERS, timeout=30)
        data = r.json()
        rows = []
        for d in data:
            rows.append({
                "submitted_at":   d.get("submitted_at", ""),
                "published_date": d.get("published_date", ""),
                "job_status":     (d.get("job_status") or {}).get("name", ""),
                "division":       (d.get("division_relation") or {}).get("name", ""),
                "state":          (d.get("state_relation") or {}).get("name", ""),
                "profession":     (d.get("profession_relation") or {}).get("name", ""),
                "created_by":     (((d.get("created_by") or {}).get("f_name", "")) + " " +
                                   ((d.get("created_by") or {}).get("l_name", ""))).strip(),
            })
        df = pd.DataFrame(rows)
        df["submitted_at"]   = pd.to_datetime(df["submitted_at"],   errors="coerce")
        df["published_date"] = pd.to_datetime(df["published_date"], errors="coerce")
        return df
    except Exception as e:
        print(f"[fetch_jobs ERROR] {e}")
        return pd.DataFrame()

def fetch_prospects():
    try:
        r = requests.get(PROSPECT_API, headers=HEADERS, timeout=30)
        data = r.json().get("data", [])
        rows = []
        for d in data:
            rows.append({
                "actionDate":    d.get("actionDate", ""),
                "businessName":  d.get("businessName", ""),
                "state":         d.get("state", ""),
                "region":        d.get("region", ""),
                "workingStatus": d.get("workingStatus", ""),
                "bdm":           d.get("businessDevelopmentManager", ""),
            })
        df = pd.DataFrame(rows)
        df["actionDate"] = pd.to_datetime(df["actionDate"], errors="coerce")
        return df
    except Exception as e:
        print(f"[fetch_prospects ERROR] {e}")
        return pd.DataFrame()

def fetch_candidates():
    try:
        r = requests.get(CANDIDATE_API, headers=HEADERS, timeout=30)
        data = r.json()
        rows = []
        for d in data:
            cp  = d.get("candidate_profile", {}) or {}
            sg  = cp.get("staff_group", {}) or {}
            tsc = sg.get("talent_sourcing_consultant") or {}
            rbc = sg.get("recruitment_business_consultant") or {}
            rows.append({
                "activity_date":  d.get("activity_date", ""),
                "working_status": (d.get("working_status") or {}).get("name", ""),
                "candidate_name": (cp.get("first_name", "") + " " + cp.get("last_name", "")).strip(),
                "candidate_id":   cp.get("candidate_id", ""),
                "profession":     (cp.get("profession_relation") or {}).get("name", ""),
                "state":          (cp.get("state_relation") or {}).get("name", ""),
                "department":     (cp.get("department_relation") or {}).get("name", ""),
                "consultant":     ((tsc.get("f_name", "") or "") + " " + (tsc.get("l_name", "") or "")).strip(),
                "rbc":            ((rbc.get("f_name", "") or "") + " " + (rbc.get("l_name", "") or "")).strip(),
            })
        df = pd.DataFrame(rows)
        df["activity_date"] = pd.to_datetime(df["activity_date"], errors="coerce")
        return df
    except Exception as e:
        print(f"[fetch_candidates ERROR] {e}")
        return pd.DataFrame()

# ── Helpers ───────────────────────────────────────────────────────────────────
def kpi_card(value, label, bg, color):
    return html.Div([
        html.Div(str(value), style={"fontSize":"32px","fontWeight":"600","color":color,"lineHeight":"1","marginBottom":"6px"}),
        html.Div(label,      style={"fontSize":"12px","fontWeight":"500","color":color,"opacity":"0.8"}),
    ], style={
        "background":bg,"borderRadius":"10px","padding":"18px 20px",
        "flex":"1","minWidth":"140px","boxSizing":"border-box",
    })

def section_title(text):
    return html.Div(text, style={
        "fontSize":"11px","fontWeight":"600","color":"#6B7A99",
        "textTransform":"uppercase","letterSpacing":"0.06em","marginBottom":"12px",
    })

def card(title, content):
    return html.Div([
        html.Div(title, style={
            "fontSize":"11px","fontWeight":"700","color":"#6B7A99","textTransform":"uppercase",
            "letterSpacing":"0.06em","marginBottom":"12px","paddingBottom":"10px",
            "borderBottom":f"1px solid {BORDER}",
        }),
        content,
    ], style={
        "background":WHITE,"borderRadius":"12px","padding":"16px 18px",
        "border":f"1px solid {BORDER}","boxShadow":"0 1px 4px rgba(0,0,0,0.06)",
    })

def make_table(df, columns, id_key):
    return dash_table.DataTable(
        id=id_key,
        columns=[{"name": c, "id": c} for c in columns],
        data=df[columns].to_dict("records") if not df.empty else [],
        page_size=15,
        sort_action="native",
        style_table={"overflowX":"auto","borderRadius":"10px","border":f"1px solid {BORDER}"},
        style_header={"backgroundColor":NAVY,"color":WHITE,"fontWeight":"600","fontSize":"12px",
                      "textTransform":"uppercase","letterSpacing":"0.04em","padding":"10px 14px","border":"none"},
        style_cell={"fontSize":"12px","padding":"9px 14px","border":f"1px solid {BORDER}",
                    "fontFamily":"system-ui,sans-serif","color":"#2D3748","backgroundColor":WHITE},
        style_data_conditional=[
            {"if":{"row_index":"odd"},"backgroundColor":LIGHT_BLUE},
            {"if":{"state":"selected"},"backgroundColor":"#BFD7F0","border":f"1px solid {BLUE}"},
        ],
    )

def opts(series):
    vals = sorted(v for v in series.dropna().unique() if str(v).strip() and str(v) not in ("N/A", ""))
    return [{"label": v, "value": v} for v in vals]

PERIOD_OPTIONS = [
    {"label": "Today",        "value": "0"},
    {"label": "Last 7 Days",  "value": "7"},
    {"label": "Last 14 Days", "value": "14"},
    {"label": "Last 30 Days", "value": "30"},
]

def period_to_range(value):
    today = date.today()
    start = today if value == "0" else today - timedelta(days=int(value))
    return str(start), str(today)

def date_filter_section(period_id, range_id):
    today = date.today()
    min_d = str(today - timedelta(days=30))
    max_d = str(today)
    start, end = period_to_range("30")
    return html.Div([
        html.Div([
            html.Div("Quick Select", style=LABEL_STYLE),
            dcc.RadioItems(
                id=period_id, options=PERIOD_OPTIONS, value="30", inline=True,
                inputStyle={"display": "none"},
                labelStyle={
                    "padding": "7px 16px", "borderRadius": "20px", "cursor": "pointer",
                    "fontSize": "12px", "fontWeight": "500", "marginRight": "6px",
                    "border": f"1px solid {BORDER}", "color": "#6B7A99",
                    "backgroundColor": WHITE, "userSelect": "none", "transition": "all 0.15s",
                },
                labelClassName="period-btn",
            ),
        ]),
        html.Div(style={"width":"1px","background":BORDER,"alignSelf":"stretch","margin":"0 4px"}),
        html.Div([
            html.Div("Custom Range", style=LABEL_STYLE),
            dcc.DatePickerRange(
                id=range_id,
                start_date=start, end_date=end,
                min_date_allowed=min_d, max_date_allowed=max_d,
                display_format="DD MMM YYYY",
                start_date_placeholder_text="Start date",
                end_date_placeholder_text="End date",
                style={"fontSize": "12px"},
            ),
        ]),
    ], style={"display":"flex","alignItems":"flex-end","gap":"12px","flexWrap":"wrap"})

# ── Shared filter bar styles ──────────────────────────────────────────────────
FILTER_BAR = {
    "background": WHITE, "padding": "14px 16px", "borderRadius": "10px",
    "border": f"1px solid {BORDER}", "marginBottom": "20px",
    "display": "flex", "flexWrap": "wrap", "gap": "16px", "alignItems": "flex-end",
}
LABEL_STYLE = {"fontSize":"11px","fontWeight":"600","color":"#6B7A99","marginBottom":"4px"}
DROP_STYLE  = {"fontSize":"12px","minWidth":"160px"}

def filter_group(label, component):
    return html.Div([
        html.Div(label, style=LABEL_STYLE),
        component,
    ], style={"display":"flex","flexDirection":"column"})

# ── Layout ────────────────────────────────────────────────────────────────────
app.layout = html.Div(style={"fontFamily":"system-ui,-apple-system,sans-serif","background":BG,"minHeight":"100vh"}, children=[

    dcc.Interval(id="refresh", interval=3600*1000, n_intervals=0),

    html.Div(style={
        "background":f"linear-gradient(135deg,{NAVY} 0%,{BLUE} 55%,{TEAL} 100%)",
        "padding":"20px 32px","display":"flex","alignItems":"center","justifyContent":"space-between",
    }, children=[
        html.Div([
            html.Div("MEDFUTURE", style={"fontSize":"11px","color":"rgba(255,255,255,0.7)","letterSpacing":"0.15em","marginBottom":"3px"}),
            html.Div("Daily Dashboard", style={"fontSize":"22px","fontWeight":"500","color":WHITE}),
        ]),
        html.Div(id="last-updated", style={"fontSize":"12px","color":"rgba(255,255,255,0.8)",
            "background":"rgba(255,255,255,0.15)","padding":"6px 14px","borderRadius":"20px"}),
    ]),

    html.Div(style={"background":WHITE,"borderBottom":f"1px solid {BORDER}","padding":"0 32px"}, children=[
        dcc.Tabs(id="tabs", value="jobs", style={"border":"none"}, children=[
            dcc.Tab(label="Job Orders",       value="jobs",
                    style={"fontWeight":"500","padding":"14px 20px","border":"none","color":"#6B7A99"},
                    selected_style={"fontWeight":"600","padding":"14px 20px","border":"none","borderBottom":f"2px solid {NAVY}","color":NAVY}),
            dcc.Tab(label="Candidates",       value="candidates",
                    style={"fontWeight":"500","padding":"14px 20px","border":"none","color":"#6B7A99"},
                    selected_style={"fontWeight":"600","padding":"14px 20px","border":"none","borderBottom":f"2px solid {TEAL}","color":TEAL}),
            dcc.Tab(label="Clients", value="prospects",
                    style={"fontWeight":"500","padding":"14px 20px","border":"none","color":"#6B7A99"},
                    selected_style={"fontWeight":"600","padding":"14px 20px","border":"none","borderBottom":f"2px solid {AMBER}","color":AMBER}),
        ]),
    ]),

    html.Div(id="page-content", style={"padding":"24px 32px"}),
])

# ── Global callbacks ──────────────────────────────────────────────────────────
@callback(Output("last-updated", "children"), Input("refresh", "n_intervals"))
def update_time(_n):
    return f"Last updated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}"

@callback(Output("page-content", "children"), Input("tabs", "value"), Input("refresh", "n_intervals"))
def render_page(tab, _n):
    if tab == "jobs":
        return jobs_page()
    elif tab == "candidates":
        return candidates_page()
    elif tab == "prospects":
        return prospects_page()

# ── Job Orders Page ───────────────────────────────────────────────────────────
def jobs_page():
    return html.Div([
        html.Div(style=FILTER_BAR, children=[
            date_filter_section("job-period", "job-date-range"),
            html.Div(style={"width":"1px","background":BORDER,"alignSelf":"stretch","margin":"0 4px"}),
            filter_group("Division", dcc.Dropdown(
                id="job-filter-division", options=[], value=None,
                multi=True, placeholder="All divisions", style=DROP_STYLE,
            )),
            filter_group("State", dcc.Dropdown(
                id="job-filter-state", options=[], value=None,
                multi=True, placeholder="All states", style=DROP_STYLE,
            )),
            filter_group("Job Status", dcc.Dropdown(
                id="job-filter-status", options=[], value=None,
                multi=True, placeholder="All statuses", style=DROP_STYLE,
            )),
            filter_group("Created By", dcc.Dropdown(
                id="job-filter-person", options=[], value=None,
                multi=True, placeholder="All people", style=DROP_STYLE,
            )),
            html.Div(id="job-summary-text", style={"fontSize":"12px","color":"#6B7A99","marginLeft":"auto","paddingBottom":"2px"}),
        ]),
        html.Div(id="job-kpis"),
        html.Div(id="job-tables"),
    ])

@callback(
    Output("job-date-range", "start_date"),
    Output("job-date-range", "end_date"),
    Input("job-period", "value"),
)
def sync_job_dates(period):
    return period_to_range(period or "30")

@callback(
    Output("job-filter-division", "options"),
    Output("job-filter-state",    "options"),
    Output("job-filter-status",   "options"),
    Output("job-filter-person",   "options"),
    Input("refresh", "n_intervals"),
)
def populate_job_filters(_n):
    df = fetch_jobs()
    if df.empty:
        return [], [], [], []
    return opts(df["division"]), opts(df["state"]), opts(df["job_status"]), opts(df["created_by"])

@callback(
    Output("job-kpis",         "children"),
    Output("job-tables",       "children"),
    Output("job-summary-text", "children"),
    Input("job-date-range",     "start_date"),
    Input("job-date-range",     "end_date"),
    Input("job-filter-division","value"),
    Input("job-filter-state",   "value"),
    Input("job-filter-status",  "value"),
    Input("job-filter-person",  "value"),
    Input("refresh",            "n_intervals"),
)
def update_jobs(start_date, end_date, divisions, states, statuses, persons, _n):
    df = fetch_jobs()
    if df.empty:
        return html.Div("Unable to load data", style={"color":RED}), html.Div(), ""

    start = pd.Timestamp(start_date) if start_date else pd.Timestamp.now() - timedelta(days=30)
    end   = pd.Timestamp(end_date)   + timedelta(days=1) if end_date else pd.Timestamp.now()

    filtered = df[(df["submitted_at"] >= start) & (df["submitted_at"] <= end)].copy()
    if divisions:
        filtered = filtered[filtered["division"].isin(divisions)]
    if states:
        filtered = filtered[filtered["state"].isin(states)]
    if statuses:
        filtered = filtered[filtered["job_status"].isin(statuses)]
    if persons:
        filtered = filtered[filtered["created_by"].isin(persons)]

    pub_filtered = df[(df["published_date"] >= start) & (df["published_date"] <= end)]

    total_submitted = len(filtered)
    total_published = len(pub_filtered.dropna(subset=["published_date"]))

    kpis = html.Div(style={"display":"flex","gap":"12px","flexWrap":"wrap","marginBottom":"20px"}, children=[
        kpi_card(total_submitted, "Total Submitted", LIGHT_BLUE,   NAVY),
        kpi_card(total_published, "Total Published", LIGHT_GREEN,  "#085041"),
        kpi_card(len(filtered[filtered["job_status"]=="Active"]),  "Active",  LIGHT_GREEN, "#0F6E56"),
        kpi_card(len(filtered[filtered["job_status"]=="Expired"]), "Expired", LIGHT_RED,   RED),
        kpi_card(len(filtered[filtered["job_status"]=="Closed"]),  "Closed",  LIGHT_AMBER, "#633806"),
    ])

    if not filtered.empty:
        div_df = filtered.groupby("division").agg(
            Submitted=("submitted_at","count")
        ).reset_index().rename(columns={"division":"Division"})
        div_df = div_df.sort_values("Submitted", ascending=False)
    else:
        div_df = pd.DataFrame(columns=["Division","Submitted"])

    if not filtered.empty:
        person_df = filtered[filtered["created_by"].str.strip() != ""].groupby(["created_by","division"]).agg(
            Total=("submitted_at","count")
        ).reset_index().rename(columns={"created_by":"Created By","division":"Division"})
        person_df = person_df.sort_values("Total", ascending=False)
    else:
        person_df = pd.DataFrame(columns=["Created By","Division","Total"])

    if not filtered.empty:
        state_df = filtered.groupby("state").agg(
            Total=("submitted_at","count")
        ).reset_index().rename(columns={"state":"State"})
        state_df = state_df.sort_values("Total", ascending=False)
    else:
        state_df = pd.DataFrame(columns=["State","Total"])

    tables = html.Div([
        html.Div(style={"display":"grid","gridTemplateColumns":"1fr 1fr 1fr","gap":"16px"}, children=[
            card("By Division",
                make_table(div_df, [c for c in ["Division","Submitted"] if c in div_df.columns], "div-table")),
            card("By State",
                make_table(state_df, [c for c in ["State","Total"] if c in state_df.columns], "state-table")),
            card("By Person (Created By)",
                make_table(person_df, [c for c in ["Created By","Division","Total"] if c in person_df.columns], "person-table")),
        ]),
    ])

    return kpis, tables, f"Showing {total_submitted:,} submitted jobs"

# ── Candidates Page ───────────────────────────────────────────────────────────
def candidates_page():
    return html.Div([
        html.Div(style=FILTER_BAR, children=[
            date_filter_section("cand-period", "cand-date-range"),
            html.Div(style={"width":"1px","background":BORDER,"alignSelf":"stretch","margin":"0 4px"}),
            filter_group("Consultant", dcc.Dropdown(
                id="cand-filter-consultant", options=[], value=None,
                multi=True, placeholder="All consultants", style=DROP_STYLE,
            )),
            filter_group("Working Status", dcc.Dropdown(
                id="cand-filter-status", options=[], value=None,
                multi=True, placeholder="All statuses", style=DROP_STYLE,
            )),
            filter_group("State", dcc.Dropdown(
                id="cand-filter-state", options=[], value=None,
                multi=True, placeholder="All states", style=DROP_STYLE,
            )),
            filter_group("Profession", dcc.Dropdown(
                id="cand-filter-profession", options=[], value=None,
                multi=True, placeholder="All professions", style=DROP_STYLE,
            )),
        ]),
        html.Div(id="cand-kpis"),
        html.Div(id="cand-tables"),
    ])

@callback(
    Output("cand-date-range", "start_date"),
    Output("cand-date-range", "end_date"),
    Input("cand-period", "value"),
)
def sync_cand_dates(period):
    return period_to_range(period or "30")

@callback(
    Output("cand-filter-consultant", "options"),
    Output("cand-filter-status",     "options"),
    Output("cand-filter-state",      "options"),
    Output("cand-filter-profession", "options"),
    Input("refresh", "n_intervals"),
)
def populate_cand_filters(_n):
    df = fetch_candidates()
    if df.empty:
        return [], [], [], []
    return opts(df["consultant"]), opts(df["working_status"]), opts(df["state"]), opts(df["profession"])

@callback(
    Output("cand-kpis",   "children"),
    Output("cand-tables", "children"),
    Input("cand-date-range",        "start_date"),
    Input("cand-date-range",        "end_date"),
    Input("cand-filter-consultant", "value"),
    Input("cand-filter-status",     "value"),
    Input("cand-filter-state",      "value"),
    Input("cand-filter-profession", "value"),
    Input("refresh",                "n_intervals"),
)
def update_candidates(start_date, end_date, consultants, statuses, states, professions, _n):
    df = fetch_candidates()
    if df.empty:
        return html.Div("Unable to load data", style={"color":RED}), html.Div()

    start = pd.Timestamp(start_date) if start_date else pd.Timestamp.now() - timedelta(days=30)
    end   = pd.Timestamp(end_date)   + timedelta(days=1) if end_date else pd.Timestamp.now()
    filtered = df[(df["activity_date"] >= start) & (df["activity_date"] <= end)].copy()
    if consultants:
        filtered = filtered[filtered["consultant"].isin(consultants)]
    if statuses:
        filtered = filtered[filtered["working_status"].isin(statuses)]
    if states:
        filtered = filtered[filtered["state"].isin(states)]
    if professions:
        filtered = filtered[filtered["profession"].isin(professions)]

    def count_status(s):
        return len(filtered[filtered["working_status"] == s]) if not filtered.empty else 0

    kpis = html.Div(style={"display":"flex","gap":"12px","flexWrap":"wrap","marginBottom":"20px"}, children=[
        kpi_card(count_status("Submissions"),         "Submissions",         LIGHT_BLUE,   NAVY),
        kpi_card(count_status("Initial Screening"),   "Initial Screening",   LIGHT_PURPLE, "#3C3489"),
        kpi_card(count_status("Job Matching"),        "Job Matching",        LIGHT_GREEN,  "#085041"),
        kpi_card(count_status("Interview Scheduled"), "Interview Scheduled", LIGHT_AMBER,  "#633806"),
        kpi_card(count_status("Interviewed"),         "Interviewed",         LIGHT_AMBER,  "#854F0B"),
        kpi_card(count_status("Offered"),             "Offered",             LIGHT_GREEN,  "#0F6E56"),
        kpi_card(count_status("Placement"),           "Placement",           LIGHT_GREEN,  "#085041"),
        kpi_card(count_status("Declined"),            "Declined",            LIGHT_RED,    RED),
    ])

    if not filtered.empty:
        ws_df = filtered.groupby("working_status").agg(
            Count=("activity_date","count")
        ).reset_index().rename(columns={"working_status":"Working Status"})
        ws_df = ws_df.sort_values("Count", ascending=False)
    else:
        ws_df = pd.DataFrame(columns=["Working Status","Count"])

    if not filtered.empty:
        cons_df = filtered[filtered["consultant"].str.strip() != ""].groupby(["consultant","working_status"]).agg(
            Total=("activity_date","count")
        ).reset_index().rename(columns={"consultant":"Consultant","working_status":"Working Status"})
        cons_df = cons_df.sort_values("Total", ascending=False)
    else:
        cons_df = pd.DataFrame(columns=["Consultant","Working Status","Total"])

    if not filtered.empty:
        act_df = filtered[["candidate_name","profession","state","department","working_status","consultant","activity_date"]].copy()
        act_df["activity_date"] = act_df["activity_date"].dt.strftime("%d %b %Y %H:%M")
        act_df.columns = ["Candidate","Profession","State","Department","Working Status","Consultant","Activity Date"]
        act_df = act_df.sort_values("Activity Date", ascending=False)
    else:
        act_df = pd.DataFrame(columns=["Candidate","Profession","State","Department","Working Status","Consultant","Activity Date"])

    tables = html.Div([
        html.Div(style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"16px","marginBottom":"16px"}, children=[
            card("Working Status Summary",
                make_table(ws_df, [c for c in ["Working Status","Count"] if c in ws_df.columns], "ws-table")),
            card("By Consultant",
                make_table(cons_df, [c for c in ["Consultant","Working Status","Total"] if c in cons_df.columns], "cons-table")),
        ]),
        card("Candidate Activity",
            make_table(act_df, [c for c in ["Candidate","Profession","State","Department","Working Status","Consultant","Activity Date"] if c in act_df.columns], "act-table")),
    ])

    return kpis, tables

# ── Prospects Page ────────────────────────────────────────────────────────────
def prospects_page():
    return html.Div([
        html.Div(style=FILTER_BAR, children=[
            date_filter_section("pros-period", "pros-date-range"),
            html.Div(style={"width":"1px","background":BORDER,"alignSelf":"stretch","margin":"0 4px"}),
            filter_group("Assigned To", dcc.Dropdown(
                id="pros-filter-bdm", options=[], value=None,
                multi=True, placeholder="All Staff", style=DROP_STYLE,
            )),
            filter_group("Status", dcc.Dropdown(
                id="pros-filter-status", options=[], value=None,
                multi=True, placeholder="All statuses", style=DROP_STYLE,
            )),
            filter_group("State", dcc.Dropdown(
                id="pros-filter-state", options=[], value=None,
                multi=True, placeholder="All states", style=DROP_STYLE,
            )),
        ]),
        html.Div(id="pros-kpis"),
        html.Div(id="pros-tables"),
    ])

@callback(
    Output("pros-date-range", "start_date"),
    Output("pros-date-range", "end_date"),
    Input("pros-period", "value"),
)
def sync_pros_dates(period):
    return period_to_range(period or "30")

@callback(
    Output("pros-filter-bdm",    "options"),
    Output("pros-filter-status", "options"),
    Output("pros-filter-state",  "options"),
    Input("refresh", "n_intervals"),
)
def populate_pros_filters(_n):
    df = fetch_prospects()
    if df.empty:
        return [], [], []
    return opts(df["bdm"]), opts(df["workingStatus"]), opts(df["state"])

@callback(
    Output("pros-kpis",   "children"),
    Output("pros-tables", "children"),
    Input("pros-date-range",    "start_date"),
    Input("pros-date-range",    "end_date"),
    Input("pros-filter-bdm",    "value"),
    Input("pros-filter-status", "value"),
    Input("pros-filter-state",  "value"),
    Input("refresh",            "n_intervals"),
)
def update_prospects(start_date, end_date, bdms, statuses, states, _n):
    df = fetch_prospects()
    if df.empty:
        return html.Div("Unable to load data", style={"color":RED}), html.Div()

    start = pd.Timestamp(start_date) if start_date else pd.Timestamp.now() - timedelta(days=30)
    end   = pd.Timestamp(end_date)   + timedelta(days=1) if end_date else pd.Timestamp.now()
    filtered = df[(df["actionDate"] >= start) & (df["actionDate"] <= end)].copy()
    if bdms:
        filtered = filtered[filtered["bdm"].isin(bdms)]
    if statuses:
        filtered = filtered[filtered["workingStatus"].isin(statuses)]
    if states:
        filtered = filtered[filtered["state"].isin(states)]

    total    = len(filtered)
    proposed = len(filtered[filtered["workingStatus"] == "Proposed"])
    tapped   = len(filtered[filtered["workingStatus"] == "Tapped"])


    kpis = html.Div(style={"display":"flex","gap":"12px","flexWrap":"wrap","marginBottom":"20px"}, children=[
        kpi_card(total,    "Total Clients", LIGHT_BLUE,  NAVY),
        kpi_card(proposed, "Proposed",        LIGHT_GREEN, "#085041"),
        kpi_card(tapped,   "Tapped",          LIGHT_AMBER, "#633806"),
    ])

    if not filtered.empty:
        bdm_df = filtered[~filtered["bdm"].isin(["N/A",""])].groupby(["bdm","workingStatus"]).agg(
            Count=("actionDate","count")
        ).reset_index().rename(columns={"bdm":"Assigned To","workingStatus":"Status"})
        bdm_df = bdm_df.sort_values("Count", ascending=False)
    else:
        bdm_df = pd.DataFrame(columns=["Assigned To","Status","Count"])

    if not filtered.empty:
        st_df = filtered[~filtered["state"].isin(["N/A",""])].groupby("state").agg(
            Count=("actionDate","count")
        ).reset_index().rename(columns={"state":"State"})
        st_df = st_df.sort_values("Count", ascending=False)
    else:
        st_df = pd.DataFrame(columns=["State","Count"])

    if not filtered.empty:
        rec_df = filtered[["businessName","state","workingStatus","bdm","actionDate"]].copy()
        rec_df["actionDate"] = rec_df["actionDate"].dt.strftime("%d %b %Y")
        rec_df.columns = ["Business Name","State","Status","Assigned To","Date"]
        rec_df = rec_df.sort_values("Date", ascending=False).head(50)
    else:
        rec_df = pd.DataFrame(columns=["Business Name","State","Status","Assigned To","Date"])

    tables = html.Div([
        html.Div(style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"16px","marginBottom":"16px"}, children=[
            card("By Assigned Staff",
                make_table(bdm_df, [c for c in ["Assigned To","Status","Count"] if c in bdm_df.columns], "bdm-table")),
            card("By State",
                make_table(st_df, [c for c in ["State","Count"] if c in st_df.columns], "st-table")),
        ]),
        card("Client Activity",
            make_table(rec_df, [c for c in ["Business Name","State","Status","Assigned To","Date"] if c in rec_df.columns], "rec-table")),
    ])

    return kpis, tables

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
