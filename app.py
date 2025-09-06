"""
Azure DevOps Sprint Dashboard - Main Streamlit Application
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
from typing import Optional

# Import custom modules
from azure_devops_client import AzureDevOpsClient
from data_analyzer import SprintAnalyzer
from visualizations import DashboardVisualizations
from config import DASHBOARD_CONFIG, AZURE_DEVOPS_CONFIG


class SprintDashboard:
    """Main dashboard application class"""
    
    def __init__(self):
        """Initialize the dashboard"""
        self.setup_page_config()
        self.viz = DashboardVisualizations()
        self.client = None
        self.analyzer = None
    
    def setup_page_config(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title=DASHBOARD_CONFIG['page_title'],
            page_icon=DASHBOARD_CONFIG['page_icon'],
            layout=DASHBOARD_CONFIG['layout'],
            initial_sidebar_state=DASHBOARD_CONFIG['initial_sidebar_state']
        )
    
    def setup_sidebar(self) -> Optional[str]:
        """
        Setup sidebar with configuration options
        
        Returns:
            Personal Access Token if provided, None otherwise
        """
        st.sidebar.title("🔧 Configuration")
        
        # Azure DevOps configuration display
        with st.sidebar.expander("📋 Azure DevOps Settings", expanded=False):
            st.write(f"**Organization:** {AZURE_DEVOPS_CONFIG['organization']}")
            st.write(f"**Project:** {AZURE_DEVOPS_CONFIG['project']}")
            st.write(f"**Team:** {AZURE_DEVOPS_CONFIG['team']}")
        
        # Personal Access Token input
        st.sidebar.subheader("🔐 Authentication")
        pat = st.sidebar.text_input(
            "Personal Access Token",
            type="password",
            help="Enter your Azure DevOps Personal Access Token"
        )
        
        if pat:
            # Test connection button
            if st.sidebar.button("🔍 Test Connection"):
                with st.spinner("Testing connection..."):
                    test_client = AzureDevOpsClient(pat)
                    if test_client.test_connection():
                        st.sidebar.success("✅ Connection successful!")
                    else:
                        st.sidebar.error("❌ Connection failed. Please check your PAT.")
        
        # Instructions
        with st.sidebar.expander("📖 Instructions", expanded=False):
            st.markdown("""
            **How to get a Personal Access Token:**
            1. Go to Azure DevOps
            2. Click on User Settings (top right)
            3. Select Personal Access Tokens
            4. Create a new token with 'Work Items (Read)' scope
            5. Copy and paste the token above
            
            **Required Permissions:**
            - Work Items: Read
            - Project and Team: Read
            """)
        
        return pat if pat else None
    
    def display_header(self):
        """Display the main dashboard header"""
        st.title("📊 Azure DevOps Sprint Dashboard")
        st.markdown(f"""
        **Organization:** {AZURE_DEVOPS_CONFIG['organization']} | 
        **Project:** {AZURE_DEVOPS_CONFIG['project']} | 
        **Team:** {AZURE_DEVOPS_CONFIG['team']}
        """)
        st.divider()
    
    def load_data(self, pat: str) -> bool:
        """
        Load data from Azure DevOps
        
        Args:
            pat: Personal Access Token
            
        Returns:
            True if data loaded successfully, False otherwise
        """
        try:
            # Initialize client
            self.client = AzureDevOpsClient(pat)
            
            # Get current iteration
            with st.spinner("Fetching current sprint..."):
                current_iteration = self.client.get_current_iteration()
                
                if not current_iteration:
                    st.warning("No active sprint found. Showing all available iterations.")
                    iterations = self.client.get_iterations()
                    if iterations:
                        # Use the most recent iteration
                        current_iteration = iterations[-1]
                    else:
                        st.error("No iterations found for this team.")
                        return False
            
            # Display current sprint info
            st.info(f"📅 **Current Sprint:** {current_iteration['name']}")
            
            # Get work items for current iteration
            with st.spinner("Fetching work items..."):
                iteration_path = current_iteration['path']
                work_items = self.client.get_work_items_by_iteration(iteration_path)
                
                if not work_items:
                    st.warning("No work items found for the current sprint.")
                    return False
            
            # Initialize analyzer
            self.analyzer = SprintAnalyzer(work_items, current_iteration)
            
            st.success(f"✅ Loaded {len(work_items)} work items from sprint: {current_iteration['name']}")
            return True
            
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return False
    
    def display_sprint_overview(self):
        """Display sprint overview section"""
        st.header("📈 Sprint Overview")
        
        # Get sprint summary
        summary_data = self.analyzer.get_sprint_summary()
        
        # Display summary cards
        self.viz.create_sprint_summary_cards(summary_data)
        
        # Sprint details
        col1, col2 = st.columns(2)
        
        with col1:
            # Sprint dates
            if self.analyzer.iteration_info:
                start_date = pd.to_datetime(self.analyzer.iteration_info['attributes']['startDate']).strftime('%Y-%m-%d')
                end_date = pd.to_datetime(self.analyzer.iteration_info['attributes']['finishDate']).strftime('%Y-%m-%d')
                st.info(f"📅 **Sprint Duration:** {start_date} to {end_date}")
        
        with col2:
            # Velocity info
            velocity_data = self.analyzer.get_velocity_data()
            if velocity_data:
                st.info(f"⚡ **Velocity:** {velocity_data.get('velocity_per_day', 0):.1f} SP/day")
    
    def display_burndown_analysis(self):
        """Display burndown analysis section"""
        st.header("🔥 Burndown Analysis")
        
        # Get daily progress data
        daily_progress = self.analyzer.get_daily_progress()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Burndown chart
            burndown_fig = self.viz.create_burndown_chart(daily_progress)
            st.plotly_chart(burndown_fig, use_container_width=True)
        
        with col2:
            # Velocity metrics
            velocity_data = self.analyzer.get_velocity_data()
            velocity_fig = self.viz.create_velocity_chart(velocity_data)
            st.plotly_chart(velocity_fig, use_container_width=True)
    
    def display_work_item_analysis(self):
        """Display work item analysis section"""
        st.header("📋 Work Item Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Work item type distribution
            type_dist = self.analyzer.get_work_item_type_distribution()
            type_fig = self.viz.create_work_item_type_chart(type_dist)
            st.plotly_chart(type_fig, use_container_width=True)
        
        with col2:
            # State distribution
            summary_data = self.analyzer.get_sprint_summary()
            state_fig = self.viz.create_state_distribution_chart(summary_data.get('state_distribution', {}))
            st.plotly_chart(state_fig, use_container_width=True)
        
        # Priority distribution
        priority_data = self.analyzer.get_priority_distribution()
        priority_fig = self.viz.create_priority_distribution_chart(priority_data)
        st.plotly_chart(priority_fig, use_container_width=True)
    
    def display_team_analysis(self):
        """Display team analysis section"""
        st.header("👥 Team Analysis")
        
        # Assignee workload
        assignee_workload = self.analyzer.get_assignee_workload()
        workload_fig = self.viz.create_assignee_workload_chart(assignee_workload)
        st.plotly_chart(workload_fig, use_container_width=True)
        
        # Detailed workload table
        if not assignee_workload.empty:
            st.subheader("📊 Detailed Team Workload")
            st.dataframe(
                assignee_workload,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "assigned_to": st.column_config.TextColumn("Assignee", width="medium"),
                    "total_items": st.column_config.NumberColumn("Total Items", width="small"),
                    "story_points": st.column_config.NumberColumn("Story Points", width="small"),
                    "completed_items": st.column_config.NumberColumn("Completed", width="small"),
                    "completed_story_points": st.column_config.NumberColumn("Completed SP", width="small"),
                    "completion_rate": st.column_config.NumberColumn("Completion %", width="small", format="%.1f%%")
                }
            )
    
    def display_quality_metrics(self):
        """Display quality and process metrics"""
        st.header("📊 Quality & Process Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Cycle time analysis
            cycle_time_data = self.analyzer.get_cycle_time_analysis()
            cycle_time_fig = self.viz.create_cycle_time_chart(cycle_time_data)
            st.plotly_chart(cycle_time_fig, use_container_width=True)
        
        with col2:
            # Blocked items
            blocked_items = self.analyzer.get_blocked_items()
            self.viz.display_blocked_items_table(blocked_items)
        
        # Cycle time details table
        if not cycle_time_data.empty:
            st.subheader("⏱️ Cycle Time Details")
            st.dataframe(
                cycle_time_data,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "work_item_type": st.column_config.TextColumn("Work Item Type", width="medium"),
                    "count": st.column_config.NumberColumn("Count", width="small"),
                    "avg_cycle_time": st.column_config.NumberColumn("Avg Days", width="small", format="%.1f"),
                    "median_cycle_time": st.column_config.NumberColumn("Median Days", width="small", format="%.1f"),
                    "min_cycle_time": st.column_config.NumberColumn("Min Days", width="small"),
                    "max_cycle_time": st.column_config.NumberColumn("Max Days", width="small")
                }
            )
    
    def display_raw_data_tab(self):
        """Display raw data in tab format"""
        st.header("🔍 Raw Data")
        
        if self.analyzer and not self.analyzer.df.empty:
            st.subheader("Work Items Data")
            
            # Display data summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Work Items", len(self.analyzer.df))
            with col2:
                st.metric("Columns", len(self.analyzer.df.columns))
            with col3:
                # Download button
                csv = self.analyzer.df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"sprint_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            st.divider()
            
            # Display the dataframe
            st.dataframe(
                self.analyzer.df,
                use_container_width=True,
                hide_index=True
            )
            
            # Data info
            with st.expander("📊 Data Information", expanded=False):
                st.write("**Column Information:**")
                for col in self.analyzer.df.columns:
                    non_null_count = self.analyzer.df[col].count()
                    total_count = len(self.analyzer.df)
                    st.write(f"- **{col}**: {non_null_count}/{total_count} non-null values")
        else:
            st.warning("No data available to display.")
    
    def run(self):
        """Run the main dashboard application"""
        # Setup sidebar and get PAT
        pat = self.setup_sidebar()
        
        # Display header
        self.display_header()
        
        if not pat:
            st.warning("⚠️ Please enter your Azure DevOps Personal Access Token in the sidebar to continue.")
            st.info("👈 Use the sidebar to configure your connection settings.")
            return
        
        # Load data
        if not self.load_data(pat):
            return
        
        # Create tabs for different sections
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📈 Sprint Overview", 
            "🔥 Burndown Analysis", 
            "📋 Work Items", 
            "👥 Team Analysis", 
            "📊 Quality Metrics", 
            "🔍 Raw Data"
        ])
        
        with tab1:
            self.display_sprint_overview()
        
        with tab2:
            self.display_burndown_analysis()
        
        with tab3:
            self.display_work_item_analysis()
        
        with tab4:
            self.display_team_analysis()
        
        with tab5:
            self.display_quality_metrics()
        
        with tab6:
            self.display_raw_data_tab()
        
        # Footer
        st.markdown("---")
        st.markdown("*Dashboard last updated: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "*")


def main():
    """Main function to run the dashboard"""
    dashboard = SprintDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
