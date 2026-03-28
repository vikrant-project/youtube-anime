#!/usr/bin/env python3
"""
GitHub Auto-Upload Script
Automatically pushes code to private GitHub repository
"""

import os
import subprocess
import logging
from pathlib import Path
from dotenv import load_dotenv
from git import Repo, GitCommandError

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class GitHubUploader:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_username = os.getenv('GITHUB_USERNAME')
        self.github_repo = os.getenv('GITHUB_REPO')
        self.repo_path = Path('/app/new')
        
        if not all([self.github_token, self.github_username, self.github_repo]):
            log.error("Missing GitHub credentials in .env file")
            return
        
        self.repo_url = f"https://{self.github_token}@github.com/{self.github_username}/{self.github_repo}.git"
    
    def create_private_repo(self) -> bool:
        """
        Create private GitHub repository using GitHub API
        """
        try:
            import requests
            
            log.info(f"Creating private repo: {self.github_repo}")
            
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            data = {
                'name': self.github_repo,
                'description': 'AI-Powered Anime Automation System for YouTube',
                'private': True,
                'auto_init': False
            }
            
            response = requests.post(
                'https://api.github.com/user/repos',
                headers=headers,
                json=data
            )
            
            if response.status_code == 201:
                log.info(f"✅ Repository created: {self.github_repo}")
                return True
            elif response.status_code == 422:
                log.info("Repository already exists")
                return True
            else:
                log.error(f"Failed to create repo: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            log.error(f"Error creating repository: {e}")
            return False
    
    def init_and_push(self, commit_message: str = "Initial commit - Anime Automation System") -> bool:
        """
        Initialize git repo and push to GitHub
        """
        try:
            log.info("\n" + "="*60)
            log.info("🚀 PUSHING TO GITHUB")
            log.info("="*60)
            
            # Change to repo directory
            os.chdir(self.repo_path)
            
            # Check if .git exists
            git_dir = self.repo_path / '.git'
            
            if git_dir.exists():
                log.info("Git repository already initialized")
                repo = Repo(self.repo_path)
            else:
                log.info("Initializing new git repository...")
                repo = Repo.init(self.repo_path)
            
            # Configure git
            with repo.config_writer() as git_config:
                git_config.set_value('user', 'name', self.github_username)
                git_config.set_value('user', 'email', f'{self.github_username}@users.noreply.github.com')
            
            # Add .gitignore
            gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
*.egg-info/
dist/
build/

# Environment
.env
*.log

# Videos and media
*.mp4
*.mkv
*.avi
anime_downloads/
processed_videos/
thumbnails/*.png

# Database
*.db
*.sqlite

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""
            
            gitignore_path = self.repo_path / '.gitignore'
            with open(gitignore_path, 'w') as f:
                f.write(gitignore_content)
            
            # Add all files
            log.info("Adding files to git...")
            repo.git.add(A=True)
            
            # Commit
            log.info(f"Creating commit: {commit_message}")
            repo.index.commit(commit_message)
            
            # Check if remote exists
            try:
                origin = repo.remote('origin')
                log.info("Remote 'origin' exists, updating URL...")
                origin.set_url(self.repo_url)
            except:
                log.info("Adding remote 'origin'...")
                origin = repo.create_remote('origin', self.repo_url)
            
            # Push to GitHub
            log.info(f"Pushing to GitHub: {self.github_username}/{self.github_repo}")
            
            try:
                # Try to push to main branch
                origin.push(refspec='HEAD:main', force=True)
                log.info("✅ Successfully pushed to 'main' branch")
            except GitCommandError:
                # If main doesn't exist, try master
                try:
                    origin.push(refspec='HEAD:master', force=True)
                    log.info("✅ Successfully pushed to 'master' branch")
                except GitCommandError as e:
                    log.error(f"Push failed: {e}")
                    return False
            
            log.info("\n✅ CODE UPLOADED TO GITHUB SUCCESSFULLY!")
            log.info(f"   Repository: https://github.com/{self.github_username}/{self.github_repo}")
            log.info(f"   Status: Private ✅")
            
            return True
            
        except Exception as e:
            log.error(f"GitHub upload error: {e}")
            return False
    
    def update_repo(self, commit_message: str = "Update anime automation system") -> bool:
        """
        Update existing repository with new changes
        """
        try:
            log.info("Updating GitHub repository...")
            
            repo = Repo(self.repo_path)
            
            # Check if there are changes
            if not repo.is_dirty() and not repo.untracked_files:
                log.info("No changes to commit")
                return True
            
            # Add all changes
            repo.git.add(A=True)
            
            # Commit
            repo.index.commit(commit_message)
            
            # Push
            origin = repo.remote('origin')
            origin.push()
            
            log.info("✅ Repository updated successfully")
            return True
            
        except Exception as e:
            log.error(f"Update error: {e}")
            return False


def main():
    """Main function"""
    uploader = GitHubUploader()
    
    # Create repository
    uploader.create_private_repo()
    
    # Push code
    success = uploader.init_and_push(
        commit_message="🎬 Initial commit - AI-Powered Anime Automation System"
    )
    
    if success:
        print("\n" + "="*60)
        print("✅ SUCCESS! Code uploaded to GitHub")
        print(f"   Repository: https://github.com/{uploader.github_username}/{uploader.github_repo}")
        print(f"   Visibility: Private 🔒")
        print("="*60)
    else:
        print("\n❌ Failed to upload to GitHub")


if __name__ == "__main__":
    main()
