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
        
        # Sprint dropdown - filter to show only 2025 sprints
        sprint_options = ["Select a sprint..."]
        if st.session_state.available_iterations:
            # Filter sprints that start with "2025"
            filtered_iterations = [
                iteration for iteration in st.session_state.available_iterations 
                if iteration['name'].startswith('2025')
            ]
            sprint_options.extend([iteration['name'] for iteration in filtered_iterations])
            
            # Update session state to only include filtered iterations for later use
            st.session_state.filtered_iterations = filtered_iterations
        
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
            
            # Find selected iteration from filtered 2025 sprints
            selected_iteration = None
            iterations_to_search = st.session_state.get('filtered_iterations', st.session_state.get('available_iterations', []))
            
            for iteration in iterations_to_search:
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
        """Display enhanced sprint overview section with comprehensive analytics"""
        st.header("📈 Sprint Overview")
        
        # Get comprehensive sprint data
        summary_data = self.analyzer.get_sprint_summary()
        velocity_data = self.analyzer.get_velocity_data()
        type_distribution = self.analyzer.get_work_item_type_distribution()
        assignee_workload = self.analyzer.get_assignee_workload()
        
        # Display summary cards
        self.viz.create_sprint_summary_cards(summary_data)
        
        # Sprint Information Section
        st.subheader("📊 Sprint Information")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Sprint dates and duration
            if self.analyzer.iteration_info:
                start_date = pd.to_datetime(self.analyzer.iteration_info['attributes']['startDate'])
                end_date = pd.to_datetime(self.analyzer.iteration_info['attributes']['finishDate'])
                current_date = pd.to_datetime(datetime.now())
                
                # Calculate sprint progress
                total_days = (end_date - start_date).days
                elapsed_days = min((current_date - start_date).days, total_days)
                remaining_days = max(total_days - elapsed_days, 0)
                progress_percentage = (elapsed_days / total_days * 100) if total_days > 0 else 0
                
                st.info(f"""
                📅 **Sprint Duration:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}
                
                ⏱️ **Progress:** {elapsed_days}/{total_days} days ({progress_percentage:.1f}%)
                
                📈 **Remaining:** {remaining_days} days
                """)
        
        with col2:
            # Velocity and completion metrics
            if velocity_data:
                completion_rate = velocity_data.get('completion_rate', 0)
                velocity_per_day = velocity_data.get('velocity_per_day', 0)
                
                st.info(f"""
                ⚡ **Velocity:** {velocity_per_day:.1f} SP/day
                
                ✅ **Completion Rate:** {completion_rate:.1f}%
                
                🎯 **Planned SP:** {velocity_data.get('planned_story_points', 0)}
                
                ✨ **Completed SP:** {velocity_data.get('completed_story_points', 0)}
                """)
        
        with col3:
            # Team and work item metrics
            total_assignees = len(assignee_workload) if not assignee_workload.empty else 0
            avg_items_per_person = summary_data.get('total_items', 0) / total_assignees if total_assignees > 0 else 0
            
            st.info(f"""
            👥 **Team Size:** {total_assignees} members
            
            📋 **Avg Items/Person:** {avg_items_per_person:.1f}
            
            🔄 **In Progress:** {summary_data.get('in_progress_items', 0)} items
            
            📊 **Work Item Types:** {len(type_distribution)} types
            """)
        
        # Detailed Analytics Section
        st.subheader("📈 Detailed Sprint Analytics")
        
        # Create tabs for different analytics views
        overview_tab1, overview_tab2, overview_tab3 = st.tabs([
            "🎯 Progress Tracking", 
            "👥 Team Performance", 
            "📊 Work Distribution"
        ])
        
        with overview_tab1:
            # Progress tracking with burndown preview
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Mini burndown chart
                daily_progress = self.analyzer.get_daily_progress()
                if not daily_progress.empty:
                    burndown_fig = self.viz.create_burndown_chart(daily_progress)
                    burndown_fig.update_layout(height=300, title="Sprint Burndown Preview")
                    st.plotly_chart(burndown_fig, use_container_width=True)
                else:
                    st.info("📊 No burndown data available for this sprint")
            
            with col2:
                # Progress metrics
                st.markdown("**📊 Progress Metrics**")
                
                # Story points progress bar
                if summary_data.get('total_story_points', 0) > 0:
                    sp_progress = summary_data.get('story_points_completion', 0) / 100
                    st.progress(sp_progress, text=f"Story Points: {sp_progress*100:.1f}%")
                
                # Items progress bar
                if summary_data.get('total_items', 0) > 0:
                    items_progress = summary_data.get('completion_percentage', 0) / 100
                    st.progress(items_progress, text=f"Work Items: {items_progress*100:.1f}%")
                
                # State breakdown
                st.markdown("**📋 State Breakdown**")
                state_dist = summary_data.get('state_distribution', {})
                for state, count in state_dist.items():
                    st.write(f"• **{state}:** {count} items")
        
        with overview_tab2:
            # Team performance overview
            if not assignee_workload.empty:
                # Top performers
                st.markdown("**🏆 Top Performers (by Story Points)**")
                top_performers = assignee_workload.head(5)
                
                for idx, row in top_performers.iterrows():
                    completion_rate = row.get('completion_rate', 0)
                    color = "🟢" if completion_rate >= 80 else "🟡" if completion_rate >= 50 else "🔴"
                    
                    st.write(f"{color} **{row['assigned_to']}**: {row['story_points']:.0f} SP "
                            f"({row['completed_story_points']:.0f} completed, {completion_rate:.1f}%)")
                
                # Team workload chart
                workload_fig = self.viz.create_assignee_workload_chart(assignee_workload)
                workload_fig.update_layout(height=300, title="Team Workload Distribution")
                st.plotly_chart(workload_fig, use_container_width=True)
            else:
                st.info("👥 No team workload data available")
        
        with overview_tab3:
            # Work distribution analytics
            col1, col2 = st.columns(2)
            
            with col1:
                # Work item type distribution
                if not type_distribution.empty:
                    type_fig = self.viz.create_work_item_type_chart(type_distribution)
                    type_fig.update_layout(height=300, title="Work Item Types")
                    st.plotly_chart(type_fig, use_container_width=True)
                else:
                    st.info("📊 No work item type data available")
            
            with col2:
                # Priority distribution
                priority_data = self.analyzer.get_priority_distribution()
                if not priority_data.empty:
                    priority_fig = self.viz.create_priority_distribution_chart(priority_data)
                    priority_fig.update_layout(height=300, title="Priority Distribution")
                    st.plotly_chart(priority_fig, use_container_width=True)
                else:
                    st.info("📊 No priority data available")
        
        # Sprint Health Indicators
        st.subheader("🏥 Sprint Health Indicators")
        
        health_col1, health_col2, health_col3, health_col4 = st.columns(4)
        
        with health_col1:
            # Completion health
            completion_rate = summary_data.get('completion_percentage', 0)
            if completion_rate >= 80:
                st.success(f"✅ **Completion:** {completion_rate:.1f}%\nExcellent progress!")
            elif completion_rate >= 60:
                st.warning(f"⚠️ **Completion:** {completion_rate:.1f}%\nOn track")
            else:
                st.error(f"🚨 **Completion:** {completion_rate:.1f}%\nNeeds attention")
        
        with health_col2:
            # Velocity health
            if velocity_data:
                velocity_per_day = velocity_data.get('velocity_per_day', 0)
                if velocity_per_day >= 2:
                    st.success(f"🚀 **Velocity:** {velocity_per_day:.1f} SP/day\nHigh velocity")
                elif velocity_per_day >= 1:
                    st.info(f"⚡ **Velocity:** {velocity_per_day:.1f} SP/day\nGood pace")
                else:
                    st.warning(f"🐌 **Velocity:** {velocity_per_day:.1f} SP/day\nSlow progress")
        
        with health_col3:
            # Team balance health
            if not assignee_workload.empty:
                workload_std = assignee_workload['story_points'].std()
                workload_mean = assignee_workload['story_points'].mean()
                balance_ratio = workload_std / workload_mean if workload_mean > 0 else 0
                
                if balance_ratio <= 0.3:
                    st.success(f"⚖️ **Balance:** Well distributed\nLow variance")
                elif balance_ratio <= 0.6:
                    st.info(f"⚖️ **Balance:** Moderately balanced\nSome variance")
                else:
                    st.warning(f"⚖️ **Balance:** Uneven distribution\nHigh variance")
        
        with health_col4:
            # Blocked items health
            blocked_items = self.analyzer.get_blocked_items()
            blocked_count = len(blocked_items) if not blocked_items.empty else 0
            
            if blocked_count == 0:
                st.success("🚫 **Blocked:** 0 items\nNo blockers")
            elif blocked_count <= 2:
                st.warning(f"🚫 **Blocked:** {blocked_count} items\nMinor blockers")
            else:
                st.error(f"🚫 **Blocked:** {blocked_count} items\nMultiple blockers")
    
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
