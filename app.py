import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import load_database, get_summary_stats

st.set_page_config(
    page_title="RLV Maintenance Knowledge Base",
    page_icon="\U0001f680",
    layout="wide"
)

# ── Load data ──
vehicles_df, records_df, merged_df, taxonomy, metadata = load_database()
stats = get_summary_stats(merged_df)

# ── Header ──
st.title("\U0001f680 Reusable Launch Vehicle Maintenance Knowledge Base")
st.markdown(
    "**Systematic collection, classification and framework for "
    "maintenance practices on Reusable Launch Vehicles.** "
    "Built in the context of DLR Institute of Maintenance and "
    "Modification research."
)
st.divider()

# ── KPIs ──
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Maintenance Records", stats["total_records"])
with c2:
    st.metric("Vehicles Covered", stats["vehicles_covered"])
with c3:
    st.metric("Subsystems", stats["subsystems_covered"])
with c4:
    st.metric("Total Est. Hours", f"{stats['total_maintenance_hours']:,.0f}")
with c5:
    st.metric("Flight-Critical", f"{stats['flight_critical_pct']}%")

st.divider()

# ── SIDEBAR FILTERS ──
st.sidebar.header("\U0001f50d Filters")

sel_vehicles = st.sidebar.multiselect(
    "Vehicle",
    options=sorted(merged_df["vehicle_name"].unique()),
    default=sorted(merged_df["vehicle_name"].unique())
)

sel_subsystems = st.sidebar.multiselect(
    "Subsystem",
    options=sorted(merged_df["subsystem"].unique()),
    default=sorted(merged_df["subsystem"].unique())
)

sel_criticality = st.sidebar.multiselect(
    "Criticality",
    options=sorted(merged_df["criticality"].unique()),
    default=sorted(merged_df["criticality"].unique())
)

sel_type = st.sidebar.multiselect(
    "Maintenance Type",
    options=sorted(merged_df["maintenance_type"].unique()),
    default=sorted(merged_df["maintenance_type"].unique())
)

# Apply filters
filtered = merged_df[
    (merged_df["vehicle_name"].isin(sel_vehicles)) &
    (merged_df["subsystem"].isin(sel_subsystems)) &
    (merged_df["criticality"].isin(sel_criticality)) &
    (merged_df["maintenance_type"].isin(sel_type))
]

st.sidebar.markdown(f"**Showing {len(filtered)} / {len(merged_df)} records**")

# ── TAB LAYOUT ──
tab1, tab2, tab3, tab4 = st.tabs([
    "\U0001f4ca Overview",
    "\U0001f4cb Records",
    "\U0001f3ed Vehicle Comparison",
    "\U0001f4d6 Classification Taxonomy"
])

