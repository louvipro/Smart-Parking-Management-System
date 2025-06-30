import asyncio
import time
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

import pandas as pd
import streamlit as st

from src.infrastructure.persistence.database import AsyncSessionLocal
from src.infrastructure.api.schemas.parking import SpotType, VehicleEntry, VehicleExit
from src.infrastructure.persistence.sqlalchemy_repositories.sqlalchemy_repositories import (
    SQLAlchemyVehicleRepository,
    SQLAlchemyParkingSpotRepository,
    SQLAlchemyParkingSessionRepository,
)
from src.application.services.analytics_service import AnalyticsService
from src.application.services.parking_service import ParkingService


st.set_page_config(
    page_title="Parking Dashboard",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Parking Management Dashboard")




async def get_parking_status():
    async with AsyncSessionLocal() as db:
        vehicle_repo = SQLAlchemyVehicleRepository(db)
        spot_repo = SQLAlchemyParkingSpotRepository(db)
        session_repo = SQLAlchemyParkingSessionRepository(db)
        service = ParkingService(vehicle_repo, spot_repo, session_repo)
        return await service.get_parking_status()


async def get_active_sessions():
    async with AsyncSessionLocal() as db:
        vehicle_repo = SQLAlchemyVehicleRepository(db)
        spot_repo = SQLAlchemyParkingSpotRepository(db)
        session_repo = SQLAlchemyParkingSessionRepository(db)
        service = ParkingService(vehicle_repo, spot_repo, session_repo)
        return await service.get_active_sessions()


async def get_all_sessions():
    async with AsyncSessionLocal() as db:
        vehicle_repo = SQLAlchemyVehicleRepository(db)
        spot_repo = SQLAlchemyParkingSpotRepository(db)
        session_repo = SQLAlchemyParkingSessionRepository(db)
        service = ParkingService(vehicle_repo, spot_repo, session_repo)
        return await service.get_all_sessions_for_dashboard()


async def get_analytics():
    async with AsyncSessionLocal() as db:
        vehicle_repo = SQLAlchemyVehicleRepository(db)
        session_repo = SQLAlchemyParkingSessionRepository(db)
        spot_repo = SQLAlchemyParkingSpotRepository(db)
        analytics = AnalyticsService(vehicle_repo, session_repo, spot_repo)
        return await analytics.get_parking_analytics()


async def get_analytics_service():
    async with AsyncSessionLocal() as db:
        vehicle_repo = SQLAlchemyVehicleRepository(db)
        session_repo = SQLAlchemyParkingSessionRepository(db)
        spot_repo = SQLAlchemyParkingSpotRepository(db)
        return AnalyticsService(vehicle_repo, session_repo, spot_repo)


async def register_entry(vehicle_data):
    async with AsyncSessionLocal() as db:
        vehicle_repo = SQLAlchemyVehicleRepository(db)
        spot_repo = SQLAlchemyParkingSpotRepository(db)
        session_repo = SQLAlchemyParkingSessionRepository(db)
        service = ParkingService(vehicle_repo, spot_repo, session_repo)
        return await service.register_vehicle_entry(
            license_plate=vehicle_data.license_plate,
            color=vehicle_data.color,
            brand=vehicle_data.brand,
            spot_type=vehicle_data.spot_type
        )


async def register_exit(exit_data):
    async with AsyncSessionLocal() as db:
        vehicle_repo = SQLAlchemyVehicleRepository(db)
        spot_repo = SQLAlchemyParkingSpotRepository(db)
        session_repo = SQLAlchemyParkingSessionRepository(db)
        service = ParkingService(vehicle_repo, spot_repo, session_repo)
        return await service.register_vehicle_exit(exit_data.license_plate)


# Get current status
status = asyncio.run(get_parking_status())
analytics = asyncio.run(get_analytics())
active_sessions = asyncio.run(get_active_sessions())
all_sessions = asyncio.run(get_all_sessions())
analytics_service_instance = asyncio.run(get_analytics_service())

# Calculate potential revenue
current_time = datetime.now(timezone.utc)
potential_revenue = sum([
    max(1.0, (current_time - s['entry_time']).total_seconds() / 3600) * s['hourly_rate']
    for s in active_sessions
]) if active_sessions else 0

# Main dashboard metrics
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Total Spots",
        status['total_spots'],
        delta=None
    )

