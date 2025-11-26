#!/usr/bin/env python3
"""
Script to search LinkedIn for BITSoM MBA alumni and extract their work history.
⚠️  WARNING: LinkedIn's Terms of Service prohibit automated scraping.
This script is for educational purposes only. Use at your own risk.

Requirements:
- pip install selenium beautifulsoup4 pandas
- Chrome/Chromium browser
- ChromeDriver installed and in PATH
"""

import os
import sys
import time
import json
import csv
from typing import List, Dict, Optional
from datetime import datetime

# Check and import required packages
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from bs4 import BeautifulSoup
    import pandas as pd
    # Try to use webdriver-manager for automatic ChromeDriver management
    try:
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        USE_WEBDRIVER_MANAGER = True
    except ImportError:
        USE_WEBDRIVER_MANAGER = False
        print("💡 Tip: Install webdriver-manager for automatic ChromeDriver setup:")
        print("   pip install webdriver-manager")
except ImportError as e:
    print("❌ Missing required packages. Install with:")
    print("   pip install selenium beautifulsoup4 pandas webdriver-manager")
    print(f"\n   Error: {e}")
    sys.exit(1)


class LinkedInScraper:
    def __init__(self, email: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize LinkedIn scraper.
        
        Args:
            email: LinkedIn email (optional, will prompt if not provided)
            password: LinkedIn password (optional, will prompt if not provided)
        """
        self.email = email or os.getenv("LINKEDIN_EMAIL")
        self.password = password or os.getenv("LINKEDIN_PASSWORD")
        self.driver = None
        self.alumni_data = []
        
    def setup_driver(self):
        """Setup Chrome WebDriver."""
        options = webdriver.ChromeOptions()
        
        # Headless mode is DISABLED to allow manual 2FA entry
        # Uncomment the line below if you need headless mode:
        # options.add_argument('--headless=new')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Add user agent to avoid detection
        options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Window size for better visibility
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        
        try:
            # Try using webdriver-manager first (auto-downloads correct ChromeDriver)
            if USE_WEBDRIVER_MANAGER:
                from selenium.webdriver.chrome.service import Service
                from webdriver_manager.chrome import ChromeDriverManager
                print("🔧 Using webdriver-manager to setup ChromeDriver...")
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                # Fallback to system ChromeDriver
                self.driver = webdriver.Chrome(options=options)
            
            self.driver.maximize_window()
            print("✅ Chrome driver initialized")
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error initializing Chrome driver: {error_msg}")
            
            if "session not created" in error_msg.lower() or "chrome instance exited" in error_msg.lower():
                print("\n💡 Common fixes:")
                print("   1. Install webdriver-manager (recommended):")
                print("      pip install webdriver-manager")
                print("\n   2. Or manually install ChromeDriver:")
                print("      - Check your Chrome version: chrome://version/")
                print("      - Download matching ChromeDriver from:")
                print("        https://chromedriver.chromium.org/")
                print("      - Or on macOS: brew install chromedriver")
                print("\n   3. If running in headless/server environment:")
                print("      - Make sure Chrome/Chromium is installed")
                print("      - Try uncommenting --headless option")
                print("\n   4. Check ChromeDriver is in PATH:")
                print("      which chromedriver")
            
            raise
    
    def login(self):
        """Login to LinkedIn with 2FA support."""
        if not self.email or not self.password:
            print("⚠️  LinkedIn credentials not provided")
            print("   Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables")
            print("   Or provide them when initializing the scraper")
            return False
        
        try:
            print("🔐 Logging into LinkedIn...")
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(2)
            
            # Enter email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.send_keys(self.email)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(self.password)
            
            # Click login
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait a bit for page to load
            time.sleep(3)
            
            # Check for 2FA challenge
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            
            # Check if we're on a 2FA/challenge page
            is_2fa_page = (
                "challenge" in current_url.lower() or
                "two-step" in page_source or
                "verification" in page_source or
                "security" in current_url.lower() or
                "enter the code" in page_source or
                "verify your identity" in page_source
            )
            
            if is_2fa_page:
                print("\n🔐 2FA/Verification detected!")
                print("   Please complete the verification in the browser window.")
                print("   This may include:")
                print("   - Entering a 2FA code from your authenticator app")
                print("   - Completing a CAPTCHA")
                print("   - Verifying your identity")
                print("\n   Waiting for you to complete verification...")
                print("   (The script will continue once you're logged in)")
                
                # Wait for user to complete 2FA (check every 2 seconds for up to 5 minutes)
                max_wait_time = 300  # 5 minutes
                check_interval = 2
                waited = 0
                
                while waited < max_wait_time:
                    time.sleep(check_interval)
                    waited += check_interval
                    
                    current_url = self.driver.current_url
                    # Check if we've successfully logged in
                    if "feed" in current_url or "mynetwork" in current_url or "linkedin.com/in/" in current_url:
                        print("✅ Successfully logged in after verification!")
                        return True
                    
                    # Still on challenge page, continue waiting
                    if "challenge" not in current_url.lower() and "security" not in current_url.lower():
                        # Might have moved to a different page, check again
                        time.sleep(2)
                        current_url = self.driver.current_url
                        if "feed" in current_url or "mynetwork" in current_url:
                            print("✅ Successfully logged in!")
                            return True
                    
                    # Show progress every 30 seconds
                    if waited % 30 == 0:
                        remaining = (max_wait_time - waited) // 60
                        print(f"   Still waiting... ({remaining} minutes remaining)")
                
                print("⏱️  Timeout waiting for verification. Please try again.")
                return False
            
            # Check if login was successful (no 2FA needed)
            time.sleep(2)
            current_url = self.driver.current_url
            if "feed" in current_url or "mynetwork" in current_url:
                print("✅ Successfully logged in")
                return True
            else:
                print("⚠️  Login status unclear - please check the browser window")
                print("   If you see a CAPTCHA or 2FA prompt, complete it manually")
                print("   The script will detect when you're logged in")
                
                # Give user a chance to complete any manual steps
                print("\n   Waiting 30 seconds for manual completion...")
                time.sleep(30)
                
                current_url = self.driver.current_url
                if "feed" in current_url or "mynetwork" in current_url:
                    print("✅ Successfully logged in!")
                    return True
                else:
                    print("⚠️  Still not logged in. Please check the browser and try again.")
                    return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            print("   Please check the browser window for any prompts or errors")
            return False
    
    def search_alumni(self, max_results: int = 50) -> List[str]:
        """
        Search for BITSoM MBA alumni on LinkedIn.
        
        Args:
            max_results: Maximum number of profiles to collect
            
        Returns:
            List of profile URLs
        """
        print(f"🔍 Searching for BITSoM MBA alumni (max {max_results} results)...")
        
        # LinkedIn search URL for BITSoM MBA
        search_url = "https://www.linkedin.com/search/results/people/?keywords=BITSoM%20MBA&origin=GLOBAL_SEARCH_HEADER"
        
        try:
            self.driver.get(search_url)
            time.sleep(3)
            
            profile_urls = []
            scroll_pause = 2
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while len(profile_urls) < max_results:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_pause)
                
                # Get all profile links
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link.get('href', '')
                    if '/in/' in href and href not in profile_urls:
                        full_url = href if href.startswith('http') else f"https://www.linkedin.com{href}"
                        profile_urls.append(full_url)
                        if len(profile_urls) >= max_results:
                            break
                
                # Check if we've reached the bottom
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                
                print(f"   Found {len(profile_urls)} profiles so far...")
            
            print(f"✅ Found {len(profile_urls)} profile URLs")
            return profile_urls[:max_results]
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def extract_profile_data(self, profile_url: str) -> Optional[Dict]:
        """
        Extract data from a LinkedIn profile.
        
        Args:
            profile_url: LinkedIn profile URL
            
        Returns:
            Dictionary with profile data or None if failed
        """
        try:
            # Navigate to profile with error handling
            try:
                self.driver.get(profile_url)
                time.sleep(3)  # Be respectful with delays
            except Exception as nav_error:
                print(f"   ⚠️  Error navigating to {profile_url}: {nav_error}")
                return None
            
            # Parse page with error handling
            try:
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            except Exception as parse_error:
                print(f"   ⚠️  Error parsing page for {profile_url}: {parse_error}")
                return None
            
            # Extract name - try multiple selectors with error handling
            name = "Unknown"
            try:
                name_selectors = [
                    ('h1', {'class': 'text-heading-xlarge'}),
                    ('h1', {'class': 'top-card-layout__title'}),
                    ('h1', {'class': 'pv-text-details__left-panel'}),
                    ('h1', {}),
                ]
                for tag, attrs in name_selectors:
                    try:
                        name_elem = soup.find(tag, attrs)
                        if name_elem:
                            name = name_elem.get_text(strip=True)
                            if name and name != "Unknown":
                                break
                    except Exception:
                        continue  # Try next selector
            except Exception as name_error:
                print(f"   ⚠️  Error extracting name: {name_error}")
                # Continue with "Unknown" name
            
            # Extract companies from experience section with error handling
            companies = []
            
            try:
                # Method 1: Look for experience section
                experience_section = soup.find('section', {'id': 'experience'})
                if experience_section:
                    try:
                        # Try to find company names in various structures
                        company_links = experience_section.find_all('a', href=lambda x: x and '/company/' in x)
                        for link in company_links:
                            try:
                                company_name = link.get_text(strip=True)
                                if company_name and company_name not in companies:
                                    companies.append(company_name)
                            except Exception:
                                continue  # Skip this link if error
                        
                        # Also try span elements with company names
                        spans = experience_section.find_all('span', class_=lambda x: x and ('t-14' in x or 't-16' in x))
                        for span in spans:
                            try:
                                text = span.get_text(strip=True)
                                # Filter out common non-company text
                                if text and len(text) > 2 and len(text) < 100:
                                    # Check if it looks like a company name (not dates, locations, etc.)
                                    if not any(word in text.lower() for word in ['present', 'full-time', 'part-time', 'intern', 'month', 'year', 'jan', 'feb', 'mar']):
                                        if text not in companies:
                                            companies.append(text)
                            except Exception:
                                continue  # Skip this span if error
                    except Exception as exp_error:
                        print(f"   ⚠️  Error parsing experience section: {exp_error}")
                        # Continue to other methods
                
                # Method 2: Look for experience items in the page
                if not companies:
                    try:
                        # Try finding experience items by class
                        exp_items = soup.find_all('div', class_=lambda x: x and ('pvs-list' in str(x) or 'experience' in str(x).lower()))
                        for item in exp_items:
                            try:
                                # Look for links that might be companies
                                links = item.find_all('a', href=lambda x: x and '/company/' in x)
                                for link in links:
                                    try:
                                        company_name = link.get_text(strip=True)
                                        if company_name and company_name not in companies:
                                            companies.append(company_name)
                                    except Exception:
                                        continue  # Skip this link
                            except Exception:
                                continue  # Skip this item
                    except Exception as exp2_error:
                        print(f"   ⚠️  Error in method 2: {exp2_error}")
                        # Continue to method 3
                
                # Method 3: Search for company links anywhere on the page
                if not companies:
                    try:
                        all_company_links = soup.find_all('a', href=lambda x: x and '/company/' in x)
                        for link in all_company_links:
                            try:
                                company_name = link.get_text(strip=True)
                                if company_name and company_name not in companies and len(company_name) < 100:
                                    companies.append(company_name)
                            except Exception:
                                continue  # Skip this link
                    except Exception as exp3_error:
                        print(f"   ⚠️  Error in method 3: {exp3_error}")
                        # Continue anyway, return empty companies list
                        
            except Exception as company_error:
                print(f"   ⚠️  Error extracting companies: {company_error}")
                # Continue with empty companies list
            
            # Clean and format the data
            try:
                return {
                    'Name': name,
                    'LinkedIn URL': profile_url,
                    'Past Companies': list(set(companies)) if companies else []
                }
            except Exception as format_error:
                print(f"   ⚠️  Error formatting data for {profile_url}: {format_error}")
                # Return minimal data if formatting fails
                return {
                    'Name': name if name else "Unknown",
                    'LinkedIn URL': profile_url,
                    'Past Companies': []
                }
            
        except TimeoutException as e:
            print(f"   ⚠️  Timeout loading {profile_url}: {e}")
            return None
        except NoSuchElementException as e:
            print(f"   ⚠️  Element not found on {profile_url}: {e}")
            # Still try to return what we can
            return {
                'Name': "Unknown",
                'LinkedIn URL': profile_url,
                'Past Companies': []
            }
        except Exception as e:
            print(f"   ⚠️  Error extracting {profile_url}: {e}")
            print(f"      Error type: {type(e).__name__}")
            return None
    
    def scrape_alumni(self, max_profiles: int = 20, delay: int = 5):
        """
        Scrape alumni profiles and extract company information.
        
        Args:
            max_profiles: Maximum number of profiles to scrape
            delay: Delay between requests (seconds)
        """
        print(f"\n{'='*60}")
        print("BITSoM LinkedIn Alumni Scraper")
        print(f"{'='*60}\n")
        
        try:
            # Setup and login
            self.setup_driver()
            if not self.login():
                print("❌ Cannot proceed without login")
                return
            
            # Search for alumni
            profile_urls = self.search_alumni(max_results=max_profiles)
            
            if not profile_urls:
                print("❌ No profiles found")
                return
            
            # Extract data from each profile
            print(f"\n📊 Extracting data from {len(profile_urls)} profiles...")
            failed_count = 0
            for i, url in enumerate(profile_urls, 1):
                try:
                    print(f"  [{i}/{len(profile_urls)}] Processing: {url}")
                    
                    # Wrap extract_profile_data in try-except to catch any errors
                    try:
                        data = self.extract_profile_data(url)
                        if data:
                            self.alumni_data.append(data)
                            print(f"      ✅ Extracted: {data.get('Name', 'Unknown')} - {len(data.get('Past Companies', []))} companies")
                        else:
                            print(f"      ⚠️  Failed to extract data (returned None)")
                            failed_count += 1
                    except Exception as extract_error:
                        # Catch errors from extract_profile_data itself
                        print(f"      ❌ Error in extract_profile_data: {extract_error}")
                        print(f"      Error type: {type(extract_error).__name__}")
                        failed_count += 1
                        # Continue to next profile
                    
                    # Save progress every 10 profiles
                    if i % 10 == 0 and self.alumni_data:
                        print(f"\n   💾 Auto-saving progress ({len(self.alumni_data)} profiles so far, {failed_count} failed)...")
                        try:
                            self.save_progress(is_error=False)
                        except Exception as save_error:
                            print(f"      ⚠️  Error saving progress: {save_error}")
                            # Continue anyway, don't stop the scraping
                    
                    time.sleep(delay)  # Be respectful with rate limiting
                    
                except KeyboardInterrupt:
                    print("\n\n⚠️  Interrupted by user (Ctrl+C)")
                    raise
                except Exception as e:
                    # Catch any other unexpected errors
                    print(f"      ❌ Unexpected error processing {url}: {e}")
                    print(f"      Error type: {type(e).__name__}")
                    import traceback
                    print(f"      Traceback:")
                    traceback.print_exc()
                    print(f"      Continuing with next profile...")
                    failed_count += 1
                    # Continue to next profile instead of stopping
                    continue
            
            print(f"\n✅ Scraped {len(self.alumni_data)} profiles successfully")
            if failed_count > 0:
                print(f"⚠️  {failed_count} profiles failed to process (skipped)")
            
            print(f"\n✅ Scraped {len(self.alumni_data)} profiles successfully")
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Script interrupted by user")
            if self.alumni_data:
                print(f"\n💾 Saving progress before exit...")
                saved_path = self.save_progress(is_error=True)
                print(f"✅ Progress saved to: {saved_path}")
                print(f"   Total profiles collected: {len(self.alumni_data)}")
            raise
            
        except Exception as e:
            print(f"\n\n❌ Fatal error occurred: {e}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            print(f"\n   Traceback:")
            traceback.print_exc()
            
            if self.alumni_data:
                print(f"\n💾 Saving progress before exit...")
                saved_path = self.save_progress(is_error=True)
                print(f"✅ Progress saved to: {saved_path}")
                print(f"   Total profiles collected: {len(self.alumni_data)}")
                print(f"   You can resume later or use this partial data")
            else:
                print("⚠️  No data to save")
            
            raise
        
    def get_all_companies(self) -> List[str]:
        """Get a list of all unique companies."""
        all_companies = set()
        for alumni in self.alumni_data:
            all_companies.update(alumni.get('Past Companies', []))
        return sorted(list(all_companies))
    
    def save_progress(self, output_file: str = "bitcom_linkedin_alumni.json", is_error: bool = False):
        """
        Save current progress to JSON file.
        
        Args:
            output_file: Output filename
            is_error: If True, adds '_progress' suffix to filename
        """
        output_path = f"data/{output_file}"
        if is_error:
            # Add timestamp to progress file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = output_file.replace('.json', '')
            output_path = f"data/{base_name}_progress_{timestamp}.json"
        
        os.makedirs("data", exist_ok=True)
        
        # Format data as requested: Name, LinkedIn URL, Past Companies
        formatted_data = []
        for alumni in self.alumni_data:
            formatted_data.append({
                'Name': alumni.get('Name', 'Unknown'),
                'LinkedIn URL': alumni.get('LinkedIn URL', ''),
                'Past Companies': alumni.get('Past Companies', [])
            })
        
        output_json = {
            'scraped_at': datetime.now().isoformat(),
            'total_profiles': len(self.alumni_data),
            'alumni': formatted_data,
            'all_companies': self.get_all_companies(),
            'companies_count': len(self.get_all_companies())
        }
        
        if is_error:
            output_json['status'] = 'partial_save_due_to_error'
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_json, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Progress saved to {output_path}")
        return output_path
    
    def save_results(self, output_file: str = "bitcom_linkedin_alumni.json"):
        """Save final results to JSON file."""
        return self.save_progress(output_file, is_error=False)
    
    def save_companies_csv(self, output_file: str = "bitcom_companies.csv"):
        """Save companies list to CSV."""
        output_path = f"data/{output_file}"
        os.makedirs("data", exist_ok=True)
        
        companies = self.get_all_companies()
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Company Name'])
            for company in companies:
                writer.writerow([company])
        
        print(f"💾 Companies list saved to {output_file}")
    
    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
            print("✅ Browser closed")


def main():
    """Main function."""
    # Verify required modules are available
    try:
        from selenium import webdriver
    except ImportError:
        print("❌ Selenium webdriver is not available.")
        print("   Please install required packages:")
        print("   pip install selenium beautifulsoup4 pandas webdriver-manager")
        print("\n   webdriver-manager will automatically handle ChromeDriver installation.")
        print("   Or manually install ChromeDriver:")
        print("   - macOS: brew install chromedriver")
        print("   - Or download from: https://chromedriver.chromium.org/")
        sys.exit(1)
    
    # Check if webdriver-manager is available
    if not USE_WEBDRIVER_MANAGER:
        print("💡 Tip: Install webdriver-manager for automatic ChromeDriver setup:")
        print("   pip install webdriver-manager\n")
    
    print("⚠️  WARNING: LinkedIn scraping may violate Terms of Service.")
    print("   Use this script responsibly and at your own risk.\n")
    
    # Get credentials
    email = input("LinkedIn Email (or press Enter to use LINKEDIN_EMAIL env var): ").strip()
    password = input("LinkedIn Password (or press Enter to use LINKEDIN_PASSWORD env var): ").strip()
    
    if not email:
        email = None
    if not password:
        password = None
    
    scraper = LinkedInScraper(email=email, password=password)
    
    try:
        # Scrape alumni (adjust max_profiles and delay as needed)
        scraper.scrape_alumni(max_profiles=350, delay=5)
        
        # Save results
        if scraper.alumni_data:
            scraper.save_results()
            scraper.save_companies_csv()
            
            # Print summary
            print(f"\n{'='*60}")
            print("Summary")
            print(f"{'='*60}")
            print(f"Total profiles scraped: {len(scraper.alumni_data)}")
            print(f"Total unique companies: {len(scraper.get_all_companies())}")
            print(f"\nCompanies found:")
            for company in scraper.get_all_companies()[:20]:  # Show first 20
                print(f"  - {company}")
            if len(scraper.get_all_companies()) > 20:
                print(f"  ... and {len(scraper.get_all_companies()) - 20} more")
        else:
            print("❌ No data collected")
            
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        # Progress should already be saved by scrape_alumni, but save again just in case
        if scraper.alumni_data:
            print("💾 Saving final progress...")
            scraper.save_progress(is_error=True)
    except Exception as e:
        print(f"\n❌ Fatal error in main: {e}")
        import traceback
        traceback.print_exc()
        # Save progress if we have any data
        if scraper.alumni_data:
            print("💾 Saving progress before exit...")
            scraper.save_progress(is_error=True)
    finally:
        # Always close the browser
        try:
            scraper.close()
        except:
            pass  # Ignore errors when closing


if __name__ == "__main__":
    main()

