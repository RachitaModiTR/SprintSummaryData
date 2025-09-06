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
    
    def get_important_work_analysis(self) -> Dict:
        """
        Analyze important work done during the sprint
        
        Returns:
            Dictionary with important work analysis
        """
        if self.df.empty:
            return {}
        
        completed_states = ['Done', 'Closed', 'Resolved']
        completed_items = self.df[self.df['state'].isin(completed_states)].copy()
        
        # High priority completed work
        high_priority_work = completed_items[completed_items['priority'] <= 2]
        
        # High story point items (significant work)
        significant_work = completed_items[completed_items['story_points'] >= 5]
        
        # Work by type
        work_by_type = completed_items.groupby('work_item_type').agg({
            'id': 'count',
            'story_points': 'sum',
            'title': lambda x: list(x)[:5]  # Top 5 titles per type
        }).rename(columns={'id': 'count', 'title': 'sample_titles'})
        
        # Key achievements
        achievements = []
        
        if not high_priority_work.empty:
            achievements.append({
                'type': 'High Priority Work',
                'count': len(high_priority_work),
                'story_points': high_priority_work['story_points'].sum(),
                'items': high_priority_work[['title', 'work_item_type', 'assigned_to', 'story_points']].to_dict('records')[:5]
            })
        
        if not significant_work.empty:
            achievements.append({
                'type': 'Significant Features',
                'count': len(significant_work),
                'story_points': significant_work['story_points'].sum(),
                'items': significant_work[['title', 'work_item_type', 'assigned_to', 'story_points']].to_dict('records')[:5]
            })
        
        # Bug fixes
        bug_fixes = completed_items[completed_items['work_item_type'].str.contains('Bug', case=False, na=False)]
        if not bug_fixes.empty:
            achievements.append({
                'type': 'Bug Fixes',
                'count': len(bug_fixes),
                'story_points': bug_fixes['story_points'].sum(),
                'items': bug_fixes[['title', 'work_item_type', 'assigned_to', 'story_points']].to_dict('records')[:5]
            })
        
        # Features/User Stories
        features = completed_items[completed_items['work_item_type'].str.contains('Feature|User Story|Story', case=False, na=False)]
        if not features.empty:
            achievements.append({
                'type': 'Features & Stories',
                'count': len(features),
                'story_points': features['story_points'].sum(),
                'items': features[['title', 'work_item_type', 'assigned_to', 'story_points']].to_dict('records')[:5]
            })
        
        return {
            'total_completed_items': len(completed_items),
            'total_completed_story_points': completed_items['story_points'].sum(),
            'work_by_type': work_by_type.to_dict('index'),
            'achievements': achievements,
            'high_priority_completed': len(high_priority_work),
            'significant_work_completed': len(significant_work)
        }
    
    def get_sprint_champion_analysis(self) -> Dict:
        """
        Determine sprint champion based on comprehensive work analysis
        
        Returns:
            Dictionary with sprint champion analysis
        """
        if self.df.empty:
            return {}
        
        assignee_workload = self.get_assignee_workload()
        
        if assignee_workload.empty:
            return {}
        
        # Filter out unassigned and people with minimal work
        significant_contributors = assignee_workload[
            (assignee_workload['assigned_to'] != 'Unassigned') & 
            (assignee_workload['story_points'] >= 3)
        ].copy()
        
        if significant_contributors.empty:
            return {}
        
        # Calculate champion score based on multiple factors
        completed_states = ['Done', 'Closed', 'Resolved']
        
        champion_scores = []
        for _, contributor in significant_contributors.iterrows():
            assignee = contributor['assigned_to']
            
            # Get assignee's work details
            assignee_work = self.df[self.df['assigned_to'] == assignee]
            completed_work = assignee_work[assignee_work['state'].isin(completed_states)]
            
            # Scoring factors
            completion_rate = contributor['completion_rate']
            story_points = contributor['story_points']
            completed_story_points = contributor['completed_story_points']
            
            # Quality factors
            high_priority_completed = len(completed_work[completed_work['priority'] <= 2])
            significant_items_completed = len(completed_work[completed_work['story_points'] >= 5])
            bug_fixes = len(completed_work[completed_work['work_item_type'].str.contains('Bug', case=False, na=False)])
            
            # Calculate weighted score
            score = (
                completion_rate * 0.4 +  # 40% weight on completion rate
                min(completed_story_points / 10 * 20, 30) +  # Up to 30 points for story points (capped)
                high_priority_completed * 5 +  # 5 points per high priority item
                significant_items_completed * 3 +  # 3 points per significant item
                bug_fixes * 2  # 2 points per bug fix
            )
            
            # Work quality analysis
            work_types = completed_work['work_item_type'].value_counts().to_dict()
            sample_work = completed_work[['title', 'work_item_type', 'story_points', 'priority']].to_dict('records')[:5]
            
            champion_scores.append({
                'assignee': assignee,
                'score': score,
                'completion_rate': completion_rate,
                'story_points': story_points,
                'completed_story_points': completed_story_points,
                'total_items': contributor['total_items'],
                'completed_items': contributor['completed_items'],
                'high_priority_completed': high_priority_completed,
                'significant_items_completed': significant_items_completed,
                'bug_fixes': bug_fixes,
                'work_types': work_types,
                'sample_work': sample_work
            })
        
        # Sort by score to find champion
        champion_scores.sort(key=lambda x: x['score'], reverse=True)
        
        if not champion_scores:
            return {}
        
        champion = champion_scores[0]
        
        # Generate achievements based on work done
        achievements = []
        
        if champion['completion_rate'] >= 90:
            achievements.append("🌟 **Excellence Award** - 90%+ completion rate")
        elif champion['completion_rate'] >= 80:
            achievements.append("⭐ **High Performer** - 80%+ completion rate")
        
        if champion['high_priority_completed'] >= 3:
            achievements.append("🚨 **Priority Master** - Completed multiple high-priority items")
        elif champion['high_priority_completed'] >= 1:
            achievements.append("🎯 **Priority Focus** - Completed high-priority work")
        
        if champion['significant_items_completed'] >= 2:
            achievements.append("💪 **Feature Champion** - Delivered significant features")
        
        if champion['bug_fixes'] >= 3:
            achievements.append("🐛 **Bug Crusher** - Fixed multiple bugs")
        
        if champion['completed_items'] == champion['total_items']:
            achievements.append("🎯 **Perfect Score** - 100% items completed")
        
        # Check if they're the top in story points
        max_story_points = significant_contributors['story_points'].max()
        if champion['story_points'] == max_story_points:
            achievements.append("💪 **Heavy Lifter** - Highest story points in sprint")
        
        # Work diversity
        if len(champion['work_types']) >= 3:
            achievements.append("🔄 **Versatile Contributor** - Worked on diverse item types")
        
        return {
            'champion': champion,
            'achievements': achievements,
            'all_scores': champion_scores,
            'team_average': {
                'completion_rate': significant_contributors['completion_rate'].mean(),
                'story_points': significant_contributors['story_points'].mean(),
                'completed_story_points': significant_contributors['completed_story_points'].mean()
            }
        }
