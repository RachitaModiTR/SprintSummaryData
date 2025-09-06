# Azure DevOps Sprint Dashboard

A comprehensive Streamlit dashboard for analyzing Azure DevOps sprint data with interactive visualizations and detailed insights.

## Features

### 📊 Sprint Overview
- Real-time sprint metrics and KPIs
- Story points tracking and completion rates
- Sprint duration and velocity analysis
- Current sprint status with key indicators

### 🔥 Burndown Analysis
- Interactive burndown chart with ideal vs actual progress
- Daily progress tracking
- Velocity metrics and completion forecasting
- Sprint goal achievement analysis

### 📋 Work Item Analysis
- Work item type distribution (User Stories, Bugs, Tasks, etc.)
- State-based analysis (New, Active, Done, etc.)
- Priority distribution and risk assessment
- Comprehensive work item breakdown

### 👥 Team Analysis
- Individual team member workload distribution
- Completion rates by assignee
- Story points allocation and progress
- Team performance metrics

### 📊 Quality & Process Metrics
- Cycle time analysis by work item type
- Blocked items identification
- Process efficiency metrics
- Quality indicators and trends

### 🔍 Data Export
- Raw data access and exploration
- CSV export functionality
- Detailed work item information
- Historical data preservation

## Installation

1. **Clone or download the project files**
2. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The dashboard is pre-configured for your Azure DevOps environment:

- **Organization:** tr-tax
- **Project:** TaxProf
- **Team:** ADGE-Prep
- **Board URL:** https://dev.azure.com/tr-tax/TaxProf/_boards/board/t/ADGE-Prep/Stories

## Usage

### 1. Get Azure DevOps Personal Access Token

1. Go to your Azure DevOps organization
2. Click on your profile picture (top right)
3. Select "Personal Access Tokens"
4. Click "New Token"
5. Configure the token:
   - **Name:** Sprint Dashboard Token
   - **Expiration:** Choose appropriate duration
   - **Scopes:** Select "Work Items (Read)" at minimum
6. Copy the generated token (save it securely!)

### 2. Run the Dashboard

```bash
streamlit run app.py
```

### 3. Configure Authentication

1. Open the dashboard in your browser
2. Enter your Personal Access Token in the sidebar
3. Click "Test Connection" to verify access
4. The dashboard will automatically load current sprint data

## Dashboard Sections

### Sprint Overview
- **Total Items:** Complete count of work items in sprint
- **Story Points:** Progress tracking with completion percentage
- **Completed Items:** Number and percentage of finished work
- **In Progress:** Currently active work items

### Burndown Chart
- **Ideal Line:** Expected progress trajectory
- **Actual Line:** Real progress with daily updates
- **Velocity Tracking:** Story points completion rate
- **Trend Analysis:** Sprint goal achievement forecast

### Work Item Breakdown
- **Type Distribution:** Visual breakdown by work item types
- **State Analysis:** Current status of all items
- **Priority Matrix:** Risk and importance assessment
- **Assignment Overview:** Team workload distribution

### Team Performance
- **Individual Metrics:** Per-person completion rates
- **Workload Balance:** Story points distribution
- **Productivity Analysis:** Team velocity insights
- **Collaboration Patterns:** Cross-team dependencies

### Quality Metrics
- **Cycle Time:** Average time from creation to completion
- **Blocked Items:** Identification of stalled work
- **Process Efficiency:** Flow and bottleneck analysis
- **Trend Monitoring:** Historical performance comparison

## File Structure

```
├── app.py                    # Main Streamlit application
├── azure_devops_client.py    # Azure DevOps API client
├── data_analyzer.py          # Data analysis and metrics calculation
├── visualizations.py         # Chart and visualization components
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
└── README.md                # This documentation
```

## API Permissions Required

Your Personal Access Token needs the following scopes:
- **Work Items:** Read
- **Project and Team:** Read
- **Analytics:** Read (optional, for advanced metrics)

## Troubleshooting

### Connection Issues
- Verify your Personal Access Token is valid and not expired
- Ensure the token has appropriate permissions
- Check that your organization, project, and team names are correct

### No Data Displayed
- Confirm there's an active sprint with work items
- Verify work items are assigned to the correct iteration path
- Check that work items have the required fields (story points, states)

### Performance Issues
- Large sprints (>100 items) may take longer to load
- Consider filtering by specific work item types if needed
- Refresh the page if data appears stale

## Customization

### Modifying Team Configuration
Edit `config.py` to change:
- Organization name
- Project name  
- Team name
- API endpoints
- Chart colors and styling

### Adding New Metrics
Extend `data_analyzer.py` to include:
- Custom KPIs
- Additional work item fields
- Team-specific calculations
- Historical trend analysis

### Custom Visualizations
Modify `visualizations.py` to add:
- New chart types
- Custom styling
- Interactive features
- Export options

## Security Notes

- Never commit Personal Access Tokens to version control
- Use environment variables for production deployments
- Regularly rotate access tokens
- Limit token permissions to minimum required scope

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your Azure DevOps permissions
3. Review the console output for error messages
4. Ensure all dependencies are properly installed

## Version History

- **v1.0.0** - Initial release with core dashboard functionality
- Comprehensive sprint analysis and visualization
- Team performance metrics and quality indicators
- Interactive charts and data export capabilities

---

*Last updated: December 2024*