with col2:
    st.metric(
        "Occupied",
        status['occupied_spots'],
        delta=f"{status['occupancy_rate']}%"
    )

with col3:
    st.metric(
        "Available",
        status['available_spots'],
        delta=None
    )

with col4:
    st.metric(
        "Today's Revenue",
        f"${analytics['today_revenue']:.2f}",
        delta=f"{analytics['today_vehicles']} vehicles"
    )

with col5:
    st.metric(
        "Potential Revenue",
        f"${potential_revenue:.2f}",
        delta=f"{len(active_sessions)} active",
        help="Revenue if all current vehicles exit now"
    )

# Tabs for different functions
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Vehicle Entry/Exit", "Current Status", "Parking History", "Floor Overview", "Analytics"])

with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🚦 Vehicle Entry")
        with st.form("entry_form"):
            license_plate = st.text_input(
                "License Plate", placeholder="ABC-123")
            color = st.text_input("Vehicle Color", placeholder="Blue")
            brand = st.text_input("Vehicle Brand", placeholder="Toyota")
            spot_type = st.selectbox("Spot Type", options=[
                                     e.value for e in SpotType])

            if st.form_submit_button("Register Entry", type="primary"):
                if license_plate and color and brand:
                    try:
                        vehicle_data = VehicleEntry(
                            license_plate=license_plate,
                            color=color,
                            brand=brand,
                            spot_type=spot_type
                        )
                        session = asyncio.run(register_entry(vehicle_data))
                        st.success(
                            f"✅ Vehicle {license_plate} assigned to spot {session['parking_spot']['spot_number']}")
                        st.balloons()
                        # Force refresh to update metrics
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    st.error("Please fill all fields")

    with col2:
        st.subheader("🚪 Vehicle Exit")
        with st.form("exit_form"):
            exit_license = st.text_input(
                "License Plate", placeholder="ABC-123", key="exit_plate")

            if st.form_submit_button("Register Exit", type="primary"):
                if exit_license:
                    try:
                        exit_data = VehicleExit(license_plate=exit_license)
                        payment = asyncio.run(register_exit(exit_data))
                        st.success(f"✅ Vehicle {payment['license_plate']} exited")
                        st.info(
                            f"Duration: {payment['duration_hours']:.2f} hours")
                        st.info(f"💰 Amount Due: ${payment['amount_due']:.2f}")
                        # Wait a moment to show the info, then refresh
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                else:
                    st.error("Please enter license plate")

with tab2:
    st.subheader("🚗 Currently Parked Vehicles")

    sessions = active_sessions # Use the already fetched active sessions

    if sessions:
        # Calculate potential revenue for each session
        current_time = datetime.now(timezone.utc)
        df_sessions = pd.DataFrame([
            {
                "License Plate": s['vehicle']['license_plate'],
                "Color": s['vehicle']['color'],
                "Brand": s['vehicle']['brand'],
                "Spot": s['parking_spot']['spot_number'],
                "Floor": s['parking_spot']['floor'],
                "Entry Time": s['entry_time'].strftime("%Y-%m-%d %H:%M"),
                "Duration (hours)": round((current_time - s['entry_time']).total_seconds() / 3600, 2),
                "Potential Revenue": f"${max(1.0, (current_time - s['entry_time']).total_seconds() / 3600) * s['hourly_rate']:.2f}"
            }
            for s in sessions
        ])

        st.dataframe(df_sessions, use_container_width=True)
    else:
        st.info("No vehicles currently parked")

