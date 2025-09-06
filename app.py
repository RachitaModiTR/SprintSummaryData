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
    
    def setup_sidebar(self) -> dict:
        """
        Setup sidebar with configuration options
        
        Returns:
            Dictionary with configuration values
        """
        st.sidebar.title("🔧 Configuration")
        
        # Azure DevOps Settings
        st.sidebar.subheader("🏢 Azure DevOps Settings")
        
        # Organization input
        organization = st.sidebar.text_input(
            "Organization",
            value=AZURE_DEVOPS_CONFIG['organization'],
            help="Azure DevOps organization name"
        )
        
        # Project input
        project = st.sidebar.text_input(
            "Project",
            value=AZURE_DEVOPS_CONFIG['project'],
            help="Azure DevOps project name"
        )
        
        # Team input
        team = st.sidebar.text_input(
            "Team",
            value=AZURE_DEVOPS_CONFIG['team'],
            help="Azure DevOps team name"
        )
        
        st.sidebar.divider()
        
        # Personal Access Token input
        st.sidebar.subheader("🔐 Authentication")
        pat = st.sidebar.text_input(
            "Personal Access Token",
            type="password",
            help="Enter your Azure DevOps Personal Access Token"
        )
        
        # Test connection button
        if pat and st.sidebar.button("🔍 Test Connection"):
            with st.spinner("Testing connection..."):
                # Create temporary config for testing
                temp_config = {
                    'organization': organization,
                    'project': project,
                    'team': team,
                    'base_url': AZURE_DEVOPS_CONFIG['base_url'],
                    'api_version': AZURE_DEVOPS_CONFIG['api_version']
                }
                test_client = AzureDevOpsClient(pat)
                test_client.config = temp_config
                
                if test_client.test_connection():
                    st.sidebar.success("✅ Connection successful!")
                    st.session_state.connection_tested = True
                else:
                    st.sidebar.error("❌ Connection failed. Please check your settings.")
                    st.session_state.connection_tested = False
        
        st.sidebar.divider()
        
        # Sprint and Area Path Configuration
        st.sidebar.subheader("📊 Data Configuration")
        
        # Initialize session state for iterations if not exists
        if 'available_iterations' not in st.session_state:
            st.session_state.available_iterations = []
        
        # Sprint selection
        if pat and organization and project and team:
            # Try to fetch iterations if connection is available
            if st.sidebar.button("🔄 Load Sprints"):
                with st.spinner("Loading available sprints..."):
                    try:
                        temp_config = {
                            'organization': organization,
                            'project': project,
                            'team': team,
                            'base_url': AZURE_DEVOPS_CONFIG['base_url'],
                            'api_version': AZURE_DEVOPS_CONFIG['api_version']
                        }
                        temp_client = AzureDevOpsClient(pat)
                        temp_client.config = temp_config
                        iterations = temp_client.get_iterations()
                        
                        if iterations:
                            st.session_state.available_iterations = iterations
                            st.sidebar.success(f"✅ Loaded {len(iterations)} sprints")
                        else:
                            st.sidebar.warning("No sprints found")
                    except Exception as e:
                        st.sidebar.error(f"Failed to load sprints: {str(e)}")
        
        # Sprint dropdown
        sprint_options = ["Select a sprint..."]
        if st.session_state.available_iterations:
            sprint_options.extend([iteration['name'] for iteration in st.session_state.available_iterations])
        
        selected_sprint = st.sidebar.selectbox(
            "Sprint",
            options=sprint_options,
            help="Select the sprint to analyze"
        )
        
        # Area Path input
        area_path = st.sidebar.text_input(
            "Area Path",
            value="TaxProf\\us\\taxAuto\\ADGE\\Prep",
            help="Enter the area path to filter work items"
        )
        
        # Fetch Data button
        fetch_data_disabled = (
            not pat or 
            not organization or 
            not project or 
            not team or 
            selected_sprint == "Select a sprint..." or
            not area_path
        )
        
        if st.sidebar.button("📥 Fetch Data", disabled=fetch_data_disabled):
            st.session_state.fetch_data_clicked = True
        
        st.sidebar.divider()
        
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
            
            **Usage:**
            1. Enter your Azure DevOps settings
            2. Add your Personal Access Token
            3. Test the connection
            4. Load available sprints
            5. Select sprint and area path
            6. Click Fetch Data to load dashboard
            """)
        
        return {
            'pat': pat,
            'organization': organization,
            'project': project,
            'team': team,
            'selected_sprint': selected_sprint,
            'area_path': area_path
        }
    
    def display_header(self, config: dict):
        """Display the main dashboard header"""
        st.title("📊 Azure DevOps Sprint Dashboard")
        st.markdown(f"""
        **Organization:** {config.get('organization', 'Not set')} | 
        **Project:** {config.get('project', 'Not set')} | 
        **Team:** {config.get('team', 'Not set')}
        """)
        st.divider()
    
    def load_data_with_config(self, config: dict) -> bool:
        """
        Load data from Azure DevOps using sidebar configuration
        
        Args:
            config: Configuration dictionary from sidebar
            
        Returns:
            True if data loaded successfully, False otherwise
        """
        try:
            # Create client config
            client_config = {
                'organization': config['organization'],
                'project': config['project'],
                'team': config['team'],
                'base_url': AZURE_DEVOPS_CONFIG['base_url'],
                'api_version': AZURE_DEVOPS_CONFIG['api_version']
            }
            
            # Initialize client
            self.client = AzureDevOpsClient(config['pat'])
            self.client.config = client_config
            
            # Find selected iteration
            selected_iteration = None
            if st.session_state.available_iterations:
                for iteration in st.session_state.available_iterations:
                    if iteration['name'] == config['selected_sprint']:
                        selected_iteration = iteration
                        break
            
            if not selected_iteration:
                st.error("Selected sprint not found. Please load sprints first.")
                return False
            
            # Display current sprint info
            st.info(f"📅 **Selected Sprint:** {selected_iteration['name']}")
            
            # Get work items for selected iteration
            with st.spinner("Fetching work items..."):
                iteration_path = selected_iteration['path']
                work_items = self.client.get_work_items_by_iteration(iteration_path, config['area_path'])
                
                if not work_items:
                    st.warning("No work items found for the selected sprint and area path.")
                    return False
            
            # Initialize analyzer
            self.analyzer = SprintAnalyzer(work_items, selected_iteration)
            
            st.success(f"✅ Loaded {len(work_items)} work items from sprint: {selected_iteration['name']}")
            st.info(f"🎯 **Area Path Filter:** {config['area_path']}")
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
        # Setup sidebar and get configuration
        config = self.setup_sidebar()
        
        # Display header with current config
        self.display_header(config)
        
        # Check if all required fields are filled
        if not config['pat']:
            st.warning("⚠️ Please enter your Azure DevOps Personal Access Token in the sidebar to continue.")
            st.info("👈 Use the sidebar to configure your connection settings.")
            return
        
        if not all([config['organization'], config['project'], config['team']]):
            st.warning("⚠️ Please fill in all Azure DevOps settings (Organization, Project, Team) in the sidebar.")
            st.info("👈 Use the sidebar to configure your connection settings.")
            return
        
        # Check if data should be loaded
        should_load_data = (
            hasattr(st.session_state, 'fetch_data_clicked') and 
            st.session_state.fetch_data_clicked and
            config['selected_sprint'] != "Select a sprint..." and
            config['area_path']
        )
        
        if should_load_data:
            # Reset the flag
            st.session_state.fetch_data_clicked = False
            
            # Load data with new configuration
            if self.load_data_with_config(config):
                st.session_state.data_loaded = True
                st.session_state.current_config = config
            else:
                st.session_state.data_loaded = False
                return
        
        # Check if data is loaded and display dashboard
        if hasattr(st.session_state, 'data_loaded') and st.session_state.data_loaded and self.analyzer:
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
        
        else:
            # Show instructions when no data is loaded
            st.info("📋 **Getting Started:**")
            st.markdown("""
            1. **Configure Settings**: Fill in your Azure DevOps organization, project, and team details
            2. **Add Token**: Enter your Personal Access Token
            3. **Test Connection**: Click the 'Test Connection' button to verify your settings
            4. **Load Sprints**: Click 'Load Sprints' to fetch available sprints
            5. **Select Sprint**: Choose the sprint you want to analyze
            6. **Set Area Path**: Adjust the area path filter if needed
            7. **Fetch Data**: Click 'Fetch Data' to load the dashboard
            """)
            
            # Show current configuration status
            with st.expander("🔍 Current Configuration Status", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Azure DevOps Settings:**")
                    st.write(f"✅ Organization: {config['organization']}" if config['organization'] else "❌ Organization: Not set")
                    st.write(f"✅ Project: {config['project']}" if config['project'] else "❌ Project: Not set")
                    st.write(f"✅ Team: {config['team']}" if config['team'] else "❌ Team: Not set")
                    st.write(f"✅ PAT: {'Set' if config['pat'] else 'Not set'}")
                
                with col2:
                    st.write("**Data Configuration:**")
                    st.write(f"✅ Sprints Loaded: {len(st.session_state.get('available_iterations', []))}")
                    st.write(f"✅ Sprint Selected: {config['selected_sprint']}" if config['selected_sprint'] != "Select a sprint..." else "❌ Sprint: Not selected")
                    st.write(f"✅ Area Path: {config['area_path']}" if config['area_path'] else "❌ Area Path: Not set")


def main():
    """Main function to run the dashboard"""
    dashboard = SprintDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
