"""
Azure DevOps API Client for fetching work items and sprint data
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import base64
import json
from typing import Dict, List, Optional, Tuple
import streamlit as st
from config import AZURE_DEVOPS_CONFIG, API_ENDPOINTS


class AzureDevOpsClient:
    """Client for interacting with Azure DevOps REST API"""
    
    def __init__(self, personal_access_token: str):
        """
        Initialize the Azure DevOps client
        
        Args:
            personal_access_token: Personal Access Token for authentication
        """
        self.pat = personal_access_token
        self.config = AZURE_DEVOPS_CONFIG
        self.session = requests.Session()
        
        # Set up authentication
        auth_string = f":{self.pat}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        self.session.headers.update({
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, url: str, params: Dict = None) -> Dict:
        """
        Make authenticated request to Azure DevOps API
        
        Args:
            url: API endpoint URL
            params: Query parameters
            
        Returns:
            JSON response as dictionary
        """
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {str(e)}")
            return {}
    
    def get_iterations(self) -> List[Dict]:
        """
        Get all iterations/sprints for the team
        
        Returns:
            List of iteration dictionaries
        """
        url = API_ENDPOINTS['iterations'].format(**self.config)
        params = {'api-version': self.config['api_version']}
        
        response = self._make_request(url, params)
        return response.get('value', [])
    
    def get_current_iteration(self) -> Optional[Dict]:
        """
        Get the current active iteration
        
        Returns:
            Current iteration dictionary or None
        """
        iterations = self.get_iterations()
        from datetime import timezone
        current_date = datetime.now(timezone.utc)
        
        for iteration in iterations:
            start_date = datetime.fromisoformat(iteration['attributes']['startDate'].replace('Z', '+00:00'))
            finish_date = datetime.fromisoformat(iteration['attributes']['finishDate'].replace('Z', '+00:00'))
            
            if start_date <= current_date <= finish_date:
                return iteration
        
        return None
    
    def get_work_items_by_iteration(self, iteration_path: str, area_path: str = None) -> List[Dict]:
        """
        Get work items for a specific iteration
        
        Args:
            iteration_path: Path of the iteration
            area_path: Area path to filter work items (optional)
            
        Returns:
            List of work item dictionaries
        """
        # Build WIQL query with optional area path filter
        base_query = f"""
        SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType],
               [System.AssignedTo], [System.CreatedDate], [System.ChangedDate],
               [Microsoft.VSTS.Scheduling.StoryPoints], [Microsoft.VSTS.Common.Priority],
               [System.Tags], [System.AreaPath], [System.IterationPath]
        FROM WorkItems
        WHERE [System.IterationPath] = '{iteration_path}'
        AND [System.TeamProject] = '{self.config['project']}'"""
        
        # Add area path filter if provided
        if area_path:
            base_query += f"\nAND [System.AreaPath] UNDER '{area_path}'"
        
        wiql_query = base_query + "\nORDER BY [System.Id]"
        
        url = f"{self.config['base_url']}/{self.config['organization']}/{self.config['project']}/_apis/wit/wiql"
        params = {'api-version': self.config['api_version']}
        
        payload = {'query': wiql_query}
        
        try:
            response = self.session.post(url, json=payload, params=params)
            response.raise_for_status()
            wiql_result = response.json()
            
            work_item_ids = [item['id'] for item in wiql_result.get('workItems', [])]
            
            if not work_item_ids:
                return []
            
            return self.get_work_items_details(work_item_ids)
            
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch work items: {str(e)}")
            return []
    
    def get_work_items_details(self, work_item_ids: List[int]) -> List[Dict]:
        """
        Get detailed information for work items
        
        Args:
            work_item_ids: List of work item IDs
            
        Returns:
            List of detailed work item dictionaries
        """
        if not work_item_ids:
            return []
        
        # Split large requests into smaller batches to avoid URI length limits
        batch_size = 100  # Azure DevOps supports up to 200, but we'll use 100 for safety
        all_work_items = []
        
        for i in range(0, len(work_item_ids), batch_size):
            batch_ids = work_item_ids[i:i + batch_size]
            
            # Use POST request for batch operations to avoid URI length limits
            url = API_ENDPOINTS['work_items_batch'].format(**self.config)
            params = {'api-version': self.config['api_version']}
            
            payload = {
                'ids': batch_ids,
                '$expand': 'all'
            }
            
            try:
                response = self.session.post(url, json=payload, params=params)
                response.raise_for_status()
                batch_result = response.json()
                all_work_items.extend(batch_result.get('value', []))
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to fetch work item batch: {str(e)}")
                continue
        
        return all_work_items
    
    def get_work_items_history(self, work_item_ids: List[int]) -> Dict[int, List[Dict]]:
        """
        Get revision history for work items
        
        Args:
            work_item_ids: List of work item IDs
            
        Returns:
            Dictionary mapping work item ID to list of revisions
        """
        history = {}
        
        for work_item_id in work_item_ids:
            url = f"{self.config['base_url']}/{self.config['organization']}/{self.config['project']}/_apis/wit/workItems/{work_item_id}/revisions"
            params = {'api-version': self.config['api_version']}
            
            response = self._make_request(url, params)
            history[work_item_id] = response.get('value', [])
        
        return history
    
    def get_team_capacity(self, iteration_id: str) -> List[Dict]:
        """
        Get team capacity for an iteration
        
        Args:
            iteration_id: Iteration ID
            
        Returns:
            List of team member capacity dictionaries
        """
        url = API_ENDPOINTS['capacity'].format(
            **self.config,
            iteration_id=iteration_id
        )
        params = {'api-version': self.config['api_version']}
        
        response = self._make_request(url, params)
        return response.get('value', [])
    
    def get_burndown_data(self, iteration_path: str) -> pd.DataFrame:
        """
        Calculate burndown data for an iteration
        
        Args:
            iteration_path: Path of the iteration
            
        Returns:
            DataFrame with burndown data
        """
        work_items = self.get_work_items_by_iteration(iteration_path)
        
        if not work_items:
            return pd.DataFrame()
        
        work_item_ids = [item['id'] for item in work_items]
        history = self.get_work_items_history(work_item_ids)
        
        # Process burndown data
        burndown_data = []
        
        for work_item in work_items:
            work_item_id = work_item['id']
            revisions = history.get(work_item_id, [])
            
            for revision in revisions:
                fields = revision.get('fields', {})
                
                burndown_data.append({
                    'date': fields.get('System.ChangedDate', ''),
                    'work_item_id': work_item_id,
                    'state': fields.get('System.State', ''),
                    'story_points': fields.get('Microsoft.VSTS.Scheduling.StoryPoints', 0) or 0,
                    'work_item_type': fields.get('System.WorkItemType', ''),
                    'title': fields.get('System.Title', '')
                })
        
        df = pd.DataFrame(burndown_data)
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
        
        return df
    
    def test_connection(self) -> bool:
        """
        Test the connection to Azure DevOps
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            url = f"{self.config['base_url']}/{self.config['organization']}/_apis/projects/{self.config['project']}"
            params = {'api-version': self.config['api_version']}
            
            response = self._make_request(url, params)
            return bool(response.get('id'))
            
        except Exception:
            return False
