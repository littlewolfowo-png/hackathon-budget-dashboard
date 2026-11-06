
import streamlit as st
import pandas as pd
import plotly.express as px
import json
import io

from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from google.oauth2 import service_account
from googleapiclient.discovery import build

# =====================================
# 模組四：智慧預算管理系統
# =====================================

st.set_page_config(
    page_title="智慧預算管理系統",
    page_icon="📊",
    layout="wide"
)

# =====================================
# 1. Google Drive 設定
# =====================================

DRIVE_FOLDER_ID = "1xXqMsySR-O0BJU5hGyNS0ZlUqOqmayT1"

DATA_SOURCE_LABEL = "Google Drive：模組二最終資料"

# 使用 Streamlit Secrets 建立 Google 服務帳戶
try:
    credentials = service_account.Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )

    drive_service = build(
        "drive",
        "v3",
        credentials=credentials,
        cache_discovery=False
    )

    drive_connected = True

except Exception as e:
    drive_service = None
    drive_connected = False
    drive_connection_error = str(e)


# =====================================
# 2. Google Drive 檔案讀取函式
# =====================================

def find_drive_file(filename):

    results = drive_service.files().list(
        q=(
            f"'{DRIVE_FOLDER_ID}' in parents "
            f"and name = '{filename}' "
            f"and trashed = false"
        ),
        spaces="drive",
        fields="files(id, name)",
        pageSize=10,
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()

    files = results.get("files", [])

    if not files:
        raise FileNotFoundError(f"Google Drive 找不到檔案：{filename}")

    return files[0]["id"]


def download_drive_file(filename):

    file_id = find_drive_file(filename)

    request = drive_service.files().get_media(
        fileId=file_id,
        supportsAllDrives=True
    )

    return request.execute()


@st.cache_data
def load_csv(file_content, filename):

    for encoding in ["utf-8-sig", "utf-8", "big5"]:

        try:
            return pd.read_csv(
                io.BytesIO(file_content),
                encoding=encoding
            )

        except UnicodeDecodeError:
            continue

    raise ValueError(f"無法辨識 CSV 編碼：{filename}")


@st.cache_data
def load_json(file_content):

    return json.loads(
        file_content.decode("utf-8-sig")
    )


# =====================================
# 3. 載入模組二 CSV
# =====================================

csv_files = {
    "年度總覽": "dashboard_summary_2026.csv",
    "部門分析": "dashboard_departments_2026.csv",
    "科目分析": "dashboard_categories_2026.csv",
    "年度回測": "dashboard_backtesting_2026.csv",
    "科目回測": "backtest_categories_2026.csv",
    "部門回測": "backtest_departments_2026.csv",
    "回測指標": "backtest_metrics_2026.csv"
}

csv_data = {}
csv_errors = {}

for name, filename in csv_files.items():

    if drive_connected:

        try:
            file_content = download_drive_file(filename)

            csv_data[name] = load_csv(
                file_content,
                filename
            )

        except Exception as e:
            csv_errors[name] = str(e)

    else:
        csv_errors[name] = "Google Drive 連線失敗"


# =====================================
# 4. 載入模組三 JSON
# =====================================

json_files = {
    "完整財務分析": "financial_analysis_2026.json",
    "AI 財務摘要": "llm_financial_context.json"
}

json_data = {}
json_errors = {}

for name, filename in json_files.items():

    if drive_connected:

        try:
            file_content = download_drive_file(filename)

            json_data[name] = load_json(file_content)

        except Exception as e:
            json_errors[name] = str(e)

    else:
        json_errors[name] = "Google Drive 連線失敗"


# =====================================
# 5. 網頁標題
# =====================================

st.title("📊 智慧預算管理與 AI 財務顧問")
st.subheader("企業年度預算監控儀表板")

st.markdown("---")



# =====================================
# 6. 資料讀取狀態
# =====================================

col1, col2, col3 = st.columns(3)

col1.metric("成功讀取 CSV", f"{len(csv_data)} / 7")
col2.metric("成功讀取 JSON", f"{len(json_data)} / 2")
col3.metric(
    "Google Drive 狀態",
    "正常" if drive_connected else "無法連線"
)

if csv_errors or json_errors:
    with st.expander("⚠️ 查看資料讀取問題"):
        for name, error in csv_errors.items():
            st.error(f"{name}：{error}")

        for name, error in json_errors.items():
            st.error(f"{name}：{error}")

# =====================================
# 7. 側邊欄功能選單
# =====================================

st.sidebar.title("功能選單")

page = st.sidebar.radio(
    "請選擇功能",
    [
        "年度預算總覽",
        "部門預算分析",
        "科目預算分析",
        "AI 財務顧問",
        "資料檢查"
    ]
)

# =====================================
# 財務 KPI：讀取模組二真實數據
# =====================================

if "年度總覽" in csv_data and not csv_data["年度總覽"].empty:

    summary = csv_data["年度總覽"].iloc[0]

    annual_budget = float(summary["annual_budget"])
    forecast_spending = float(summary["forecast_annual_spending"])
    forecast_variance = float(summary["forecast_net_variance"])
    variance_rate = float(summary["forecast_variance_rate_pct"])

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("全年預算", f"NT$ {annual_budget:,.0f}")

    col2.metric("預測全年支出", f"NT$ {forecast_spending:,.0f}")

    col3.metric(
     "預測差異",
    f"NT$ {forecast_variance:,.0f}",
    delta="超出預算" if forecast_variance > 0 else "低於預算",
    delta_color="inverse"
    )

    col4.metric(
         "預測差異率",
    f"{variance_rate:.2f}%",
    delta="需注意" if variance_rate > 0 else "正常",
    delta_color="inverse"
    )

st.markdown("---")



# =====================================
# 8. 年度預算總覽
# =====================================

if page == "年度預算總覽":

    st.header("📈 年度預算總覽")

    if "年度總覽" in csv_data and not csv_data["年度總覽"].empty:

        df = csv_data["年度總覽"]
        summary = df.iloc[0]

        st.success("已成功讀取模組二年度總覽資料")

        # -----------------------------
        # 1. 年度財務 KPI
        # -----------------------------

        # 重新依照金額計算差異率，避免不清楚原始差異率的分母
        if annual_budget != 0:
            calculated_rate = (
                forecast_variance / annual_budget
            ) * 100
        else:
            calculated_rate = 0

        st.subheader("年度財務指標")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "全年既定預算",
            f"NT$ {annual_budget:,.0f}"
        )

        col2.metric(
            "AI 預測全年支出",
            f"NT$ {forecast_spending:,.0f}"
        )

        col3.metric(
            "預測差異金額",
            f"NT$ {forecast_variance:+,.0f}"
        )

        col4.metric(
            "預測差異率",
            f"{calculated_rate:+.2f}%"
        )

        st.markdown("---")

        # -----------------------------
        # 2. 年度預算風險燈號
        # -----------------------------

        st.subheader("🚦 年度預算風險燈號")

        # 優先讀取模組二是否有提供年度風險燈號
        original_risk = str(
            summary.get("年度風險燈號", "")
        ).strip()

        if "藍" in original_risk:
            light_status = "藍燈"
            light_color = "#3B82F6"
            light_message = "模組二判定為藍燈，請參考原始風險定義。"

        elif forecast_variance > 0:
            light_status = "紅燈"
            light_color = "#EF4444"
            light_message = (
                f"AI 預測支出高於既定預算 "
                f"NT$ {forecast_variance:,.0f}，"
                f"預測超支 {calculated_rate:.2f}%。"
            )

        elif calculated_rate <= -10:
            light_status = "綠燈"
            light_color = "#22C55E"
            light_message = (
                f"AI 預測支出低於既定預算 "
                f"NT$ {abs(forecast_variance):,.0f}，"
                f"低於預算 {abs(calculated_rate):.2f}%。"
            )

        else:
            light_status = "黃燈"
            light_color = "#EAB308"
            light_message = (
                f"AI 預測支出低於既定預算 "
                f"NT$ {abs(forecast_variance):,.0f}，"
                f"差異率 {calculated_rate:.2f}%，"
                f"建議持續觀察。"
            )

        # 四顆燈，只點亮目前狀態
        light_colors = {
            "紅燈": "#EF4444" if light_status == "紅燈" else "#444444",
            "黃燈": "#EAB308" if light_status == "黃燈" else "#444444",
            "綠燈": "#22C55E" if light_status == "綠燈" else "#444444",
            "藍燈": "#3B82F6" if light_status == "藍燈" else "#444444"
        }

        
        # 四色交通號誌
        light_colors = {
            "紅燈": "#EF4444",
            "黃燈": "#EAB308",
            "綠燈": "#22C55E",
            "藍燈": "#3B82F6"
        }

        traffic_lights = ""

        for name, color in light_colors.items():

            current_color = (
                color if light_status == name else "#444444"
            )

            traffic_lights += f"""
                <div style="
                    width:30px;
                    height:30px;
                    border-radius:50%;
                    background:{current_color};
                    box-shadow:0 0 10px {current_color};
                "></div>
            """

        
        st.html(
            f"""
            <div style="
                display:flex;
                align-items:center;
                gap:24px;
                background:#202124;
                padding:22px;
                border-radius:16px;
                max-width:750px;
            ">
                <div style="
                    background:#090909;
                    padding:12px;
                    border-radius:30px;
                    display:flex;
                    flex-direction:column;
                    gap:9px;
                ">
                    {traffic_lights}
                </div>

                <div style="color:white;">
                    <h2 style="margin:0;color:{light_color};">
                        {light_status}
                    </h2>
                    <p style="margin-top:10px;line-height:1.7;">
                        {light_message}
                    </p>
                    <small style="color:#AAAAAA;">
                        比較基準：既定全年預算
                    </small>
                </div>
            </div>
            """
        )


        st.markdown("---")

        # -----------------------------
        # 3. 年度預算與預測支出比較
        # -----------------------------

        st.subheader("📊 年度預算與 AI 預測支出比較")

        comparison_df = pd.DataFrame({
            "項目": ["全年既定預算", "AI 預測全年支出"],
            "金額": [annual_budget, forecast_spending]
        })

        fig = px.bar(
            comparison_df,
            x="項目",
            y="金額",
            color="項目",
            text="金額",
            title="全年既定預算 vs AI 預測全年支出",
            color_discrete_sequence=["#60A5FA", "#F59E0B"]
        )

        fig.update_traces(
            texttemplate="NT$ %{y:,.0f}",
            textposition="outside",
            cliponaxis=False,
            width=0.35
        )

        fig.update_layout(
            yaxis_title="金額（NT$）",
            xaxis_title="",
            showlegend=False,
            yaxis_range=[
                0,
                max(annual_budget, forecast_spending) * 1.2
            ]
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False}
        )

        # -----------------------------
        # 4. 原始資料
        # -----------------------------

        with st.expander("查看年度總覽原始資料"):
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

    else:
        st.warning("目前無法讀取年度總覽 CSV")

