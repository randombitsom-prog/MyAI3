# LinkedIn BITSoM Alumni Scraper

⚠️ **IMPORTANT**: LinkedIn's Terms of Service prohibit automated scraping. Use these scripts responsibly and at your own risk.

## Options

### Option 1: Automated Scraping (⚠️ Violates ToS)

**File**: `linkedin_bitcom_alumni.py`

**Requirements**:
```bash
pip install selenium beautifulsoup4 pandas
# Also need ChromeDriver: https://chromedriver.chromium.org/
```

**Usage**:
```bash
# Set credentials as environment variables
export LINKEDIN_EMAIL="your-email@example.com"
export LINKEDIN_PASSWORD="your-password"

# Or provide when prompted
python scripts/linkedin_bitcom_alumni.py
```

**Risks**:
- May violate LinkedIn's Terms of Service
- Account could be banned
- Rate limiting and CAPTCHAs
- Legal issues

### Option 2: Manual Collection (✅ Recommended)

**File**: `linkedin_alumni_alternative.py`

**Usage**:
```bash
# Step 1: Create template
python scripts/linkedin_alumni_alternative.py create-template

# Step 2: Manually edit data/linkedin_alumni_manual.json
# Add alumni data you collect from LinkedIn

# Step 3: Process the data
python scripts/linkedin_alumni_alternative.py
```

**How to collect data manually**:
1. Go to LinkedIn
2. Search: "BITSoM MBA" or "BITSoM" in education
3. For each profile:
   - Copy name
   - Copy profile URL
   - Copy all companies from Experience section
4. Add to the JSON file

### Option 3: LinkedIn Official API (✅ Best, but Limited)

LinkedIn offers APIs but they're restricted:
- **LinkedIn Learning API**: For course data only
- **LinkedIn Marketing API**: For ads, not profiles
- **LinkedIn Sales Navigator API**: Paid, requires Sales Navigator subscription

**No public API for profile search exists.**

### Option 4: Third-Party Services (✅ Legal, but Paid)

**Services with LinkedIn data**:
- **Apollo.io**: Has LinkedIn integration, paid API
- **ZoomInfo**: B2B database with LinkedIn data
- **Lusha**: Contact data with LinkedIn integration
- **Hunter.io**: Email finder with LinkedIn data

These services have APIs and are legal to use.

## Recommended Approach

For your capstone project, I recommend:

1. **Manual collection** (Option 2) for a small sample (20-50 alumni)
2. **Use the data** to show proof of concept
3. **Document** that you used manual collection to comply with ToS
4. **Mention** in your documentation that for production, you'd use:
   - LinkedIn Sales Navigator API (if budget allows)
   - Third-party services like Apollo.io
   - Or partner with BITSoM alumni office for official data

## Output

Both scripts generate:
- `data/bitcom_linkedin_alumni.json`: Full alumni data with companies
- `data/bitcom_companies.csv`: List of all unique companies

## Legal Disclaimer

⚠️ **This script is for educational purposes only.**
- LinkedIn's ToS prohibits automated scraping
- Use at your own risk
- The author is not responsible for any account bans or legal issues
- For production use, consider official APIs or third-party services