# ── TAB 1: Overview ──
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Records by Subsystem")
        fig1 = px.bar(
            filtered.groupby("subsystem").size().reset_index(name="count")
                .sort_values("count", ascending=True),
            x="count", y="subsystem", orientation="h",
            color="count", color_continuous_scale="Reds"
        )
        fig1.update_layout(height=400, showlegend=False,
                           yaxis_title="", xaxis_title="Number of records")
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.subheader("Records by Maintenance Type")
        fig2 = px.pie(
            filtered.groupby("maintenance_type").size()
                .reset_index(name="count"),
            values="count", names="maintenance_type",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Estimated Hours by Vehicle")
        hours_data = filtered.groupby("vehicle_name")[
            "estimated_duration_hours"].sum().reset_index()
        hours_data.columns = ["Vehicle", "Hours"]
        fig3 = px.bar(
            hours_data.sort_values("Hours", ascending=True),
            x="Hours", y="Vehicle", orientation="h",
            color="Hours", color_continuous_scale="Blues"
        )
        fig3.update_layout(height=400, showlegend=False,
                           yaxis_title="", xaxis_title="Total est. hours")
        st.plotly_chart(fig3, use_container_width=True)
    
    with col4:
        st.subheader("Criticality Distribution")
        fig4 = px.sunburst(
            filtered,
            path=["criticality", "subsystem", "maintenance_type"],
            color="criticality",
            color_discrete_map={
                "Flight-Critical": "#E74C3C",
                "Mission-Critical": "#F39C12",
                "Routine": "#27AE60"
            }
        )
        fig4.update_layout(height=400)
        st.plotly_chart(fig4, use_container_width=True)
    
    # Turnaround phase flow
    st.subheader("Maintenance Activities by Turnaround Phase")
    phase_order = [
        "Recovery", "Post-Flight-Inspection", "Refurbishment",
        "Re-Integration", "Pre-Flight-Testing", "Launch-Preparation"
    ]
    phase_data = filtered.groupby("turnaround_phase").agg(
        count=("id", "size"),
        hours=("estimated_duration_hours", "sum")
    ).reindex(phase_order).reset_index()
    
    fig5 = go.Figure()
    fig5.add_trace(go.Bar(
        x=phase_data["turnaround_phase"],
        y=phase_data["count"],
        name="Number of activities",
        marker_color="#3498DB"
    ))
    fig5.add_trace(go.Bar(
        x=phase_data["turnaround_phase"],
        y=phase_data["hours"],
        name="Estimated hours",
        marker_color="#E74C3C",
        yaxis="y2"
    ))
    fig5.update_layout(
        yaxis=dict(title="Number of activities"),
        yaxis2=dict(title="Estimated hours", overlaying="y",
                    side="right"),
        barmode="group",
        height=350,
        template="plotly_white"
    )
    st.plotly_chart(fig5, use_container_width=True)

# ── TAB 2: Records Table ──
with tab2:
    st.subheader("Maintenance Records Database")
    
    display_cols = [
        "vehicle_name", "operator", "subsystem", "component",
        "maintenance_type", "inspection_method", "turnaround_phase",
        "criticality", "description", "frequency",
        "estimated_duration_hours", "source"
    ]
    
    st.dataframe(
        filtered[display_cols].rename(columns={
            "vehicle_name": "Vehicle",
            "operator": "Operator",
            "subsystem": "Subsystem",
            "component": "Component",
            "maintenance_type": "Type",
            "inspection_method": "Method",
            "turnaround_phase": "Phase",
            "criticality": "Criticality",
            "description": "Description",
            "frequency": "Frequency",
            "estimated_duration_hours": "Est. Hours",
            "source": "Source"
        }),
        use_container_width=True,
        height=500
    )
    
    # Export
    csv = filtered[display_cols].to_csv(index=False)
    st.download_button(
        "\U0001f4e5 Export filtered data as CSV",
        csv, "rlv_maintenance_data.csv", "text/csv"
    )

# ── TAB 3: Vehicle Comparison ──
with tab3:
    st.subheader("Vehicle Comparison Matrix")
    
    comparison = filtered.groupby("vehicle_name").agg(
        total_records=("id", "size"),
        total_hours=("estimated_duration_hours", "sum"),
        flight_critical=("criticality",
                         lambda x: (x == "Flight-Critical").sum()),
        subsystems_covered=("subsystem", "nunique"),
        unique_methods=("inspection_method", "nunique")
    ).reset_index()
    
    # Add vehicle metadata
    comparison = comparison.merge(
        vehicles_df[["name", "class", "max_reuses_demonstrated",
                      "target_turnaround_days"]],
        left_on="vehicle_name", right_on="name"
    )
    
    st.dataframe(
        comparison[[
            "vehicle_name", "class", "max_reuses_demonstrated",
            "target_turnaround_days", "total_records",
            "total_hours", "flight_critical",
            "subsystems_covered", "unique_methods"
        ]].rename(columns={
            "vehicle_name": "Vehicle",
            "class": "Class",
            "max_reuses_demonstrated": "Max Reuses",
            "target_turnaround_days": "Target Turnaround (days)",
            "total_records": "Maint. Records",
            "total_hours": "Total Est. Hours",
            "flight_critical": "Flight-Critical Items",
            "subsystems_covered": "Subsystems",
            "unique_methods": "Inspection Methods"
        }),
        use_container_width=True
    )
    
    # Radar chart
    st.subheader("Vehicle Maintenance Profile (Radar)")
    
    radar_vehicles = st.multiselect(
        "Select vehicles to compare",
        options=sorted(comparison["vehicle_name"].unique()),
        default=sorted(comparison["vehicle_name"].unique())[:3]
    )
    
    if radar_vehicles:
        categories = ["Records", "Hours", "Flight-Critical",
                      "Subsystems", "Methods"]
        fig_radar = go.Figure()
        
        for v in radar_vehicles:
            row = comparison[comparison["vehicle_name"] == v].iloc[0]
            values = [
                row["total_records"] / comparison["total_records"].max(),
                row["total_hours"] / comparison["total_hours"].max(),
                row["flight_critical"] / max(comparison["flight_critical"].max(), 1),
                row["subsystems_covered"] / comparison["subsystems_covered"].max(),
                row["unique_methods"] / comparison["unique_methods"].max(),
            ]
            fig_radar.add_trace(go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                name=v,
                fill="toself",
                opacity=0.5
            ))
        
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            height=450,
            template="plotly_white"
        )
        st.plotly_chart(fig_radar, use_container_width=True)

# ── TAB 4: Classification Taxonomy ──
with tab4:
    st.subheader("Classification Taxonomy")
    st.markdown(
        "The following taxonomy was developed to systematically "
        "classify RLV maintenance practices across vehicles and "
        "subsystems."
    )
    
    for category, values in taxonomy.items():
        with st.expander(
            f"**{category.replace('_', ' ').title()}** "
            f"({len(values)} classes)"
        ):
            for v in values:
                st.markdown(f"- `{v}`")
    
    st.divider()
    st.subheader("Data Sources")
    for src in metadata["sources"]:
        st.markdown(f"- {src}")
    
    st.divider()
    st.subheader("Methodology")
    st.markdown("""
    **Data collection approach:**
    1. Identified all currently operational or in-development RLVs 
       with publicly available maintenance information
    2. For each vehicle, systematically catalogued maintenance 
       activities by subsystem, working through propulsion, 
       structures, TPS, avionics, landing, recovery, and ground 
       systems
    3. Each record was classified using the taxonomy above
    4. Estimated durations were assigned based on public statements, 
       analogous systems (e.g. Space Shuttle heritage), and 
       engineering judgment
    
    **Limitations:**
    - Data is limited to publicly available sources — proprietary 
      OEM maintenance manuals are not accessible
    - Estimated durations are approximate and based on public 
      statements, not measured data
    - The database currently covers 5 vehicles and 20 records; 
      a production version would require significantly more entries
    - Classification categories may need refinement as more data 
      becomes available
    """)

st.divider()
st.caption(
    "RLV Maintenance Knowledge Base | "
    "Built by Oscar Vincent Dbritto | "
)