# =====================================
# 9. 部門預算分析
# =====================================

elif page == "部門預算分析":

    st.header("🏢 部門預算分析")

    if "部門分析" in csv_data:

        df = csv_data["部門分析"].copy()

        st.success(f"已成功讀取模組二部門分析資料，共 {len(df)} 個部門")

        # 欄位設定
        dept_col = "部門"
        budget_col = "全年總預算_現況"
        actual_col = "當月實際支出"
        variance_col = "c.累積預算差異金額"
        execution_col = "e.預算執行率(%)"
        forecast_col = "e.預測全年總支出"
        risk_col = "部門風險燈號"

        # 數字轉換
        for col in [
            budget_col,
            actual_col,
            variance_col,
            execution_col,
            forecast_col
        ]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # =========================
        # 部門 KPI
        # =========================

        st.subheader("📊 部門整體指標")

        c1, c2, c3, c4 = st.columns(4)

        if budget_col in df.columns:
            c1.metric(
                "部門全年預算",
                f"NT$ {df[budget_col].sum():,.0f}"
            )

        if actual_col in df.columns:
            c2.metric(
                "當月實際支出",
                f"NT$ {df[actual_col].sum():,.0f}"
            )

        if variance_col in df.columns:
            c3.metric(
                "累積預算差異",
                f"NT$ {df[variance_col].sum():,.0f}"
            )

        if execution_col in df.columns:
            c4.metric(
                "平均預算執行率",
                f"{df[execution_col].mean():.2f}%"
            )

        # =========================
        # 預算與預測支出比較
        # =========================

        st.subheader("📈 各部門預算與預測支出")

        if dept_col in df.columns and all(
            col in df.columns for col in [budget_col, forecast_col]
        ):

            chart_df = df[
                [dept_col, budget_col, forecast_col]
            ].melt(
                id_vars=dept_col,
                var_name="項目",
                value_name="金額"
            )

            fig = px.bar(
                chart_df,
                x=dept_col,
                y="金額",
                color="項目",
                barmode="group",
                title="各部門全年預算與預測全年支出比較"
            )

            st.plotly_chart(fig, use_container_width=True)

        # =========================
        # 預算執行率
        # =========================

        st.subheader("📊 各部門預算執行率")

        if dept_col in df.columns and execution_col in df.columns:

            fig = px.bar(
                df,
                x=dept_col,
                y=execution_col,
                title="各部門預算執行率（%）"
            )

            fig.add_hline(
                y=100,
                line_dash="dash",
                annotation_text="100% 預算基準"
            )

            st.plotly_chart(fig, use_container_width=True)

        # =========================
        # 部門風險燈號
        # =========================

        st.subheader("🚦 部門風險燈號")

        risk_columns = [
            dept_col,
            risk_col,
            "最高風險分數",
            "紅燈項目數",
            "黃燈項目數",
            "綠燈項目數",
            "藍燈項目數",
            "異常支出項目數"
        ]

        available_columns = [
            col for col in risk_columns if col in df.columns
        ]

        if available_columns:
            risk_df = df[available_columns].copy()

            # 風險燈號顏色設定
            risk_color_style = JsCode("""
                function(params) {
                    const value = String(params.value || "");

                    if (value.includes("紅")) {
                        return {
                            'backgroundColor': '#FEE2E2',
                            'color': '#B91C1C',
                            'fontWeight': 'bold'
                        };
                    }
                    if (value.includes("黃")) {
                        return {
                            'backgroundColor': '#FEF3C7',
                            'color': '#92400E',
                            'fontWeight': 'bold'
                        };
                    }
                    if (value.includes("綠")) {
                        return {
                            'backgroundColor': '#DCFCE7',
                            'color': '#166534',
                            'fontWeight': 'bold'
                        };
                    }
                    if (value.includes("藍")) {
                        return {
                            'backgroundColor': '#DBEAFE',
                            'color': '#1D4ED8',
                            'fontWeight': 'bold'
                        };
                    }
                    return {};
                }
            """)

            gb = GridOptionsBuilder.from_dataframe(risk_df)

            gb.configure_default_column(
                resizable=True,
                sortable=True,
                filter=True
            )

            # 固定最左側部門欄位
            gb.configure_column(
                dept_col,
                pinned="left",
                lockPinned=True,
                minWidth=150
            )

            # 風險燈號欄位上色
            if risk_col in risk_df.columns:
                gb.configure_column(
                    risk_col,
                    cellStyle=risk_color_style,
                    minWidth=120
                )

            AgGrid(
                risk_df,
                gridOptions=gb.build(),
                height=350,
                fit_columns_on_grid_load=False,
                theme="streamlit",
                allow_unsafe_jscode=True
            )

                # =========================
        # 完整資料
        # =========================

                with st.expander("查看部門完整分析資料"):
            st.write("資料筆數：", len(df))
            st.write("欄位名稱：", df.columns.tolist())
            st.dataframe(df, use_container_width=True)

    else:
        st.warning("目前無法讀取部門分析 CSV")


