#!/usr/bin/env python3
"""
Bennett University LMS Downloader (Direct Authentication)
Downloads all files from LMS courses using direct HTTP authentication.
No browser automation needed - faster and more reliable.
"""

import os
import re
import sys
import time
import getpass
import urllib.parse
import argparse
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


class LMSDownloaderDirect:
    def __init__(self, username: str = None, password: str = None, output_dir: str = "lms_downloads", course_url: str = None):
        """Initialize the direct LMS downloader."""
        self.username = username
        self.password = password
        self.output_dir = output_dir
        self.course_url = course_url
        self.session = requests.Session()
        
        # Add headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.lms_base_url = "https://lms.bennett.edu.in"
        self.login_url = f"{self.lms_base_url}/login/index.php?authldap_skipntlmsso=1"
        self.dashboard_url = f"{self.lms_base_url}/my/"
        
        self.downloaded_files = []
        self.failed_files = []
        
        # File type categories
        self.file_categories = {
            'PDFs': ['.pdf'],
            'Documents': ['.doc', '.docx', '.txt', '.odt', '.rtf'],
            'Spreadsheets': ['.xls', '.xlsx', '.csv', '.ods'],
            'Presentations': ['.ppt', '.pptx', '.odp'],
            'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
            'Videos': ['.mp4', '.avi', '.mov', '.mkv', '.webm'],
            'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'],
            'Code': ['.py', '.js', '.java', '.cpp', '.c', '.html', '.css', '.sql'],
        }

    def sanitize_filename(self, filename: str) -> str:
        """Remove invalid characters from filename."""
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = filename.strip('. ')
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:190] + ext
        return filename

    def get_file_category(self, filename: str) -> str:
        """Determine file category based on extension."""
        ext = Path(filename).suffix.lower()
        for category, extensions in self.file_categories.items():
            if ext in extensions:
                return category
        return None

    def login(self) -> bool:
        """Authenticate with the LMS."""
        print("\n" + "=" * 60)
        print("AUTHENTICATING WITH LMS")
        print("=" * 60 + "\n")
        
        if not self.username or not self.password:
            print("Enter your Bennett LMS credentials:\n")
            self.username = input("Username: ").strip()
            self.password = getpass.getpass("Password: ")
        
        print(f"\nLogging in as: {self.username}")
        
        try:
            print("  Fetching login page...")
            response = self.session.get(self.login_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            csrf_token = None
            
            for input_elem in soup.find_all('input'):
                if input_elem.get('name') == 'logintoken':
                    csrf_token = input_elem.get('value')
                    break
            
            login_data = {'username': self.username, 'password': self.password}
            
            if csrf_token:
                login_data['logintoken'] = csrf_token
                print(f"  Found CSRF token")
            
            print("  Sending credentials...")
            response = self.session.post(self.login_url, data=login_data, allow_redirects=True, timeout=10)
            
            print(f"  Response status: {response.status_code}")
            print(f"  Final URL: {response.url}")
            
            print("  Verifying login...")
            time.sleep(1)
            
            dashboard_check = self.session.get(self.dashboard_url, timeout=10)
            
            if 'login' not in dashboard_check.url.lower() and dashboard_check.status_code == 200:
                print("OK Login successful!\n")
                return True
            elif response.status_code == 200 and 'login' not in response.url.lower():
                print("OK Login successful!\n")
                return True
            else:
                print("X Login failed. Invalid credentials.\n")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"X Login error: {e}\n")
            return False

    def get_course_name(self, course_url: str) -> str:
        """Extract course name from course page."""
        try:
            response = self.session.get(course_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try page title first (most reliable)
            if soup.title:
                title = soup.title.get_text(strip=True)
                # Format: "Course: CSET244: Design and Analysis of Algorithms  (Even Semester 2025-26)"
                if 'Course:' in title:
                    # Remove "Course:" prefix and semester info
                    name = title.split('Course:')[1].strip()
                    # Remove semester part in parentheses
                    if '(' in name:
                        name = name.split('(')[0].strip()
                    if name:
                        return self.sanitize_filename(name)[:100]
            
            # Fallback selectors
            for selector in ['h1.page-title', 'h1']:
                elem = soup.select_one(selector)
                if elem:
                    name = elem.get_text(strip=True)
                    if name and len(name) > 2:
                        return self.sanitize_filename(name)[:100]
            
            return "Course"
        except Exception:
            return "Course"

    def get_courses(self) -> dict:
        """Fetch all available courses from dashboard."""
        print("Fetching your courses...\n")
        try:
            response = self.session.get(self.dashboard_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            courses = {}
            
            for selector in [("div.course-info-container", "h4.media-heading a"), ("div.card", "a.card-link")]:
                containers = soup.select(selector[0])
                if containers:
                    for container in containers:
                        link = container.select_one(selector[1])
                        if link:
                            course_name = link.get_text(strip=True)
                            course_url = link.get('href', '')
                            if course_name and course_url:
                                courses[course_name] = course_url
                    if courses:
                        return courses
            
            return {}
        except:
            return {}

    def get_course_resources(self, course_url: str) -> list:
        """Fetch resources from a course."""
        try:
            response = self.session.get(course_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            resources = []
            
            for li in soup.find_all('li', class_=re.compile('activity.*resource')):
                link_elem = li.find('a')
                if link_elem and link_elem.get('href'):
                    resources.append({'name': link_elem.get_text(strip=True), 'url': link_elem['href']})
            
            return resources
        except:
            return []

    def download_file(self, file_url: str, filename: str, course_path: str) -> bool:
        """Download a single file."""
        try:
            head_response = self.session.head(file_url, allow_redirects=True, timeout=10)
            online_size = int(head_response.headers.get('Content-Length', 0))
            
            if not filename or filename.lower() == 'download':
                filename = urllib.parse.unquote(head_response.url.split('/')[-1])
            
            # Get extension from filename first
            ext = os.path.splitext(filename)[1].lower()
            if not ext:
                # Try content-type first (most reliable)
                content_type = head_response.headers.get('Content-Type', '').lower()
                ext = self._get_ext_from_content_type(content_type)
                
                # If content-type didn't help, try filename hints
                if not ext:
                    filename_lower = filename.lower()
                    if 'ppt' in filename_lower:
                        ext = '.pptx'
                    elif 'pdf' in filename_lower:
                        ext = '.pdf'
                    elif 'doc' in filename_lower or 'word' in filename_lower:
                        ext = '.docx'
                    elif 'sheet' in filename_lower or 'excel' in filename_lower:
                        ext = '.xlsx'
                    elif 'video' in filename_lower or 'mp4' in filename_lower:
                        ext = '.mp4'
                
                # Final fallback
                if not ext:
                    ext = '.bin'
                
                filename = filename + ext
            
            filename = self.sanitize_filename(filename)
            category = self.get_file_category(filename)
            
            category_path = os.path.join(course_path, category) if category else course_path
            os.makedirs(category_path, exist_ok=True)
            
            file_path = os.path.join(category_path, filename)
            
            if os.path.exists(file_path) and online_size > 0:
                if os.path.getsize(file_path) == online_size:
                    return True
            
            response = self.session.get(file_url, stream=True, timeout=30)
            total_size = int(response.headers.get('content-length', 0))
            
            with open(file_path, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename, leave=False) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            
            self.downloaded_files.append(file_path)
            return True
        except Exception as e:
            self.failed_files.append((filename, str(e)))
            return False

    def _get_ext_from_content_type(self, content_type: str) -> str:
        """Get file extension from content-type."""
        type_map = {
            'application/pdf': '.pdf',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.ms-excel': '.xls',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/vnd.ms-powerpoint': '.ppt',
            'application/vnd.ms-powerpoint.presentation.macroenabled.12': '.pptm',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
            'application/vnd.ms-powerpoint.slideshow.macroEnabled.12': '.ppsm',
            'application/zip': '.zip',
            'text/plain': '.txt',
            'video/mp4': '.mp4',
            'image/jpeg': '.jpg',
            'image/png': '.png',
        }
        content_type = content_type.lower()
        for key, ext in type_map.items():
            if key in content_type:
                return ext
        return ''

    def setup_directories(self):
        """Create output directory structure."""
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"OK Output directory: {os.path.abspath(self.output_dir)}\n")

    def download_all(self):
        """Main download routine - downloads from specific course URL only if provided."""
        print("\n" + "=" * 60)
        print("BENNETT UNIVERSITY LMS DOWNLOADER")
        print("=" * 60)
        
        self.setup_directories()
        
        if not self.login():
            print("Cannot proceed without valid login.\n")
            return
        
        if self.course_url:
            print(f"\nDOWNLOADING FROM COURSE: {self.course_url}\n")
            course_name = self.get_course_name(self.course_url)
            courses = {course_name: self.course_url}
        else:
            courses = self.get_courses()
            if not courses:
                print("No courses found.\n")
                return
        
        print("\n" + "=" * 60)
        print("DOWNLOADING FILES")
        print("=" * 60 + "\n")
        
        for course_name, course_url in courses.items():
            course_folder = self.sanitize_filename(course_name)
            course_path = os.path.join(self.output_dir, course_folder)
            os.makedirs(course_path, exist_ok=True)
            
            print(f"\nCourse: {course_name}")
            print("-" * 60)
            
            resources = self.get_course_resources(course_url)
            
            if not resources:
                print("  No resources found.\n")
                continue
            
            print(f"  Found {len(resources)} resource(s)\n")
            
            for resource in resources:
                self.download_file(resource['url'], resource['name'], course_path)
            
            time.sleep(1)
        
        self.print_summary()

    def print_summary(self):
        """Print download summary."""
        print("\n" + "=" * 60)
        print("DOWNLOAD SUMMARY")
        print("=" * 60)
        print(f"OK Downloaded: {len(self.downloaded_files)} files")
        print(f"X Failed: {len(self.failed_files)} files")
        print(f"Location: {os.path.abspath(self.output_dir)}\n")


def main():
    parser = argparse.ArgumentParser(description='Download files from Bennett University LMS')
    parser.add_argument('course_url', nargs='?', default=None, help='Course URL (optional)')
    parser.add_argument('-u', '--username', help='LMS username')
    parser.add_argument('-p', '--password', help='LMS password')
    parser.add_argument('-o', '--output', default='lms_downloads', help='Output directory')
    args = parser.parse_args()
    
    try:
        # Ask for course URL if not provided
        course_url = args.course_url
        if not course_url:
            print("\n" + "=" * 60)
            print("BENNETT UNIVERSITY LMS DOWNLOADER")
            print("=" * 60 + "\n")
            print("Enter course link (or press Enter to download from ALL courses):")
            user_input = input("Course URL: ").strip()
            if user_input:
                course_url = user_input
        
        downloader = LMSDownloaderDirect(args.username, args.password, args.output, course_url)
        downloader.download_all()
    except KeyboardInterrupt:
        print("\n\nX Download interrupted")
    except Exception as e:
        print(f"\nX Fatal error: {e}")


if __name__ == "__main__":
    main()
