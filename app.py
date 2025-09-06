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
        
        # Authentication Section
        st.sidebar.subheader("🔐 Authentication")
        pat = st.sidebar.text_input(
            "Personal Access Token",
            type="password",
            help="Enter your Azure DevOps Personal Access Token"
        )
        
        # Azure DevOps Settings Section
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
        
        # Data Configuration Section
        st.sidebar.subheader("📊 Data Configuration")
        
        # Initialize session state for iterations and area paths if not exists
        if 'available_iterations' not in st.session_state:
            st.session_state.available_iterations = []
        if 'available_area_paths' not in st.session_state:
            st.session_state.available_area_paths = []
        
        # Sprint and Area Path loading
        if pat and organization and project and team:
            col1, col2 = st.sidebar.columns(2)
            
            with col1:
                # Load Sprints button
                if st.button("🔄 Load Sprints", use_container_width=True):
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
            
            with col2:
                # Load Area Paths button
                if st.button("📁 Load Areas", use_container_width=True):
                    with st.spinner("Loading area paths..."):
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
                            area_paths = temp_client.get_area_paths("TaxProf")
                            
                            if area_paths:
                                st.session_state.available_area_paths = area_paths
                                st.sidebar.success(f"✅ Loaded {len(area_paths)} area paths")
                            else:
                                st.sidebar.warning("No area paths found under TaxProf")
                        except Exception as e:
                            st.sidebar.error(f"Failed to load area paths: {str(e)}")
        
        # Sprint dropdown - show all available sprints
        sprint_options = ["Select a sprint..."]
        default_sprint_index = 0
        
        if st.session_state.available_iterations:
            # Show all sprints (no filtering)
            all_iterations = st.session_state.available_iterations
            sprint_options.extend([iteration['name'] for iteration in all_iterations])
            
            # Find current sprint and set as default
            from datetime import timezone
            current_date = datetime.now(timezone.utc)
            
            for i, iteration in enumerate(all_iterations):
                start_date = datetime.fromisoformat(iteration['attributes']['startDate'].replace('Z', '+00:00'))
                finish_date = datetime.fromisoformat(iteration['attributes']['finishDate'].replace('Z', '+00:00'))
                
                if start_date <= current_date <= finish_date:
                    default_sprint_index = i + 1  # +1 because of "Select a sprint..." at index 0
                    break
            
            # Update session state to include all iterations for later use
            st.session_state.filtered_iterations = all_iterations
        
        # Sprint selection
        use_dropdown = st.sidebar.checkbox("Use dropdown selection", value=True, help="Uncheck to manually enter sprint name")
        
        if use_dropdown and sprint_options and len(sprint_options) > 1:
            selected_sprint = st.sidebar.selectbox(
                "Select Sprint",
                options=sprint_options,
                index=default_sprint_index,
                help="Select the sprint to analyze (current sprint selected by default)"
            )
        else:
            selected_sprint = st.sidebar.text_input(
                "Sprint Name",
                value="",
                placeholder="Enter sprint name (e.g., Sprint 2024.1, 2024\\Sprint 1)",
                help="Enter the exact sprint name or iteration path"
            )
            
            if sprint_options and len(sprint_options) > 1:
                with st.sidebar.expander("📋 Available Sprints", expanded=False):
                    for sprint in sprint_options[1:]:
                        st.write(f"• {sprint}")
        
        # Area Path selection
        use_area_dropdown = st.sidebar.checkbox("Use area path dropdown", value=True, help="Uncheck to manually enter area path")
        
        area_path_options = ["Select an area path..."]
        default_area_index = 0
        
        if st.session_state.available_area_paths:
            area_path_options.extend(st.session_state.available_area_paths)
            default_area_path = "TaxProf\\us\\taxAuto\\ADGE\\Prep"
            if default_area_path in st.session_state.available_area_paths:
                default_area_index = st.session_state.available_area_paths.index(default_area_path) + 1
        
        if use_area_dropdown and area_path_options and len(area_path_options) > 1:
            area_path = st.sidebar.selectbox(
                "Select Area Path",
                options=area_path_options,
                index=default_area_index,
                help="Select the area path to filter work items"
            )
            if area_path == "Select an area path...":
                area_path = ""
        else:
            area_path = st.sidebar.text_input(
                "Area Path",
                value="TaxProf\\us\\taxAuto\\ADGE\\Prep",
                placeholder="Enter area path (e.g., TaxProf\\us\\taxAuto\\ADGE\\Prep)",
                help="Enter the area path to filter work items"
            )
            
            if area_path_options and len(area_path_options) > 1:
                with st.sidebar.expander("📁 Available Area Paths", expanded=False):
                    for path in area_path_options[1:]:
                        st.write(f"• {path}")
        
        # Fetch Data button
        fetch_data_disabled = (
            not pat or not organization or not project or not team or 
            selected_sprint == "Select a sprint..." or not selected_sprint or not area_path
        )
        
        if st.sidebar.button("📥 Fetch Data", disabled=fetch_data_disabled):
            st.session_state.fetch_data_clicked = True
        
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
            4. Load available sprints and area paths
            5. Select sprint and area path (or enter manually)
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
            
            # Find selected iteration from all available sprints
            selected_iteration = None
            iterations_to_search = st.session_state.get('filtered_iterations', st.session_state.get('available_iterations', []))
            
            for iteration in iterations_to_search:
                if iteration['name'] == config['selected_sprint']:
                    selected_iteration = iteration
                    break
            
            # If not found in loaded iterations, try to use the sprint name directly
            if not selected_iteration:
                st.info(f"Sprint '{config['selected_sprint']}' not found in loaded iterations. Attempting to fetch data using the provided sprint name...")
                
                # Create a mock iteration object for manually entered sprint names
                selected_iteration = {
                    'name': config['selected_sprint'],
                    'path': config['selected_sprint'],  # Use the sprint name as path
                    'attributes': {
                        'startDate': '2024-01-01T00:00:00Z',  # Default dates
                        'finishDate': '2024-12-31T23:59:59Z'
                    }
                }
            
            # Get work items for selected iteration
            with st.spinner("Fetching work items..."):
                iteration_path = selected_iteration['path']
                work_items = self.client.get_work_items_by_iteration(iteration_path, config['area_path'])
                
                if not work_items:
                    st.warning("No work items found for the selected sprint and area path. Please verify the sprint name is correct.")
                    return False
            
            # Initialize analyzer
            self.analyzer = SprintAnalyzer(work_items, selected_iteration)
            
            return True
            
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return False
    
    def display_sprint_overview(self):
        """Display enhanced sprint overview section with comprehensive analytics"""
        # Beautiful header with gradient background effect
        st.markdown("""
        <div style="
            background: linear-gradient(90deg, #A8DADC 0%, #F1FAEE 100%);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        ">
            <h1 style="color: #2E2E2E; margin: 0; font-size: 2.5em;">📈 Sprint Overview</h1>
            <p style="color: #6C757D; margin: 5px 0 0 0; font-size: 1.1em;">Comprehensive sprint analytics and insights</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Get comprehensive sprint data
        summary_data = self.analyzer.get_sprint_summary()
        velocity_data = self.analyzer.get_velocity_data()
        type_distribution = self.analyzer.get_work_item_type_distribution()
        assignee_workload = self.analyzer.get_assignee_workload()
        
        # Display summary cards with beautiful styling
        st.markdown("### 📊 Sprint Metrics")
        with st.container():
            self.viz.create_sprint_summary_cards(summary_data)
        
        # Sprint Information Section
        st.subheader("📊 Sprint Information")
        
        # Display key sprint data prominently
        sprint_name = self.analyzer.iteration_info['name'] if self.analyzer.iteration_info else "Unknown Sprint"
        total_work_items = len(self.analyzer.df) if self.analyzer and not self.analyzer.df.empty else 0
        area_path = st.session_state.get('current_config', {}).get('area_path', 'Not specified')
        
        st.markdown(f"""
        📅 **Selected Sprint:** {sprint_name}
        
        ✅ **Loaded {total_work_items} work items** from sprint: {sprint_name}
        
        🎯 **Area Path Filter:** {area_path}
        """)
        
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Sprint dates and duration
            if self.analyzer.iteration_info:
                start_date = pd.to_datetime(self.analyzer.iteration_info['attributes']['startDate']).tz_localize(None)
                end_date = pd.to_datetime(self.analyzer.iteration_info['attributes']['finishDate']).tz_localize(None)
                current_date = pd.to_datetime(datetime.now()).tz_localize(None)
                
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
        
        # Important Work Done Section
        st.subheader("🎯 Important Work Completed")
        
        important_work = self.analyzer.get_important_work_analysis()
        
        if important_work and important_work.get('achievements'):
            # Display key achievements in columns
            achievement_cols = st.columns(min(len(important_work['achievements']), 4))
            
            for i, achievement in enumerate(important_work['achievements'][:4]):
                with achievement_cols[i % 4]:
                    st.metric(
                        achievement['type'],
                        f"{achievement['count']} items",
                        f"{achievement['story_points']:.0f} SP"
                    )
            
            # Detailed work breakdown
            with st.expander("📋 Detailed Work Breakdown", expanded=False):
                for achievement in important_work['achievements']:
                    st.markdown(f"### {achievement['type']}")
                    
                    if achievement['items']:
                        work_df = pd.DataFrame(achievement['items'])
                        st.dataframe(
                            work_df,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "title": st.column_config.TextColumn("Work Item", width="large"),
                                "work_item_type": st.column_config.TextColumn("Type", width="small"),
                                "assigned_to": st.column_config.TextColumn("Assignee", width="medium"),
                                "story_points": st.column_config.NumberColumn("SP", width="small")
                            }
                        )
                    st.divider()
        else:
            st.info("📋 No significant work completed yet in this sprint")
        
        # Sprint Champion Section
        st.subheader("🏆 Sprint Champion")
        
        champion_analysis = self.analyzer.get_sprint_champion_analysis()
        
        if champion_analysis and champion_analysis.get('champion'):
            champion = champion_analysis['champion']
            achievements = champion_analysis['achievements']
            team_avg = champion_analysis['team_average']
            
            # Champion Header Card
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
                border: 2px solid #FFD700;
            ">
                <h2 style="color: #2E2E2E; margin: 0; font-size: 2em;">🥇 {champion['assignee']}</h2>
                <p style="color: #4A4A4A; margin: 5px 0 0 0; font-size: 1.2em; font-weight: bold;">Sprint Champion - Score: {champion['score']:.1f} points</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Champion Key Metrics
            st.markdown("#### 📊 Champion Performance")
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                st.metric(
                    "Completion Rate",
                    f"{champion['completion_rate']:.1f}%",
                    f"{champion['completion_rate'] - team_avg['completion_rate']:+.1f}% vs avg"
                )
            
            with metric_col2:
                st.metric(
                    "Story Points",
                    f"{champion['completed_story_points']:.0f} / {champion['story_points']:.0f}",
                    f"{champion['story_points'] - team_avg['story_points']:+.1f} vs avg"
                )
            
            with metric_col3:
                total_completed_sp = summary_data.get('completed_story_points', 0)
                contribution_pct = (champion['completed_story_points'] / total_completed_sp * 100) if total_completed_sp > 0 else 0
                st.metric(
                    "Sprint Contribution",
                    f"{contribution_pct:.1f}%",
                    "of total completed work"
                )
            
            with metric_col4:
                st.metric(
                    "Work Items",
                    f"{champion['total_items']:.0f} items",
                    f"{champion['high_priority_completed']} high priority"
                )
            
            st.divider()
            
            # Champion Details in organized sections
            detail_col1, detail_col2 = st.columns([1, 1])
            
            with detail_col1:
                st.markdown("#### 🎯 Work Quality Breakdown")
                quality_data = [
                    {"Category": "🚨 High Priority Items", "Count": champion['high_priority_completed']},
                    {"Category": "💪 Significant Features", "Count": champion['significant_items_completed']},
                    {"Category": "🐛 Bug Fixes", "Count": champion['bug_fixes']},
                    {"Category": "🔄 Work Item Types", "Count": len(champion['work_types'])}
                ]
                
                for item in quality_data:
                    st.markdown(f"**{item['Category']}:** {item['Count']}")
                
                # Achievements
                if achievements:
                    st.markdown("#### 🏅 Achievements")
                    for achievement in achievements:
                        st.markdown(f"• {achievement}")
            
            with detail_col2:
                # Sample work completed
                if champion.get('sample_work') and len(champion['sample_work']) > 0:
                    st.markdown("#### 🔍 Recent Work Completed")
                    sample_df = pd.DataFrame(champion['sample_work'][:5])  # Show top 5
                    st.dataframe(
                        sample_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "title": st.column_config.TextColumn("Work Item", width="large"),
                            "work_item_type": st.column_config.TextColumn("Type", width="small"),
                            "story_points": st.column_config.NumberColumn("SP", width="small")
                        }
                    )
                else:
                    st.markdown("#### 🏆 Champion Recognition")
                    st.info("🌟 **Outstanding Performance**\n\nThis team member has demonstrated exceptional productivity and quality in their sprint contributions.")
            
            # Team Leaderboard (simplified)
            if len(champion_analysis.get('all_scores', [])) > 1:
                st.divider()
                st.markdown("#### 🏅 Top Contributors This Sprint")
                
                leaderboard_data = []
                for i, contributor in enumerate(champion_analysis['all_scores'][:5]):  # Top 5
                    leaderboard_data.append({
                        '🏆': i + 1,
                        'Name': contributor['assignee'],
                        'Score': f"{contributor['score']:.1f}",
                        'Completion': f"{contributor['completion_rate']:.0f}%",
                        'Story Points': f"{contributor['completed_story_points']:.0f}",
                        'High Priority': contributor['high_priority_completed']
                    })
                
                leaderboard_df = pd.DataFrame(leaderboard_data)
                st.dataframe(
                    leaderboard_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "🏆": st.column_config.NumberColumn("Rank", width="small"),
                        "Name": st.column_config.TextColumn("Contributor", width="medium"),
                        "Score": st.column_config.TextColumn("Score", width="small"),
                        "Completion": st.column_config.TextColumn("Completion", width="small"),
                        "Story Points": st.column_config.TextColumn("Completed SP", width="small"),
                        "High Priority": st.column_config.NumberColumn("Priority Items", width="small")
                    }
                )
        else:
            st.info("🏆 No champion data available - need team members with significant work completed")
        
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
    
    def display_getting_started_section(self, config: dict):
        """Display comprehensive getting started section for first-time users"""
        st.header("📋 Getting Started")
        st.markdown("Welcome to Azure DevOps Sprint Dashboard. Follow these steps to set up your dashboard:")
        
        # Step-by-step guide
        st.markdown("### 🚀 Quick Setup Guide")
        
        # Step 1: Authentication
        step1_status = "✅" if config['pat'] else "⏳"
        step1_color = "success" if config['pat'] else "info"
        
        with st.container():
            st.markdown(f"### {step1_status} Step 1: Authentication")
            if config['pat']:
                st.success("✅ Personal Access Token configured successfully!")
            else:
                st.info("🔐 **Set up your Personal Access Token (PAT)**")
                
                with st.expander("📖 How to create a Personal Access Token", expanded=not config['pat']):
                    st.markdown("""
                    **Follow these steps to create your PAT:**
                    
                    1. 🌐 Go to your Azure DevOps organization
                    2. 👤 Click on your profile picture (top right corner)
                    3. 🔧 Select **"Personal Access Tokens"**
                    4. ➕ Click **"+ New Token"**
                    5. 📝 Give it a name (e.g., "Sprint Dashboard")
                    6. 📅 Set expiration date (recommended: 90 days)
                    7. 🔍 Under **Scopes**, select **"Work Items (Read)"**
                    8. ✨ Click **"Create"**
                    9. 📋 **Copy the token immediately** (you won't see it again!)
                    10. 📥 Paste it in the sidebar under "Personal Access Token"
                    
                    **Required Permissions:**
                    - ✅ Work Items: Read
                    - ✅ Project and Team: Read
                    """)
                
                st.markdown("👈 **Action Required:** Enter your PAT in the sidebar to continue")
        
        st.divider()
        
        # Step 2: Azure DevOps Settings
        step2_status = "✅" if all([config['organization'], config['project'], config['team']]) else "⏳"
        
        with st.container():
            st.markdown(f"### {step2_status} Step 2: Azure DevOps Settings")
            if all([config['organization'], config['project'], config['team']]):
                st.success(f"✅ Connected to: {config['organization']}/{config['project']}/{config['team']}")
            else:
                st.info("🏢 **Configure your Azure DevOps connection**")
                
                missing_fields = []
                if not config['organization']:
                    missing_fields.append("Organization")
                if not config['project']:
                    missing_fields.append("Project")
                if not config['team']:
                    missing_fields.append("Team")
                
                if missing_fields:
                    st.warning(f"⚠️ Missing: {', '.join(missing_fields)}")
                
                with st.expander("ℹ️ Where to find these values", expanded=not all([config['organization'], config['project'], config['team']])):
                    st.markdown("""
                    **Finding your Azure DevOps settings:**
                    
                    **Organization:** 
                    - Look at your Azure DevOps URL: `https://dev.azure.com/YOUR-ORG/`
                    - Example: If URL is `https://dev.azure.com/tr-tax/`, then Organization = `tr-tax`
                    
                    **Project:**
                    - This is your project name in Azure DevOps
                    - Example: `TaxProf`, `MyProject`, etc.
                    
                    **Team:**
                    - Usually the same as your project name
                    - Or check under Project Settings > Teams
                    """)
                
                st.markdown("👈 **Action Required:** Fill in Organization, Project, and Team in the sidebar")
        
        st.divider()
        
        # Step 3: Test Connection
        step3_status = "✅" if st.session_state.get('connection_tested') else "⏳"
        
        with st.container():
            st.markdown(f"### {step3_status} Step 3: Test Connection")
            if st.session_state.get('connection_tested'):
                st.success("✅ Connection tested successfully!")
            else:
                st.info("🔍 **Verify your connection**")
                if config['pat'] and all([config['organization'], config['project'], config['team']]):
                    st.markdown("👈 **Action Required:** Click 'Test Connection' button in the sidebar")
                else:
                    st.warning("⚠️ Complete Steps 1 & 2 first before testing connection")
        
        st.divider()
        
        # Step 4: Load Data
        sprints_loaded = len(st.session_state.get('available_iterations', []))
        areas_loaded = len(st.session_state.get('available_area_paths', []))
        step4_status = "✅" if sprints_loaded > 0 else "⏳"
        
        with st.container():
            st.markdown(f"### {step4_status} Step 4: Load Sprints and Area Paths")
            if sprints_loaded > 0:
                st.success(f"✅ Loaded {sprints_loaded} sprints and {areas_loaded} area paths")
            else:
                st.info("📊 **Load available data for selection**")
                if st.session_state.get('connection_tested'):
                    st.markdown("""
                    **Load your data:**
                    - 🔄 Click **'Load Sprints'** to fetch available sprints
                    - 📁 Click **'Load Areas'** to fetch area paths under TaxProf
                    
                    **Or enter manually:**
                    - ☑️ Uncheck the dropdown options to enter sprint/area path manually
                    """)
                    st.markdown("👈 **Action Required:** Click 'Load Sprints' and 'Load Areas' buttons in the sidebar")
                else:
                    st.warning("⚠️ Test connection first before loading data")
        
        st.divider()
        
        # Step 5: Select Sprint and Area Path
        sprint_selected = config['selected_sprint'] != "Select a sprint..." and config['selected_sprint']
        area_selected = bool(config['area_path'])
        step5_status = "✅" if sprint_selected and area_selected else "⏳"
        
        with st.container():
            st.markdown(f"### {step5_status} Step 5: Select Sprint and Area Path")
            if sprint_selected and area_selected:
                st.success(f"✅ Selected: {config['selected_sprint']} | Area: {config['area_path']}")
            else:
                st.info("🎯 **Choose your sprint and area path**")
                
                if not sprint_selected:
                    if sprints_loaded > 0:
                        st.markdown("👈 **Action Required:** Select a sprint from the dropdown in the sidebar")
                    else:
                        st.warning("⚠️ Load sprints first, or uncheck dropdown to enter manually")
                
                if not area_selected:
                    st.markdown("👈 **Action Required:** Select or enter an area path in the sidebar")
        
        st.divider()
        
        # Step 6: Fetch Data
        step6_status = "✅" if st.session_state.get('data_loaded') else "⏳"
        
        with st.container():
            st.markdown(f"### {step6_status} Step 6: Fetch Data and View Dashboard")
            if st.session_state.get('data_loaded'):
                st.success("✅ Dashboard loaded successfully! Scroll down to view your sprint analytics.")
            else:
                st.info("📥 **Load your sprint dashboard**")
                
                can_fetch = (config['pat'] and all([config['organization'], config['project'], config['team']]) 
                           and sprint_selected and area_selected)
                
                if can_fetch:
                    st.markdown("👈 **Action Required:** Click 'Fetch Data' button in the sidebar to load your dashboard")
                    st.success("🎉 All requirements met! Ready to fetch data.")
                else:
                    missing_steps = []
                    if not config['pat']:
                        missing_steps.append("Personal Access Token")
                    if not all([config['organization'], config['project'], config['team']]):
                        missing_steps.append("Azure DevOps Settings")
                    if not sprint_selected:
                        missing_steps.append("Sprint Selection")
                    if not area_selected:
                        missing_steps.append("Area Path")
                    
                    st.warning(f"⚠️ Complete these steps first: {', '.join(missing_steps)}")
        
        # Progress indicator
        completed_steps = sum([
            bool(config['pat']),
            bool(all([config['organization'], config['project'], config['team']])),
            bool(st.session_state.get('connection_tested', False)),
            bool(sprints_loaded > 0),
            bool(sprint_selected and area_selected),
            bool(st.session_state.get('data_loaded', False))
        ])
        
        progress = completed_steps / 6
        st.progress(progress, text=f"Setup Progress: {completed_steps}/6 steps completed ({progress:.0%})")
        
        if completed_steps == 6:
            st.balloons()
            st.success("🎉 **Setup Complete!** Your dashboard is ready. Explore the tabs below for detailed sprint analytics.")
    
    def run(self):
        """Run the main dashboard application"""
        # Setup sidebar and get configuration
        config = self.setup_sidebar()
        
        # Display header with current config
        self.display_header(config)
        
        # Show Getting Started section only if data is not loaded
        if not st.session_state.get('data_loaded', False):
            # Show as a popup-style guide with option to dismiss
            with st.container():
                # Add a toggle to show/hide the getting started guide
                if 'show_getting_started' not in st.session_state:
                    st.session_state.show_getting_started = True
                
                # Show getting started guide if enabled
                if st.session_state.show_getting_started:
                    # Create columns for the dismiss button
                    guide_col1, guide_col2 = st.columns([10, 1])
                    
                    with guide_col2:
                        if st.button("✕", help="Hide Getting Started Guide", key="hide_guide"):
                            st.session_state.show_getting_started = False
                            st.rerun()
                    
                    with guide_col1:
                        self.display_getting_started_section(config)
                else:
                    # Show a button to bring back the guide if hidden
                    if st.button("📋 Show Getting Started Guide", help="Show setup instructions"):
                        st.session_state.show_getting_started = True
                        st.rerun()
        
        # Check if all required fields are filled and show appropriate messages
        if not config['pat']:
            if not st.session_state.get('data_loaded', False):
                st.info("👆 **Next Step:** Enter your Personal Access Token in the sidebar")
            return
        
        if not all([config['organization'], config['project'], config['team']]):
            if not st.session_state.get('data_loaded', False):
                st.info("👆 **Next Step:** Complete your Azure DevOps settings in the sidebar")
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
            # Create tabs for different sections including Getting Started as the last tab
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "📈 Sprint Overview", 
                "🔥 Burndown Analysis", 
                "📋 Work Items", 
                "👥 Team Analysis", 
                "📊 Quality Metrics", 
                "🔍 Raw Data",
                "📋 Getting Started"
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
            
            with tab7:
                # Display Getting Started guide in the tab
                config = self.setup_sidebar()  # Get current config for the guide
                self.display_getting_started_section(config)
            
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
