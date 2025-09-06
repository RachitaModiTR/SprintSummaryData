"""
Configuration file for Azure DevOps Sprint Dashboard
"""

# Azure DevOps Configuration
AZURE_DEVOPS_CONFIG = {
    'organization': 'tr-tax',
    'project': 'TaxProf',
    'team': 'ADGE-Prep',
    'base_url': 'https://dev.azure.com',
    'api_version': '7.0'
}

# Dashboard Configuration
DASHBOARD_CONFIG = {
    'page_title': 'Azure DevOps Sprint Dashboard',
    'page_icon': '📊',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded'
}

# Chart Colors
CHART_COLORS = {
    'primary': '#0078d4',
    'secondary': '#106ebe',
    'success': '#107c10',
    'warning': '#ff8c00',
    'danger': '#d13438',
    'info': '#00bcf2',
    'light': '#f3f2f1',
    'dark': '#323130'
}

# Work Item Types
WORK_ITEM_TYPES = {
    'User Story': {'color': '#0078d4', 'icon': '📖'},
    'Bug': {'color': '#d13438', 'icon': '🐛'},
    'Task': {'color': '#107c10', 'icon': '✅'},
    'Feature': {'color': '#ff8c00', 'icon': '🚀'},
    'Epic': {'color': '#5c2d91', 'icon': '🎯'},
    'Test Case': {'color': '#00bcf2', 'icon': '🧪'}
}

# Work Item States
WORK_ITEM_STATES = {
    'New': {'color': '#605e5c', 'category': 'proposed'},
    'Active': {'color': '#0078d4', 'category': 'inprogress'},
    'Resolved': {'color': '#ff8c00', 'category': 'resolved'},
    'Closed': {'color': '#107c10', 'category': 'completed'},
    'Removed': {'color': '#a4262c', 'category': 'removed'},
    'To Do': {'color': '#605e5c', 'category': 'proposed'},
    'Doing': {'color': '#0078d4', 'category': 'inprogress'},
    'Done': {'color': '#107c10', 'category': 'completed'}
}

# API Endpoints
API_ENDPOINTS = {
    'work_items': '{base_url}/{organization}/{project}/_apis/wit/workitems',
    'work_items_batch': '{base_url}/{organization}/{project}/_apis/wit/workitemsbatch',
    'iterations': '{base_url}/{organization}/{project}/{team}/_apis/work/teamsettings/iterations',
    'capacity': '{base_url}/{organization}/{project}/{team}/_apis/work/teamsettings/iterations/{iteration_id}/capacities',
    'team_days_off': '{base_url}/{organization}/{project}/{team}/_apis/work/teamsettings/iterations/{iteration_id}/teamdaysoff'
}
