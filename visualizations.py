"""
Visualization components for Azure DevOps Sprint Dashboard
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st
from typing import Dict, List
from config import CHART_COLORS, WORK_ITEM_TYPES, WORK_ITEM_STATES


class DashboardVisualizations:
    """Class for creating dashboard visualizations"""
    
    def __init__(self):
        """Initialize the visualizations class"""
        self.colors = CHART_COLORS
        self.work_item_types = WORK_ITEM_TYPES
        self.work_item_states = WORK_ITEM_STATES
    
    def create_sprint_summary_cards(self, summary_data: Dict) -> None:
        """
        Create summary cards for sprint overview
        
        Args:
            summary_data: Dictionary with sprint summary metrics
        """
        if not summary_data:
            st.warning("No sprint data available")
            return
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📋 Total Items",
                value=summary_data.get('total_items', 0),
                delta=None
            )
        
        with col2:
            st.metric(
                label="📊 Story Points",
                value=f"{summary_data.get('completed_story_points', 0)}/{summary_data.get('total_story_points', 0)}",
                delta=f"{summary_data.get('story_points_completion', 0):.1f}%"
            )
        
        with col3:
            st.metric(
                label="✅ Completed",
                value=summary_data.get('completed_items', 0),
                delta=f"{summary_data.get('completion_percentage', 0):.1f}%"
            )
        
        with col4:
            st.metric(
                label="🔄 In Progress",
                value=summary_data.get('in_progress_items', 0),
                delta=None
            )
    
    def create_burndown_chart(self, daily_progress: pd.DataFrame) -> go.Figure:
        """
        Create burndown chart
        
        Args:
            daily_progress: DataFrame with daily progress data
            
        Returns:
            Plotly figure object
        """
        if daily_progress.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No burndown data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        fig = go.Figure()
        
        # Ideal burndown line
        total_points = daily_progress['total_story_points'].iloc[0]
        ideal_line = [total_points - (total_points * i / (len(daily_progress) - 1)) 
                     for i in range(len(daily_progress))]
        
        fig.add_trace(go.Scatter(
            x=daily_progress['date'],
            y=ideal_line,
            mode='lines',
            name='Ideal Burndown',
            line=dict(color=self.colors['secondary'], dash='dash'),
            hovertemplate='<b>Ideal</b><br>Date: %{x}<br>Remaining: %{y} SP<extra></extra>'
        ))
        
        # Actual burndown line
        fig.add_trace(go.Scatter(
            x=daily_progress['date'],
            y=daily_progress['remaining_story_points'],
            mode='lines+markers',
            name='Actual Burndown',
            line=dict(color=self.colors['primary'], width=3),
            marker=dict(size=6),
            hovertemplate='<b>Actual</b><br>Date: %{x}<br>Remaining: %{y} SP<extra></extra>'
        ))
        
        fig.update_layout(
            title='Sprint Burndown Chart',
            xaxis_title='Date',
            yaxis_title='Remaining Story Points',
            hovermode='x unified',
            showlegend=True,
            height=400
        )
        
        return fig
    
    def create_work_item_type_chart(self, type_distribution: pd.DataFrame) -> go.Figure:
        """
        Create work item type distribution chart
        
        Args:
            type_distribution: DataFrame with work item type data
            
        Returns:
            Plotly figure object
        """
        if type_distribution.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No work item data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        colors = [self.work_item_types.get(wt, {}).get('color', self.colors['primary']) 
                 for wt in type_distribution['work_item_type']]
        
        fig = go.Figure(data=[
            go.Pie(
                labels=type_distribution['work_item_type'],
                values=type_distribution['count'],
                hole=0.4,
                marker_colors=colors,
                textinfo='label+percent',
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title='Work Items by Type',
            height=400,
            showlegend=True
        )
        
        return fig
    
    def create_state_distribution_chart(self, state_distribution: Dict) -> go.Figure:
        """
        Create work item state distribution chart
        
        Args:
            state_distribution: Dictionary with state counts
            
        Returns:
            Plotly figure object
        """
        if not state_distribution:
            fig = go.Figure()
            fig.add_annotation(
                text="No state data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        states = list(state_distribution.keys())
        counts = list(state_distribution.values())
        colors = [self.work_item_states.get(state, {}).get('color', self.colors['primary']) 
                 for state in states]
        
        fig = go.Figure(data=[
            go.Bar(
                x=states,
                y=counts,
                marker_color=colors,
                text=counts,
                textposition='auto',
                hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title='Work Items by State',
            xaxis_title='State',
            yaxis_title='Count',
            height=400
        )
        
        return fig
    
    def create_assignee_workload_chart(self, assignee_workload: pd.DataFrame) -> go.Figure:
        """
        Create assignee workload chart
        
        Args:
            assignee_workload: DataFrame with assignee workload data
            
        Returns:
            Plotly figure object
        """
        if assignee_workload.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No assignee data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Story Points Distribution', 'Completion Rate'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Story points bar chart
        fig.add_trace(
            go.Bar(
                x=assignee_workload['assigned_to'],
                y=assignee_workload['story_points'],
                name='Total Story Points',
                marker_color=self.colors['primary'],
                hovertemplate='<b>%{x}</b><br>Story Points: %{y}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Completion rate bar chart
        fig.add_trace(
            go.Bar(
                x=assignee_workload['assigned_to'],
                y=assignee_workload['completion_rate'],
                name='Completion Rate (%)',
                marker_color=self.colors['success'],
                hovertemplate='<b>%{x}</b><br>Completion Rate: %{y:.1f}%<extra></extra>'
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            title='Team Workload Analysis',
            height=400,
            showlegend=False
        )
        
        fig.update_xaxes(title_text="Assignee", row=1, col=1)
        fig.update_xaxes(title_text="Assignee", row=1, col=2)
        fig.update_yaxes(title_text="Story Points", row=1, col=1)
        fig.update_yaxes(title_text="Completion Rate (%)", row=1, col=2)
        
        return fig
    
    def create_velocity_chart(self, velocity_data: Dict) -> go.Figure:
        """
        Create velocity visualization
        
        Args:
            velocity_data: Dictionary with velocity metrics
            
        Returns:
            Plotly figure object
        """
        if not velocity_data:
            fig = go.Figure()
            fig.add_annotation(
                text="No velocity data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        categories = ['Planned', 'Completed']
        values = [
            velocity_data.get('planned_story_points', 0),
            velocity_data.get('completed_story_points', 0)
        ]
        colors = [self.colors['warning'], self.colors['success']]
        
        fig = go.Figure(data=[
            go.Bar(
                x=categories,
                y=values,
                marker_color=colors,
                text=values,
                textposition='auto',
                hovertemplate='<b>%{x}</b><br>Story Points: %{y}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title=f'Sprint Velocity (Completion Rate: {velocity_data.get("completion_rate", 0):.1f}%)',
            xaxis_title='Category',
            yaxis_title='Story Points',
            height=400
        )
        
        return fig
    
    def create_cycle_time_chart(self, cycle_time_data: pd.DataFrame) -> go.Figure:
        """
        Create cycle time analysis chart
        
        Args:
            cycle_time_data: DataFrame with cycle time analysis
            
        Returns:
            Plotly figure object
        """
        if cycle_time_data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No cycle time data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=cycle_time_data['work_item_type'],
            y=cycle_time_data['avg_cycle_time'],
            name='Average Cycle Time',
            marker_color=self.colors['info'],
            error_y=dict(
                type='data',
                array=cycle_time_data['std_cycle_time'],
                visible=True
            ),
            hovertemplate='<b>%{x}</b><br>Avg Cycle Time: %{y:.1f} days<br>Count: %{customdata}<extra></extra>',
            customdata=cycle_time_data['count']
        ))
        
        fig.update_layout(
            title='Average Cycle Time by Work Item Type',
            xaxis_title='Work Item Type',
            yaxis_title='Days',
            height=400
        )
        
        return fig
    
    def create_priority_distribution_chart(self, priority_data: pd.DataFrame) -> go.Figure:
        """
        Create priority distribution chart
        
        Args:
            priority_data: DataFrame with priority distribution
            
        Returns:
            Plotly figure object
        """
        if priority_data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No priority data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        priority_colors = {
            'Critical': self.colors['danger'],
            'High': self.colors['warning'],
            'Medium': self.colors['info'],
            'Low': self.colors['success']
        }
        
        colors = [priority_colors.get(priority, self.colors['primary']) 
                 for priority in priority_data['priority_label']]
        
        fig = go.Figure(data=[
            go.Pie(
                labels=priority_data['priority_label'],
                values=priority_data['count'],
                hole=0.4,
                marker_colors=colors,
                textinfo='label+percent',
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Story Points: %{customdata}<extra></extra>',
                customdata=priority_data['story_points']
            )
        ])
        
        fig.update_layout(
            title='Work Items by Priority',
            height=400,
            showlegend=True
        )
        
        return fig
    
    def display_blocked_items_table(self, blocked_items: pd.DataFrame) -> None:
        """
        Display blocked items in a table format
        
        Args:
            blocked_items: DataFrame with blocked items data
        """
        if blocked_items.empty:
            st.info("No potentially blocked items found")
            return
        
        st.subheader("🚫 Potentially Blocked Items")
        st.caption("Items that haven't been updated in the last 3 days")
        
        # Format the dataframe for display
        display_df = blocked_items.copy()
        display_df['title'] = display_df['title'].str[:50] + '...'  # Truncate long titles
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "title": st.column_config.TextColumn("Title", width="large"),
                "work_item_type": st.column_config.TextColumn("Type", width="medium"),
                "state": st.column_config.TextColumn("State", width="medium"),
                "assigned_to": st.column_config.TextColumn("Assignee", width="medium"),
                "days_since_update": st.column_config.NumberColumn("Days Since Update", width="small")
            }
        )
