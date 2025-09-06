"""
Data analysis functions for Azure DevOps Sprint Dashboard
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from config import WORK_ITEM_STATES, WORK_ITEM_TYPES


class SprintAnalyzer:
    """Analyzer for sprint data and metrics"""
    
    def __init__(self, work_items: List[Dict], iteration_info: Dict):
        """
        Initialize the sprint analyzer
        
        Args:
            work_items: List of work item dictionaries
            iteration_info: Iteration/sprint information
        """
        self.work_items = work_items
        self.iteration_info = iteration_info
        self.df = self._create_dataframe()
    
    def _create_dataframe(self) -> pd.DataFrame:
        """
        Create a pandas DataFrame from work items
        
        Returns:
            DataFrame with work item data
        """
        if not self.work_items:
            return pd.DataFrame()
        
        data = []
        for item in self.work_items:
            fields = item.get('fields', {})
            
            # Extract assignee information
            assigned_to = fields.get('System.AssignedTo', {})
            assignee = assigned_to.get('displayName', 'Unassigned') if assigned_to else 'Unassigned'
            
            data.append({
                'id': item.get('id'),
                'title': fields.get('System.Title', ''),
                'work_item_type': fields.get('System.WorkItemType', ''),
                'state': fields.get('System.State', ''),
                'assigned_to': assignee,
                'created_date': pd.to_datetime(fields.get('System.CreatedDate', '')),
                'changed_date': pd.to_datetime(fields.get('System.ChangedDate', '')),
                'story_points': fields.get('Microsoft.VSTS.Scheduling.StoryPoints', 0) or 0,
                'priority': fields.get('Microsoft.VSTS.Common.Priority', 2),
                'tags': fields.get('System.Tags', ''),
                'area_path': fields.get('System.AreaPath', ''),
                'iteration_path': fields.get('System.IterationPath', '')
            })
        
        return pd.DataFrame(data)
    
    def get_sprint_summary(self) -> Dict:
        """
        Get high-level sprint summary metrics
        
        Returns:
            Dictionary with sprint summary data
        """
        if self.df.empty:
            return {}
        
        total_items = len(self.df)
        total_story_points = self.df['story_points'].sum()
        
        # State distribution
        state_counts = self.df['state'].value_counts().to_dict()
        
        # Completed items (Done, Closed, Resolved states)
        completed_states = ['Done', 'Closed', 'Resolved']
        completed_items = self.df[self.df['state'].isin(completed_states)]
        completed_count = len(completed_items)
        completed_story_points = completed_items['story_points'].sum()
        
        # In progress items
        in_progress_states = ['Active', 'Doing', 'In Progress']
        in_progress_count = len(self.df[self.df['state'].isin(in_progress_states)])
        
        # Calculate completion percentage
        completion_percentage = (completed_count / total_items * 100) if total_items > 0 else 0
        story_points_completion = (completed_story_points / total_story_points * 100) if total_story_points > 0 else 0
        
        return {
            'total_items': total_items,
            'total_story_points': total_story_points,
            'completed_items': completed_count,
            'completed_story_points': completed_story_points,
            'in_progress_items': in_progress_count,
            'completion_percentage': completion_percentage,
            'story_points_completion': story_points_completion,
            'state_distribution': state_counts
        }
    
    def get_work_item_type_distribution(self) -> pd.DataFrame:
        """
        Get distribution of work items by type
        
        Returns:
            DataFrame with work item type distribution
        """
        if self.df.empty:
            return pd.DataFrame()
        
        type_dist = self.df.groupby('work_item_type').agg({
            'id': 'count',
            'story_points': 'sum'
        }).rename(columns={'id': 'count'}).reset_index()
        
        return type_dist
    
    def get_assignee_workload(self) -> pd.DataFrame:
        """
        Get workload distribution by assignee
        
        Returns:
            DataFrame with assignee workload data
        """
        if self.df.empty:
            return pd.DataFrame()
        
        assignee_workload = self.df.groupby('assigned_to').agg({
            'id': 'count',
            'story_points': 'sum'
        }).rename(columns={'id': 'total_items'}).reset_index()
        
        # Add completion data
        completed_states = ['Done', 'Closed', 'Resolved']
        completed_by_assignee = self.df[self.df['state'].isin(completed_states)].groupby('assigned_to').agg({
            'id': 'count',
            'story_points': 'sum'
        }).rename(columns={'id': 'completed_items', 'story_points': 'completed_story_points'})
        
        assignee_workload = assignee_workload.merge(
            completed_by_assignee, 
            left_on='assigned_to', 
            right_index=True, 
            how='left'
        ).fillna(0)
        
        # Calculate completion rates
        assignee_workload['completion_rate'] = (
            assignee_workload['completed_items'] / assignee_workload['total_items'] * 100
        ).fillna(0)
        
        return assignee_workload.sort_values('story_points', ascending=False)
    
    def get_priority_distribution(self) -> pd.DataFrame:
        """
        Get distribution of work items by priority
        
        Returns:
            DataFrame with priority distribution
        """
        if self.df.empty:
            return pd.DataFrame()
        
        priority_mapping = {1: 'Critical', 2: 'High', 3: 'Medium', 4: 'Low'}
        
        priority_dist = self.df.copy()
        priority_dist['priority_label'] = priority_dist['priority'].map(priority_mapping)
        
        return priority_dist.groupby('priority_label').agg({
            'id': 'count',
            'story_points': 'sum'
        }).rename(columns={'id': 'count'}).reset_index()
    
    def get_daily_progress(self) -> pd.DataFrame:
        """
        Get daily progress data for burndown chart
        
        Returns:
            DataFrame with daily progress data
        """
        if self.df.empty or not self.iteration_info:
            return pd.DataFrame()
        
        # Get sprint date range
        start_date = pd.to_datetime(self.iteration_info['attributes']['startDate'])
        end_date = pd.to_datetime(self.iteration_info['attributes']['finishDate'])
        
        # Create date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Calculate remaining work for each day
        daily_data = []
        total_story_points = self.df['story_points'].sum()
        
        for date in date_range:
            # Items completed by this date
            completed_items = self.df[
                (self.df['changed_date'] <= date) & 
                (self.df['state'].isin(['Done', 'Closed', 'Resolved']))
            ]
            
            completed_points = completed_items['story_points'].sum()
            remaining_points = total_story_points - completed_points
            
            daily_data.append({
                'date': date,
                'remaining_story_points': remaining_points,
                'completed_story_points': completed_points,
                'total_story_points': total_story_points
            })
        
        return pd.DataFrame(daily_data)
    
    def get_velocity_data(self) -> Dict:
        """
        Calculate team velocity metrics
        
        Returns:
            Dictionary with velocity data
        """
        if self.df.empty or not self.iteration_info:
            return {}
        
        # Sprint duration in days
        start_date = pd.to_datetime(self.iteration_info['attributes']['startDate'])
        end_date = pd.to_datetime(self.iteration_info['attributes']['finishDate'])
        sprint_duration = (end_date - start_date).days
        
        # Completed story points
        completed_states = ['Done', 'Closed', 'Resolved']
        completed_points = self.df[self.df['state'].isin(completed_states)]['story_points'].sum()
        
        # Planned story points
        planned_points = self.df['story_points'].sum()
        
        # Calculate velocity
        velocity = completed_points / sprint_duration if sprint_duration > 0 else 0
        
        return {
            'sprint_duration': sprint_duration,
            'planned_story_points': planned_points,
            'completed_story_points': completed_points,
            'velocity_per_day': velocity,
            'completion_rate': (completed_points / planned_points * 100) if planned_points > 0 else 0
        }
    
    def get_cycle_time_analysis(self) -> pd.DataFrame:
        """
        Analyze cycle time for completed work items
        
        Returns:
            DataFrame with cycle time analysis
        """
        if self.df.empty:
            return pd.DataFrame()
        
        completed_states = ['Done', 'Closed', 'Resolved']
        completed_items = self.df[self.df['state'].isin(completed_states)].copy()
        
        if completed_items.empty:
            return pd.DataFrame()
        
        # Calculate cycle time (from created to completed)
        completed_items['cycle_time_days'] = (
            completed_items['changed_date'] - completed_items['created_date']
        ).dt.days
        
        # Group by work item type
        cycle_time_analysis = completed_items.groupby('work_item_type')['cycle_time_days'].agg([
            'count', 'mean', 'median', 'std', 'min', 'max'
        ]).round(2)
        
        cycle_time_analysis.columns = [
            'count', 'avg_cycle_time', 'median_cycle_time', 
            'std_cycle_time', 'min_cycle_time', 'max_cycle_time'
        ]
        
        return cycle_time_analysis.reset_index()
    
    def get_blocked_items(self) -> pd.DataFrame:
        """
        Identify potentially blocked items
        
        Returns:
            DataFrame with potentially blocked items
        """
        if self.df.empty:
            return pd.DataFrame()
        
        # Items that haven't been updated in the last 3 days and are not completed
        from datetime import timezone
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=3)
        incomplete_states = ['New', 'Active', 'Doing', 'To Do', 'In Progress']
        
        # Make sure changed_date is timezone aware
        df_copy = self.df.copy()
        if not df_copy.empty and not df_copy['changed_date'].dt.tz:
            df_copy['changed_date'] = df_copy['changed_date'].dt.tz_localize('UTC')
        
        blocked_items = df_copy[
            (df_copy['changed_date'] < cutoff_date) & 
            (df_copy['state'].isin(incomplete_states))
        ].copy()
        
        if blocked_items.empty:
            return pd.DataFrame()
        
        blocked_items['days_since_update'] = (
            datetime.now(timezone.utc) - blocked_items['changed_date']
        ).dt.days
        
        return blocked_items[['id', 'title', 'work_item_type', 'state', 'assigned_to', 'days_since_update']].sort_values('days_since_update', ascending=False)
