# Quick Start Guide - Azure DevOps Sprint Dashboard

## 🚀 Getting Started in 5 Minutes

### Step 1: Install Dependencies

**For Python 3.13 users (recommended approach):**
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with pre-compiled wheels
pip install --upgrade pip
pip install streamlit requests plotly python-dateutil azure-devops numpy
pip install pandas --no-build-isolation
```

**For Python 3.8-3.12 users:**
```bash
pip install -r requirements.txt
```

### Step 2: Get Your Personal Access Token
1. Go to https://dev.azure.com/tr-tax
2. Click your profile picture → Personal Access Tokens
3. Create new token with "Work Items (Read)" permission
4. Copy the token (save it securely!)

### Step 3: Run the Dashboard
```bash
streamlit run app.py
```

### Step 4: Configure Authentication
1. Dashboard opens in your browser automatically
2. Enter your Personal Access Token in the sidebar
3. Click "Test Connection"
4. Dashboard loads your sprint data automatically!

## 📊 What You'll See

### Sprint Overview
- **Total Items**: 25 work items
- **Story Points**: 45/60 (75% complete)
- **Completed**: 18 items (72% complete)
- **In Progress**: 5 items

### Interactive Charts
- **Burndown Chart**: Track daily progress vs ideal
- **Work Item Types**: Visual breakdown of Stories, Bugs, Tasks
- **Team Workload**: Individual performance metrics
- **Cycle Time**: Process efficiency analysis

### Key Features
- ✅ Real-time data from Azure DevOps
- 📈 Interactive Plotly visualizations
- 👥 Team performance insights
- 🔍 Blocked items identification
- 📥 CSV data export

## 🔧 Troubleshooting

### "Connection Failed"
- Check your Personal Access Token
- Verify token has "Work Items (Read)" permission
- Ensure you're connected to the internet

### "No Sprint Data"
- Confirm there's an active sprint
- Check work items are in the current iteration
- Verify team configuration in config.py

### "Import Errors"
- Run: `pip install -r requirements.txt`
- Use Python 3.7+ 
- Check all dependencies installed successfully

## 📋 Pre-configured Settings

Your dashboard is ready for:
- **Organization**: tr-tax
- **Project**: TaxProf  
- **Team**: ADGE-Prep
- **Board**: https://dev.azure.com/tr-tax/TaxProf/_boards/board/t/ADGE-Prep/Stories

## 🎯 Next Steps

1. **Explore the Dashboard**: Navigate through all sections
2. **Export Data**: Use the CSV download feature
3. **Customize**: Modify config.py for your needs
4. **Share**: Send the dashboard URL to your team

## 💡 Pro Tips

- **Refresh Data**: Restart the app to get latest updates
- **Filter Views**: Use browser bookmarks for specific sections
- **Team Meetings**: Perfect for sprint reviews and retrospectives
- **Historical Analysis**: Export data regularly for trend analysis

---

**Need Help?** Check the full README.md for detailed documentation.