# =====================================
# 10. 科目預算分析
# =====================================

elif page == "科目預算分析":

    st.header("📋 科目預算分析")
    if "科目分析" in csv_data:

        df = csv_data["科目分析"].copy()

        st.success(f"已成功讀取模組二科目分析資料，共 {len(df)} 筆")

        # 欄位設定
        dept_col = "部門"
        category_col = "費用項目"
        budget_col = "全年總預算_現況"
        actual_col = "當月實際支出"
        variance_col = "c.累積預算差異金額"
        execution_col = "e.預算執行率(%)"
        forecast_col = "e.預測全年總支出"
        forecast_variance_col = "f.預測全年差異金額"
        risk_col = "a.風險燈號"
        quality_col = "d.資料品質評分"

        # 數值欄位轉換
        numeric_columns = [
            budget_col,
            actual_col,
            variance_col,
            execution_col,
            forecast_col,
            forecast_variance_col,
            quality_col
        ]

        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col], errors="coerce"
                )

        # =========================
        # 科目整體 KPI
        # =========================

        st.subheader("📊 科目整體指標")

        c1, c2, c3, c4 = st.columns(4)

        if budget_col in df.columns:
            c1.metric(
                "全年預算合計",
                f"NT$ {df[budget_col].sum():,.0f}"
            )

        if actual_col in df.columns:
            c2.metric(
                "當月實際支出",
                f"NT$ {df[actual_col].sum():,.0f}"
            )

        if variance_col in df.columns:
            c3.metric(
                "累積預算差異",
                f"NT$ {df[variance_col].sum():,.0f}"
            )

        if execution_col in df.columns:
            c4.metric(
                "平均預算執行率",
                f"{df[execution_col].mean():.2f}%"
            )

        st.markdown("---")

        # =========================
        # 各費用項目預算與預測支出
        # =========================

        st.subheader("📈 各費用項目全年預算與預測支出")

        if all(
            col in df.columns
            for col in [category_col, budget_col, forecast_col]
        ):

            chart_df = df.groupby(
                category_col
            )[[budget_col, forecast_col]].sum().reset_index()

            chart_df = chart_df.melt(
                id_vars=category_col,
                var_name="項目",
                value_name="金額"
            )

            fig = px.bar(
                chart_df,
                x=category_col,
                y="金額",
                color="項目",
                barmode="group",
                title="各費用項目全年預算與預測支出比較"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # =========================
        # 各費用項目當月實際支出
        # =========================

        st.subheader("💰 各費用項目當月實際支出")

        if category_col in df.columns and actual_col in df.columns:

            monthly_df = df.groupby(
                category_col
            )[actual_col].sum().reset_index()

            fig = px.bar(
                monthly_df,
                x=category_col,
                y=actual_col,
                title="各費用項目當月實際支出比較"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # =========================
        # 累積預算差異
        # =========================

        st.subheader("📊 各費用項目累積預算差異")

        if category_col in df.columns and variance_col in df.columns:

            variance_df = df.groupby(
                category_col
            )[variance_col].sum().reset_index()

            fig = px.bar(
                variance_df,
                x=category_col,
                y=variance_col,
                title="各費用項目累積預算差異金額"
            )

            fig.add_hline(
                y=0,
                line_dash="dash"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # =========================
        # 預算執行率
        # =========================

        st.subheader("📉 各費用項目預算執行率")

        if category_col in df.columns and execution_col in df.columns:

            execution_df = df.groupby(
                category_col
            )[execution_col].mean().reset_index()

            fig = px.bar(
                execution_df,
                x=category_col,
                y=execution_col,
                title="各費用項目平均預算執行率（%）"
            )

            fig.add_hline(
                y=100,
                line_dash="dash",
                annotation_text="100% 預算基準"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # =========================
        # 費用項目風險燈號
        # =========================

        st.subheader("🚦 各費用項目風險燈號")

        if category_col in df.columns and risk_col in df.columns:

            risk_df = pd.crosstab(
                df[category_col],
                df[risk_col]
            ).reset_index()

            fig = px.bar(
                risk_df,
                x=category_col,
                y=[
                    col for col in risk_df.columns
                    if col != category_col
                ],
                title="各費用項目風險燈號比較",
                barmode="stack"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            st.dataframe(
                risk_df,
                use_container_width=True
            )

        # =========================
        # 資料品質評分
        # =========================

        st.subheader("🔍 各費用項目資料品質")

        if category_col in df.columns and quality_col in df.columns:

            quality_df = df.groupby(
                category_col
            )[quality_col].mean().reset_index()

            fig = px.bar(
                quality_df,
                x=category_col,
                y=quality_col,
                title="各費用項目平均資料品質評分"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # =========================
        # 完整資料
        # =========================

        with st.expander("查看科目完整分析資料"):
            st.dataframe(
                df,
                use_container_width=True
            )

    else:
        st.warning("目前無法讀取科目分析 CSV")





# =====================================
# 11. AI 財務顧問
# =====================================

elif page == "AI 財務顧問":

    st.header("🤖 AI 財務顧問")
    st.caption("根據模組三財務分析資料，提供企業預算風險與管理決策參考")

    if "AI 財務摘要" not in json_data:
        st.warning("目前無法讀取 AI 財務摘要 JSON")

    else:
        # 直接讀取模組三的 AI 財務摘要 JSON
        data = json_data["AI 財務摘要"]

        # 讀取各項資料
        company = data.get("company_summary", {})
        risks = data.get("risk_summary", {})
        departments = data.get("department_risks", [])
        high_risks = data.get("high_priority_risks", [])
        anomalies = data.get("monthly_anomalies", [])
        backtest = data.get("backtesting_summary", {})

        st.success("已成功讀取模組三完整財務分析資料")

        # ---------------------------------
        # 1. 公司財務總覽
        # ---------------------------------

        st.subheader("📊 公司財務總覽")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "全年預算",
            f"NT$ {company.get('annual_budget', 0):,.0f}"
        )

        c2.metric(
            "預測全年支出",
            f"NT$ {company.get('forecast_annual_spending', 0):,.0f}"
        )

        c3.metric(
            "預測淨差異",
            f"NT$ {company.get('forecast_net_variance', 0):,.0f}",
            delta="超出預算" if company.get("forecast_net_variance", 0) > 0 else "低於預算",
            delta_color="inverse"
        )

        c4.metric(
            "預測差異率",
            f"{company.get('forecast_variance_rate_pct', 0):.2f}%"
        )

        st.markdown("---")

        
        # ---------------------------------
        # 2. 全公司風險概況
        # ---------------------------------

        st.subheader("🚦 全公司風險概況")

        # 讀取原始風險統計
        red_count = risks.get("red_count", 0)
        yellow_count = risks.get("yellow_count", 0)
        green_count = risks.get("green_count", 0)
        blue_count = risks.get("blue_count", 0)

        # 四色風險卡片
        risk_cards = [
            ("紅燈", red_count, "#EF4444"),
            ("黃燈", yellow_count, "#EAB308"),
            ("綠燈", green_count, "#22C55E"),
            ("藍燈", blue_count, "#3B82F6")
        ]

        cards_html = ""

        for label, count, color in risk_cards:

            cards_html += f"""
            <div style="
                flex:1;
                min-width:120px;
                background:#202124;
                border:2px solid {color};
                border-radius:14px;
                padding:18px;
                box-shadow:0 0 12px {color}55;
                text-align:center;
            ">
                <div style="
                    color:{color};
                    font-size:17px;
                    font-weight:bold;
                ">
                    ● {label}
                </div>

                <div style="
                    color:white;
                    font-size:32px;
                    font-weight:bold;
                    margin-top:10px;
                ">
                    {count}
                </div>

                <div style="
                    color:#AAAAAA;
                    font-size:12px;
                ">
                    風險項目
                </div>
            </div>
            """

        st.html(
            f"""
            <div style="
                display:flex;
                flex-wrap:wrap;
                gap:14px;
                width:100%;
            ">
                {cards_html}
            </div>
            """
        )

        # 異常支出與資料品質
        st.markdown("### 📋 其他風險指標")

        anomaly_count = risks.get("anomaly_count", 0)
        quality_score = risks.get(
            "average_data_quality_score", 0
        )

        a1, a2 = st.columns(2)

        a1.metric(
            "異常支出項目",
            anomaly_count
        )

        a2.metric(
            "平均資料品質評分",
            quality_score
        )

        st.markdown("---")


        # ---------------------------------
        # 3. 部門風險分析
        # ---------------------------------

        st.subheader("🏢 各部門風險分析")

        if departments:
            dept_df = pd.DataFrame(departments)

            st.dataframe(
                dept_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("目前沒有部門風險資料")

        # ---------------------------------
        # 4. 高優先風險項目
        # ---------------------------------

        st.subheader("⚠️ 高優先風險項目")

        if high_risks:
            risk_df = pd.DataFrame(high_risks)

            show_columns = [
                "部門",
                "費用項目",
                "a.風險燈號",
                "預測全年差異金額",
                "預測全年差異率(%)",
                "b.預測超支金額",
                "異常原因"
            ]

            available_columns = [
                col for col in show_columns
                if col in risk_df.columns
            ]

            st.dataframe(
                risk_df[available_columns],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("目前沒有高優先風險項目")

        # ---------------------------------
        # 5. 異常支出分析
        # ---------------------------------

        st.subheader("🔍 當月異常支出明細")

        if anomalies:
            anomaly_df = pd.DataFrame(anomalies)

            anomaly_columns = [
                "部門",
                "費用項目",
                "a.風險燈號",
                "當月預算",
                "當月實際支出",
                "當月預算差異率(%)",
                "異常原因"
            ]

            available_columns = [
                col for col in anomaly_columns
                if col in anomaly_df.columns
            ]

            st.dataframe(
                anomaly_df[available_columns],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("目前沒有異常支出紀錄")

        # ---------------------------------
        # 6. 預算預測回測績效
        # ---------------------------------

        st.subheader("📈 預算預測回測績效")

        b1, b2, b3 = st.columns(3)

        b1.metric(
            "WAPE",
            f"{backtest.get('rolling_2026_company_wape_pct', 0):.2f}%"
        )

        b2.metric(
            "MAPE",
            f"{backtest.get('rolling_2026_company_mape_pct', 0):.2f}%"
        )

        b3.metric(
            "驗證期間",
            backtest.get("validation_period", "無資料")
        )

        st.info(
            backtest.get(
                "limitations",
                "回測結果僅供參考"
            )
        )

        # ---------------------------------
        # 7. AI 財務分析摘要
        # ---------------------------------

        st.markdown("---")
        st.subheader("🧠 AI 財務分析摘要")

        if "AI 財務摘要" in json_data:
            st.json(json_data["AI 財務摘要"])

        # ---------------------------------
        # 8. 原始完整財務分析 JSON
        # ---------------------------------

        with st.expander("查看完整財務分析 JSON"):
            st.json(data)



# =====================================
# 12. 資料檢查
# =====================================

elif page == "資料檢查":

    st.header("🔍 模組二、模組三資料檢查")

    st.write(f"資料來源：{DATA_SOURCE_LABEL}")

    # -------------------------------
    # 一、整體檔案讀取狀態
    # -------------------------------

    st.subheader("📊 整體資料讀取狀態")

    csv_count = len(csv_data)
    json_count = len(json_data)

    col1, col2 = st.columns(2)

    with col1:
        st.metric("CSV 成功讀取數", f"{csv_count} / 7")

    with col2:
        st.metric("JSON 成功讀取數", f"{json_count} / 2")

    if csv_count == 7 and json_count == 2:
        st.success("✅ 模組二、模組三資料皆已成功讀取")
    else:
        st.warning("⚠️ 部分資料尚未成功讀取，請檢查資料來源及檔案")

    # -------------------------------
    # 二、CSV 檔案檢查
    # -------------------------------

    st.subheader("📄 CSV 檔案檢查")

    if csv_data:

        csv_check_results = []

        for name, df in csv_data.items():

            missing_count = int(df.isnull().sum().sum())

            csv_check_results.append({
                "檔案名稱": name,
                "資料筆數": len(df),
                "欄位數量": len(df.columns),
                "缺失值數量": missing_count,
                "檢查結果": "正常" if missing_count == 0 else "有缺失值"
            })

        csv_check_df = pd.DataFrame(csv_check_results)

        st.dataframe(
            csv_check_df,
            use_container_width=True,
            hide_index=True
        )

        for name, df in csv_data.items():

            with st.expander(f"📂 {name}"):

                st.write("**欄位名稱**")
                st.write(df.columns.tolist())

                st.write("**缺失值統計**")
                missing = df.isnull().sum()
                missing = missing[missing > 0]

                if missing.empty:
                    st.success("✅ 沒有缺失值")
                else:
                    st.warning("⚠️ 以下欄位有缺失值")
                    st.dataframe(missing)

                st.write("**完整資料預覽**")
                st.dataframe(df, use_container_width=True)

    else:
        st.error("❌ 沒有成功讀取任何 CSV 檔案")

    # -------------------------------
    # 三、JSON 檔案檢查
    # -------------------------------

    st.subheader("📋 JSON 檔案檢查")

    if json_data:

        for name, data in json_data.items():

            with st.expander(f"📂 {name}"):

                if isinstance(data, dict):

                    st.success("✅ JSON 結構正常")

                    st.write("**主要資料欄位**")
                    st.write(list(data.keys()))

                    st.write("**完整 JSON 內容**")
                    st.json(data)

                else:
                    st.warning("⚠️ JSON 最外層不是字典格式")
                    st.json(data)

    else:
        st.error("❌ 沒有成功讀取任何 JSON 檔案")

    # -------------------------------
    # 四、資料檢查結論
    # -------------------------------

    st.subheader("📝 資料檢查結論")

    if csv_count == 7 and json_count == 2:

        total_missing = sum(
            int(df.isnull().sum().sum())
            for df in csv_data.values()
        )

        if total_missing == 0:
            st.success(
                "✅ 所有預期的 CSV 與 JSON 檔案均已讀取，"
                "且 CSV 沒有缺失值。"
            )
        else:
            st.warning(
                f"⚠️ 所有預期檔案均已讀取，"
                f"但 CSV 共發現 {total_missing} 個缺失值，請進一步確認。"
            )

    else:
        st.error("❌ 檔案數量未達預期，請確認資料來源。")

# =====================================
# 13. 頁尾
# =====================================

st.markdown("---")

st.caption("智慧預算管理系統｜模組四")