with tab3:
    st.subheader("📜 Parking History")

    if all_sessions:
        current_time = datetime.now(timezone.utc)
        df_history = pd.DataFrame([
            {
                "Status": "Exited" if s['exit_time'] else "Parked",
                "License Plate": s['vehicle']['license_plate'],
                "Color": s['vehicle']['color'],
                "Brand": s['vehicle']['brand'],
                "Spot": s['parking_spot']['spot_number'],
                "Entry Time": s['entry_time'].strftime("%Y-%m-%d %H:%M"),
                "Exit Time": s['exit_time'].strftime("%Y-%m-%d %H:%M") if s['exit_time'] else "N/A",
                "Duration (hours)": round((s['exit_time'] - s['entry_time']).total_seconds() / 3600, 2) if s['exit_time'] else round((current_time - s['entry_time']).total_seconds() / 3600, 2),
                "Final Revenue": f"${s['amount_paid']:.2f}" if s['amount_paid'] is not None else "N/A",
                "Potential Revenue": f"${max(1.0, (current_time - s['entry_time']).total_seconds() / 3600) * s['hourly_rate']:.2f}" if not s['exit_time'] else "N/A"
            }
            for s in all_sessions
        ])

        st.dataframe(df_history, use_container_width=True)
    else:
        st.info("No parking sessions recorded yet.")


with tab4:
    st.subheader("🏢 Floor Overview")

    # Create floor visualization
    floors_data = []
    for floor in status['floors']:
        floors_data.extend([
            {"Floor": f"Floor {floor['floor']}",
                "Status": "Occupied", "Count": floor['occupied']},
            {"Floor": f"Floor {floor['floor']}",
                "Status": "Available", "Count": floor['available']}
        ])

    df_floors = pd.DataFrame(floors_data)

    # Use Streamlit's native bar chart
    st.bar_chart(
        df_floors.pivot(index="Floor", columns="Status", values="Count"),
        color=["#FF6B6B", "#4ECDC4"]
    )

