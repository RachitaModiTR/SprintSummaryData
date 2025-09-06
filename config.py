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

# Chart Colors - Beautiful Pastel Palette
CHART_COLORS = {
    'primary': '#A8DADC',      # Soft teal
    'secondary': '#F1FAEE',    # Cream white
    'success': '#B8E6B8',     # Soft mint green
    'warning': '#FFE5B4',     # Peach
    'danger': '#FFB3BA',      # Soft pink
    'info': '#B3D9FF',        # Light sky blue
    'light': '#F8F9FA',       # Very light gray
    'dark': '#6C757D',        # Soft gray
    'purple': '#D8BFD8',      # Thistle
    'coral': '#F5B7B1',       # Light coral
    'lavender': '#E6E6FA',    # Lavender
    'mint': '#AFEEEE',        # Pale turquoise
    'rose': '#FFE4E1',        # Misty rose
    'sage': '#C8D5B9',        # Sage green
    'champagne': '#F7E7CE'    # Champagne
}

# Pastel Color Palette for Charts
PASTEL_PALETTE = [
    '#A8DADC',  # Soft teal
    '#F1FAEE',  # Cream white
    '#B8E6B8',  # Soft mint green
    '#FFE5B4',  # Peach
    '#FFB3BA',  # Soft pink
    '#B3D9FF',  # Light sky blue
    '#D8BFD8',  # Thistle
    '#F5B7B1',  # Light coral
    '#E6E6FA',  # Lavender
    '#AFEEEE',  # Pale turquoise
    '#FFE4E1',  # Misty rose
    '#C8D5B9',  # Sage green
    '#F7E7CE',  # Champagne
    '#DDA0DD',  # Plum
    '#F0E68C'   # Khaki
]

# Work Item Types with Pastel Colors
WORK_ITEM_TYPES = {
    'User Story': {'color': '#A8DADC', 'icon': '📖'},
    'Bug': {'color': '#FFB3BA', 'icon': '🐛'},
    'Task': {'color': '#B8E6B8', 'icon': '✅'},
    'Feature': {'color': '#FFE5B4', 'icon': '🚀'},
    'Epic': {'color': '#D8BFD8', 'icon': '🎯'},
    'Test Case': {'color': '#B3D9FF', 'icon': '🧪'},
    'Issue': {'color': '#F5B7B1', 'icon': '⚠️'},
    'Requirement': {'color': '#E6E6FA', 'icon': '📋'},
    'Story': {'color': '#AFEEEE', 'icon': '📚'}
}

# Work Item States with Pastel Colors
WORK_ITEM_STATES = {
    'New': {'color': '#E6E6FA', 'category': 'proposed'},
    'Active': {'color': '#A8DADC', 'category': 'inprogress'},
    'Resolved': {'color': '#FFE5B4', 'category': 'resolved'},
    'Closed': {'color': '#B8E6B8', 'category': 'completed'},
    'Removed': {'color': '#FFB3BA', 'category': 'removed'},
    'To Do': {'color': '#F1FAEE', 'category': 'proposed'},
    'Doing': {'color': '#B3D9FF', 'category': 'inprogress'},
    'Done': {'color': '#C8D5B9', 'category': 'completed'},
    'In Progress': {'color': '#AFEEEE', 'category': 'inprogress'},
    'Committed': {'color': '#F7E7CE', 'category': 'committed'}
}

# API Endpoints
API_ENDPOINTS = {
    'work_items': '{base_url}/{organization}/{project}/_apis/wit/workitems',
    'work_items_batch': '{base_url}/{organization}/{project}/_apis/wit/workitemsbatch',
    'iterations': '{base_url}/{organization}/{project}/{team}/_apis/work/teamsettings/iterations',
    'capacity': '{base_url}/{organization}/{project}/{team}/_apis/work/teamsettings/iterations/{iteration_id}/capacities',
    'team_days_off': '{base_url}/{organization}/{project}/{team}/_apis/work/teamsettings/iterations/{iteration_id}/teamdaysoff'
}
