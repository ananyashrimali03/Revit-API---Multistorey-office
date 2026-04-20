import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

BASE_PATH = r"C:\Users\anany\OneDrive\Desktop\CMU\S26\Job Apps\KUNZ\kunz_demo\office\\"

st.set_page_config(
    page_title="Office Building Analytics",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 7-Story Office Building — BIM Analytics Dashboard")
st.caption(
    "Pipeline: Revit Model → Dynamo + Revit API → "
    "Python Processing → Streamlit Dashboard"
)

# Load all data
@st.cache_data
def load_data():
    rooms = pd.read_csv(BASE_PATH + "rooms.csv")
    walls = pd.read_csv(BASE_PATH + "walls.csv")
    floors = pd.read_csv(BASE_PATH + "floors.csv")
    doors = pd.read_csv(BASE_PATH + "doors.csv")
    windows = pd.read_csv(BASE_PATH + "windows.csv")
    return rooms, walls, floors, doors, windows

rooms, walls, floors, doors, windows = load_data()


@st.cache_data
def _cached_wall_materials(base_path: str):
    from process_materials import load_wall_materials_dataframe

    return load_wall_materials_dataframe(base_path)


# Categorize rooms
def categorize_room(name):
    name_lower = str(name).lower()
    if any(x in name_lower for x in [
        'office', 'work', 'open plan', 'desk'
    ]):
        return 'Office Space'
    elif any(x in name_lower for x in [
        'meeting', 'conference', 'board',
        'seminar', 'training'
    ]):
        return 'Meeting'
    elif any(x in name_lower for x in [
        'reception', 'lobby', 'entrance',
        'foyer', 'waiting'
    ]):
        return 'Reception'
    elif any(x in name_lower for x in [
        'toilet', 'wc', 'bathroom',
        'shower', 'washroom'
    ]):
        return 'Sanitary'
    elif any(x in name_lower for x in [
        'kitchen', 'pantry', 'cafe',
        'break', 'canteen'
    ]):
        return 'Breakout'
    elif any(x in name_lower for x in [
        'store', 'storage', 'utility',
        'plant', 'server', 'it'
    ]):
        return 'Support'
    elif any(x in name_lower for x in [
        'corridor', 'hall', 'stair',
        'lift', 'elevator', 'circulation'
    ]):
        return 'Circulation'
    else:
        return 'Other'

rooms['Category'] = rooms['Name'].apply(categorize_room)

def render_spatial_tab(rooms, walls, floors, doors, windows):
    st.divider()

    # ── SECTION 1: BUILDING OVERVIEW ─────────────────────────

    st.header("📊 Building Overview")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("Floors", 7)
    with col2:
        st.metric("Rooms", len(rooms))
    with col3:
        st.metric("Walls", len(walls))
    with col4:
        st.metric("Doors", len(doors))
    with col5:
        st.metric("Windows", len(windows))
    with col6:
        st.metric(
            "Total Floor Area",
            f"{floors['Area_m2'].sum():.0f} m²"
        )

    st.divider()

    st.subheader("Overview charts")
    overview_pick = st.selectbox(
        "Chart",
        ("Floor Area by Level", "Elements per Level"),
        key="chart_overview",
    )

    if overview_pick == "Floor Area by Level":
        floor_by_level = floors.groupby(
            'Level'
        )['Area_m2'].sum().reset_index()
        floor_by_level = floor_by_level.sort_values('Level')
        levels_list = floor_by_level['Level'].tolist()

        focus_level = st.selectbox(
            "Focus floor",
            levels_list,
            index=0,
            key="floor_area_focus",
            help=(
                "Highlights one level; faded bars are other floors. "
                "Dashed line = average of the other floors; dotted = mean "
                "across all levels."
            ),
        )

        sel_area = float(
            floor_by_level.loc[
                floor_by_level['Level'] == focus_level, 'Area_m2'
            ].iloc[0]
        )
        other_mask = floor_by_level['Level'] != focus_level
        if other_mask.any():
            avg_other = float(
                floor_by_level.loc[other_mask, 'Area_m2'].mean()
            )
        else:
            avg_other = sel_area
        avg_all = float(floor_by_level['Area_m2'].mean())
        delta_vs_other = sel_area - avg_other
        denom = avg_other if abs(avg_other) > 1e-6 else 1.0
        delta_pct = (delta_vs_other / denom) * 100.0

        c_m1, c_m2, c_m3, c_m4 = st.columns(4)
        with c_m1:
            st.metric("Selected floor", f"{sel_area:.0f} m²")
        with c_m2:
            st.metric("Avg of other floors", f"{avg_other:.0f} m²")
        with c_m3:
            st.metric(
                "Δ vs other avg",
                f"{delta_vs_other:+.0f} m²",
                f"{delta_pct:+.1f}%",
            )
        with c_m4:
            st.metric("Mean all levels", f"{avg_all:.0f} m²")

        bar_colors = [
            '#1d4ed8' if lev == focus_level else 'rgba(148, 163, 184, 0.42)'
            for lev in floor_by_level['Level']
        ]
        fig = go.Figure(
            data=[
                go.Bar(
                    x=floor_by_level['Level'],
                    y=floor_by_level['Area_m2'],
                    marker=dict(
                        color=bar_colors,
                        line=dict(width=1, color='rgba(30, 41, 59, 0.35)'),
                    ),
                    text=[f"{v:.0f}" for v in floor_by_level['Area_m2']],
                    textposition='outside',
                    hovertemplate=(
                        "<b>%{x}</b><br>Area: %{y:.1f} m²"
                        "<extra></extra>"
                    ),
                )
            ]
        )
        ymax = max(
            float(floor_by_level['Area_m2'].max()) * 1.18,
            avg_all * 1.12,
            avg_other * 1.12,
            sel_area * 1.12,
        )
        fig.add_hline(
            y=avg_other,
            line_dash='dash',
            line_width=2,
            line_color='#64748b',
            annotation_text=f"Avg other floors: {avg_other:.0f} m²",
            annotation_position="top left",
        )
        fig.add_hline(
            y=avg_all,
            line_dash='dot',
            line_width=2,
            line_color='#0f766e',
            annotation_text=f"Mean all levels: {avg_all:.0f} m²",
            annotation_position="bottom left",
        )
        fig.update_layout(
            title="Floor area by level — focus vs others (overlay)",
            xaxis_title="Level",
            yaxis_title="Floor plate area (m²)",
            showlegend=False,
            bargap=0.22,
            yaxis=dict(range=[0, ymax]),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        wall_counts = walls.groupby('Level').size()
        door_counts = doors.groupby('Level').size()
        window_counts = windows.groupby('Level').size()

        element_data = []
        for level in walls['Level'].unique():
            element_data.append({
                'Level': level,
                'Walls': wall_counts.get(level, 0),
                'Doors': door_counts.get(level, 0),
                'Windows': window_counts.get(level, 0)
            })

        element_df = pd.DataFrame(element_data).sort_values('Level')
        fig = px.bar(
            element_df.melt(
                id_vars='Level',
                var_name='Element',
                value_name='Count'
            ),
            x='Level',
            y='Count',
            color='Element',
            barmode='group',
            color_discrete_sequence=[
                'steelblue', 'tomato', 'gold'
            ],
            title="Elements per Level",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── SECTION 2: SPACE ANALYTICS ───────────────────────────

    st.header("📐 Space Analytics")

    st.subheader("Space charts")
    space_pick = st.selectbox(
        "Chart",
        (
            "Room Area by Category",
            "Room Distribution by Category",
            "Rooms by Level",
            "Room Size Distribution",
        ),
        key="chart_space",
    )

    if space_pick == "Room Area by Category":
        cat_area = rooms.groupby(
            'Category'
        )['Area_m2'].sum().reset_index()
        cat_area = cat_area.sort_values('Area_m2', ascending=False)
        fig = px.bar(
            cat_area,
            x='Category',
            y='Area_m2',
            color='Category',
            labels={'Area_m2': 'Total Area (m²)'},
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig.update_layout(showlegend=False, title="Room Area by Category")
        st.plotly_chart(fig, use_container_width=True)
    elif space_pick == "Room Distribution by Category":
        fig = px.pie(
            rooms.groupby(
                'Category'
            ).size().reset_index(name='Count'),
            values='Count',
            names='Category',
            color_discrete_sequence=px.colors.qualitative.Set2,
            title="Room Distribution by Category",
        )
        st.plotly_chart(fig, use_container_width=True)
    elif space_pick == "Rooms by Level":
        room_level = rooms.groupby(
            ['Level', 'Category']
        ).size().reset_index(name='Count')
        fig = px.bar(
            room_level,
            x='Level',
            y='Count',
            color='Category',
            barmode='stack',
            color_discrete_sequence=px.colors.qualitative.Set2,
            title="Rooms by Level",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig = px.histogram(
            rooms,
            x='Area_m2',
            nbins=15,
            color='Category',
            labels={'Area_m2': 'Area (m²)'},
            color_discrete_sequence=px.colors.qualitative.Set2,
            title="Room Size Distribution",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── SECTION 3: FACADE ANALYTICS ──────────────────────────

    st.header("🪟 Facade Analytics")
    st.caption(
        "Window to wall ratio analysis — "
        "key metric for daylighting and energy performance"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Windows", len(windows))
    with col2:
        st.metric("Total Doors", len(doors))
    with col3:
        ratio = round(len(windows) / len(walls) * 100, 1)
        st.metric(
            "Windows per Wall %",
            f"{ratio}%"
        )

    st.subheader("Facade charts")
    facade_pick = st.selectbox(
        "Chart",
        ("Windows by Level", "Window Types"),
        key="chart_facade",
    )

    if facade_pick == "Windows by Level":
        win_level = windows.groupby(
            'Level'
        ).size().reset_index(name='Count')
        win_level = win_level.sort_values('Level')
        fig = px.bar(
            win_level,
            x='Level',
            y='Count',
            color='Level',
            labels={'Count': 'Window Count'},
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        fig.update_layout(showlegend=False, title="Windows by Level")
        st.plotly_chart(fig, use_container_width=True)
    else:
        win_types = windows.groupby(
            'Type'
        ).size().reset_index(name='Count')
        win_types = win_types.sort_values('Count', ascending=False)
        fig = px.bar(
            win_types.head(10),
            x='Count',
            y='Type',
            orientation='h',
            color='Count',
            color_continuous_scale='Blues',
            title="Window Types",
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── SECTION 4: WALL ANALYTICS ────────────────────────────

    st.header("🧱 Wall Analytics")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Total Wall Length",
            f"{walls['Length_m'].sum():.0f} m"
        )

    with col2:
        st.metric(
            "Total Wall Area",
            f"{walls['Area_m2'].sum():.0f} m²"
        )

    st.subheader("Wall charts")
    wall_pick = st.selectbox(
        "Chart",
        ("Wall Length by Level", "Wall Types Distribution"),
        key="chart_walls",
    )

    if wall_pick == "Wall Length by Level":
        wall_level = walls.groupby(
            'Level'
        )['Length_m'].sum().reset_index()
        wall_level = wall_level.sort_values('Level')
        fig = px.bar(
            wall_level,
            x='Level',
            y='Length_m',
            color='Level',
            labels={'Length_m': 'Total Length (m)'},
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        fig.update_layout(showlegend=False, title="Wall Length by Level")
        st.plotly_chart(fig, use_container_width=True)
    else:
        wall_types = walls.groupby(
            'Type'
        ).size().reset_index(name='Count')
        wall_types = wall_types.sort_values(
            'Count', ascending=False
        )
        fig = px.bar(
            wall_types.head(10),
            x='Count',
            y='Type',
            orientation='h',
            color='Count',
            color_continuous_scale='Reds',
            title="Wall Types Distribution",
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── SECTION 5: QC CHECKS ─────────────────────────────────

    st.header("⚠️ Model QC Checks")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Room QC")

        # Check for missing names
        missing_names = rooms[
            rooms['Name'].isna() |
            (rooms['Name'] == 'Unknown') |
            (rooms['Name'] == '')
        ]

        # Check for very small rooms
        small_rooms = rooms[rooms['Area_m2'] < 3.0]

        # Check for unassigned categories
        other_rooms = rooms[rooms['Category'] == 'Other']

        if len(missing_names) > 0:
            st.warning(
                f"{len(missing_names)} rooms with missing names"
            )
        else:
            st.success("✓ All rooms have names")

        if len(small_rooms) > 0:
            st.warning(
                f"{len(small_rooms)} rooms under 3m² — "
                f"review required"
            )
            st.dataframe(
                small_rooms[['Number', 'Name', 'Area_m2', 'Level']],
                use_container_width=True
            )
        else:
            st.success("✓ All rooms above minimum size")

        if len(other_rooms) > 0:
            st.info(
                f"{len(other_rooms)} rooms uncategorized — "
                f"review naming"
            )

    with col2:
        st.subheader("Model Completeness")

        checks = {
            "Rooms extracted": len(rooms) > 0,
            "Walls extracted": len(walls) > 0,
            "Floors extracted": len(floors) > 0,
            "Doors extracted": len(doors) > 0,
            "Windows extracted": len(windows) > 0,
            "All rooms named": len(missing_names) == 0,
            "No tiny rooms": len(small_rooms) == 0,
        }

        for check, passed in checks.items():
            if passed:
                st.success(f"✓ {check}")
            else:
                st.error(f"✗ {check}")

    st.divider()

    # ── SECTION 6: ROOM SCHEDULE ─────────────────────────────

    st.header("📋 Complete Room Schedule")

    col1, col2, col3 = st.columns(3)

    with col1:
        search = st.text_input("Search rooms")
    with col2:
        level_filter = st.selectbox(
            "Filter by level",
            ["All"] + sorted(rooms['Level'].unique().tolist())
        )
    with col3:
        cat_filter = st.selectbox(
            "Filter by category",
            ["All"] + sorted(rooms['Category'].unique().tolist())
        )

    filtered = rooms.copy()

    if search:
        filtered = filtered[
            filtered['Name'].str.contains(
                search, case=False, na=False
            )
        ]

    if level_filter != "All":
        filtered = filtered[
            filtered['Level'] == level_filter
        ]

    if cat_filter != "All":
        filtered = filtered[
            filtered['Category'] == cat_filter
        ]

    st.dataframe(
        filtered[[
            'Number', 'Name', 'Category',
            'Level', 'Area_m2', 'Perimeter_m'
        ]],
        use_container_width=True,
        column_config={
            'Area_m2': st.column_config.NumberColumn(
                'Area (m²)', format="%.2f"
            ),
            'Perimeter_m': st.column_config.NumberColumn(
                'Perimeter (m)', format="%.2f"
            )
        }
    )

    st.divider()

    st.caption(
        f"7 Floors | {len(rooms)} Rooms | "
        f"{len(walls)} Walls | {len(doors)} Doors | "
        f"{len(windows)} Windows | "
        f"{floors['Area_m2'].sum():.0f} m² Total Area | "
        "Extracted via Revit API + Dynamo | "
        "Streamlit Dashboard"
    )

def render_materials_tab(base_path: str):
    st.header("Wall materials and embodied carbon")
    st.caption(
        "Layer volumes from Revit; density and carbon factors from "
        "process_materials (ICE-style defaults)."
    )
    try:
        from process_materials import material_carbon_summary

        dfm = _cached_wall_materials(base_path)
    except FileNotFoundError:
        st.warning(
            "No wall_materials.csv found. Export wall material takeoffs "
            "into the project folder to populate this tab."
        )
        return
    except Exception as err:
        st.error(f"Could not load materials: {err}")
        return

    total_tc = dfm["Embodied_Carbon_kgCO2e"].sum() / 1000.0
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Material layers", len(dfm))
    with c2:
        st.metric("Total volume", f"{dfm['Volume_m3'].sum():.1f} m³")
    with c3:
        st.metric("Total mass", f"{dfm['Mass_kg'].sum():,.0f} kg")
    with c4:
        st.metric("Embodied carbon", f"{total_tc:.2f} tCO2e")

    summary = material_carbon_summary(dfm)

    st.subheader("Materials charts")
    mat_pick = st.selectbox(
        "Chart",
        (
            "Embodied carbon by material",
            "Volume by material",
            "Carbon by level",
        ),
        key="chart_materials",
    )
    if mat_pick == "Embodied carbon by material":
        top = summary.head(15)
        fig = px.bar(
            top,
            x="Embodied_Carbon_kgCO2e",
            y="Material",
            orientation="h",
            labels={"Embodied_Carbon_kgCO2e": "kgCO2e"},
            color="Embodied_Carbon_kgCO2e",
            color_continuous_scale="YlOrRd",
            title="Top materials by embodied carbon",
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    elif mat_pick == "Volume by material":
        vol_sum = summary.sort_values("Volume_m3", ascending=False).head(12)
        fig = px.pie(
            vol_sum,
            values="Volume_m3",
            names="Material",
            title="Share of material volume (top 12)",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        by_level = (
            dfm.groupby("Level", as_index=False)["Embodied_Carbon_kgCO2e"]
            .sum()
            .sort_values("Level")
        )
        fig = px.bar(
            by_level,
            x="Level",
            y="Embodied_Carbon_kgCO2e",
            color="Level",
            labels={"Embodied_Carbon_kgCO2e": "kgCO2e"},
            color_discrete_sequence=px.colors.sequential.Sunsetdark,
            title="Embodied carbon by level",
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("By-material summary")
    st.dataframe(summary, use_container_width=True)

    with st.expander("Full layer schedule (enriched)"):
        st.dataframe(dfm, use_container_width=True)

    st.caption(
        "Factors are indicative; validate against project EPDs or EC3."
    )


st.divider()
tab_spatial, tab_materials = st.tabs(
    ["Spatial information", "Materials"]
)
with tab_spatial:
    render_spatial_tab(rooms, walls, floors, doors, windows)
with tab_materials:
    render_materials_tab(BASE_PATH)