with tab5:
    st.subheader("📊 Parking Analytics")

    # Overview Section
    st.subheader("Overview")
    col1_overview, col2_overview = st.columns(2)

    with col1_overview:
        st.metric("Occupancy Rate", f"{status['occupancy_rate']}%",
                  delta=f"{status['occupied_spots']} vehicles")
        st.progress(status['occupancy_rate'] / 100)
        occupancy_data = pd.DataFrame({
            'Status': ['Occupied', 'Available'],
            'Count': [status['occupied_spots'], status['available_spots']]
        })
        st.bar_chart(occupancy_data.set_index('Status'))

    with col2_overview:
        st.metric("Average Duration Today",
                  f"{analytics['average_duration_hours']:.2f} hours")
        st.metric("Vehicles Today", analytics['today_vehicles'])
        st.metric("Current Occupancy", analytics['current_occupancy'])
        st.write("**Floor Breakdown:**")
        for floor in status['floors']:
            st.write(
                f"Floor {floor['floor']}: {floor['occupied']}/{floor['total']} occupied")

    st.markdown("---") # Separator

    # Monthly Report Section
    st.subheader("Monthly Report")

    # Monthly Filter and Navigation
    monthly_revenue_data = asyncio.run(analytics_service_instance.get_revenue_by_month())
    monthly_usage_data = asyncio.run(analytics_service_instance.get_monthly_parking_usage())

    # Extract all unique months and sort them
    all_months_str = sorted(list(set([m['month'] for m in monthly_revenue_data] + [m['month'] for m in monthly_usage_data])), reverse=True)
    
    # Convert month strings to datetime objects for easier manipulation
    all_months_dt = sorted([datetime.strptime(m, '%Y-%m') for m in all_months_str], reverse=True)

    # Get current month for default selection
    current_month_str = datetime.now().strftime('%Y-%m')
    if current_month_str not in all_months_str:
        all_months_str.insert(0, current_month_str) # Add current month if not present
        all_months_dt.insert(0, datetime.strptime(current_month_str, '%Y-%m'))
        all_months_dt.sort(reverse=True) # Re-sort after adding

    # Initialize session state for selected month if not already set
    if 'selected_month_analytics' not in st.session_state:
        st.session_state.selected_month_analytics = current_month_str if current_month_str in all_months_str else (all_months_str[0] if all_months_str else "All Months")

    # Navigation buttons and selectbox
    col_nav_left, col_nav_right = st.columns([3, 1])
    with col_nav_left:
        col_prev_btn, col_month_select = st.columns([1, 2])
        with col_prev_btn:
            if st.button("Previous Month", key="prev_month_btn_report"):
                current_month_dt = datetime.strptime(st.session_state.selected_month_analytics, '%Y-%m')
                prev_month_dt = current_month_dt - relativedelta(months=1)
                st.session_state.selected_month_analytics = prev_month_dt.strftime('%Y-%m')
                st.rerun()
        with col_month_select:
            selected_month_from_box = st.selectbox("Select Month", all_months_str, index=all_months_str.index(st.session_state.selected_month_analytics) if st.session_state.selected_month_analytics in all_months_str else 0, key="month_selector_report")
            if selected_month_from_box != st.session_state.selected_month_analytics:
                st.session_state.selected_month_analytics = selected_month_from_box
                st.rerun()
    with col_nav_right:
        if st.button("Next Month", key="next_month_btn_report"):
            current_month_dt = datetime.strptime(st.session_state.selected_month_analytics, '%Y-%m')
            next_month_dt = current_month_dt + relativedelta(months=1)
            st.session_state.selected_month_analytics = next_month_dt.strftime('%Y-%m')
            st.rerun()

    selected_month_str = st.session_state.selected_month_analytics

    # Calculate months to display (previous, current, next)
    selected_month_dt = datetime.strptime(selected_month_str, '%Y-%m')
    months_to_display_dt = sorted([
        selected_month_dt - relativedelta(months=1),
        selected_month_dt,
        selected_month_dt + relativedelta(months=1)
    ])
    months_to_display_str = [m.strftime('%Y-%m') for m in months_to_display_dt]

    # Monthly Revenue and Usage Sections side-by-side
    col_monthly_data1, col_monthly_data2 = st.columns(2)

    with col_monthly_data1:
        st.subheader("Monthly Revenue")
        if monthly_revenue_data:
            df_monthly_revenue = pd.DataFrame(monthly_revenue_data)
            
            # Create a full DataFrame for the three months with zero values
            df_display_revenue = pd.DataFrame({'month': months_to_display_str, 'total_revenue': 0.0})
            df_display_revenue = pd.merge(df_display_revenue, df_monthly_revenue, on='month', how='left', suffixes=('_fill', ''))
            df_display_revenue['total_revenue'] = df_display_revenue['total_revenue'].fillna(0)
            df_display_revenue = df_display_revenue[['month', 'total_revenue']]
            df_display_revenue = df_display_revenue.set_index('month')

            col_rev_chart, col_rev_metric = st.columns([3, 1])
            with col_rev_chart:
                st.bar_chart(df_display_revenue, use_container_width=False, width=400)
            with col_rev_metric:
                # Display total revenue for the selected month
                selected_month_revenue = df_monthly_revenue[df_monthly_revenue['month'] == selected_month_str]['total_revenue'].sum()
                st.metric(f"Revenue for {selected_month_str}", f"${selected_month_revenue:.2f}")
        else:
            st.info("No monthly revenue data available.")

    with col_monthly_data2:
        st.subheader("Monthly Parking Usage")
        if monthly_usage_data:
            df_monthly_usage = pd.DataFrame(monthly_usage_data)

            # Create a full DataFrame for the three months with zero values
            df_display_usage = pd.DataFrame({'month': months_to_display_str, 'session_count': 0})
            df_display_usage = pd.merge(df_display_usage, df_monthly_usage, on='month', how='left', suffixes=('_fill', ''))
            df_display_usage['session_count'] = df_display_usage['session_count'].fillna(0).astype(int)
            df_display_usage = df_display_usage[['month', 'session_count']]
            df_display_usage = df_display_usage.set_index('month')

            col_usage_chart, col_usage_metric = st.columns([3, 1])
            with col_usage_chart:
                st.bar_chart(df_display_usage, use_container_width=False, width=400)
            with col_usage_metric:
                # Display total usage for the selected month
                selected_month_usage = df_monthly_usage[df_monthly_usage['month'] == selected_month_str]['session_count'].sum()
                st.metric(f"Usage for {selected_month_str}", f"{selected_month_usage} sessions")
        else:
            st.info("No monthly parking usage data available.")




