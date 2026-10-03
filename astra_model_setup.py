"""
ChatGPT Astra Opensource Model Integration
This module integrates the Astra opensource model for project creation and management
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime


class AstraProjectGenerator:
    """
    Astra Model-based Project Generator
    Creates new projects using the opensource Astra model
    """
    
    def __init__(self, model_name: str = "astra-opensource"):
        """
        Initialize the Astra model for project generation
        
        Args:
            model_name: Name of the Astra model to use
        """
        self.model_name = model_name
        self.projects = []
        self.config = {
            "model": model_name,
            "version": "1.0.0",
            "created_at": datetime.now().isoformat()
        }
    
    def create_project(self, project_name: str, project_type: str, 
                      description: str = "", config: Optional[Dict] = None) -> Dict:
        """
        Create a new project using the Astra model
        
        Args:
            project_name: Name of the project
            project_type: Type of project (web, api, ml, data, etc.)
            description: Project description
            config: Additional configuration options
            
        Returns:
            Dictionary containing project details
        """
        project = {
            "id": len(self.projects) + 1,
            "name": project_name,
            "type": project_type,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "status": "initialized",
            "model_version": self.model_name,
            "structure": self._generate_project_structure(project_type),
            "config": config or {}
        }
        
        self.projects.append(project)
        return project
    
    def _generate_project_structure(self, project_type: str) -> Dict:
        """
        Generate project structure based on project type
        
        Args:
            project_type: Type of project
            
        Returns:
            Dictionary containing project directory structure
        """
        structures = {
            "web": {
                "directories": ["src", "public", "tests", "docs"],
                "files": [
                    "README.md",
                    "package.json",
                    ".gitignore",
                    "src/index.html",
                    "src/App.js",
                    "src/styles.css"
                ]
            },
            "api": {
                "directories": ["src", "routes", "models", "middleware", "tests", "docs"],
                "files": [
                    "README.md",
                    "requirements.txt",
                    ".gitignore",
                    "src/main.py",
                    "routes/__init__.py",
                    "models/__init__.py"
                ]
            },
            "ml": {
                "directories": ["data", "models", "notebooks", "src", "tests", "docs"],
                "files": [
                    "README.md",
                    "requirements.txt",
                    ".gitignore",
                    "setup.py",
                    "notebooks/analysis.ipynb",
                    "src/train.py",
                    "src/predict.py"
                ]
            },
            "data": {
                "directories": ["raw", "processed", "scripts", "queries", "docs"],
                "files": [
                    "README.md",
                    ".gitignore",
                    "scripts/etl.py",
                    "queries/schema.sql",
                    "docs/data_dictionary.md"
                ]
            },
            "default": {
                "directories": ["src", "tests", "docs"],
                "files": ["README.md", ".gitignore"]
            }
        }
        
        return structures.get(project_type, structures["default"])
    
    def list_projects(self) -> List[Dict]:
        """
        List all created projects
        
        Returns:
            List of project dictionaries
        """
        return self.projects
    
    def get_project(self, project_id: int) -> Optional[Dict]:
        """
        Get specific project details
        
        Args:
            project_id: ID of the project
            
        Returns:
            Project dictionary or None if not found
        """
        for project in self.projects:
            if project["id"] == project_id:
                return project
        return None
    
    def export_project_config(self, project_id: int, filename: str = None) -> str:
        """
        Export project configuration as JSON
        
        Args:
            project_id: ID of the project
            filename: Output filename (optional)
            
        Returns:
            JSON string of project configuration
        """
        project = self.get_project(project_id)
        if not project:
            return ""
        
        if filename:
            with open(filename, 'w') as f:
                json.dump(project, f, indent=2)
            return f"Project config exported to {filename}"
        
        return json.dumps(project, indent=2)


def main():
    """Example usage of the Astra Project Generator"""
    
    # Initialize the generator
    generator = AstraProjectGenerator()
    
    # Create sample projects
    web_project = generator.create_project(
        project_name="MyWebApp",
        project_type="web",
        description="Modern web application using Astra model"
    )
    
    api_project = generator.create_project(
        project_name="DataAPI",
        project_type="api",
        description="RESTful API with Astra model integration",
        config={"framework": "FastAPI", "database": "PostgreSQL"}
    )
    
    ml_project = generator.create_project(
        project_name="MLModel",
        project_type="ml",
        description="Machine learning project with Astra",
        config={"framework": "PyTorch", "dataset": "custom"}
    )
    
    # Display created projects
    print("=" * 60)
    print("ASTRA Project Generator - Created Projects")
    print("=" * 60)
    
    for project in generator.list_projects():
        print(f"\n📦 Project: {project['name']}")
        print(f"   Type: {project['type']}")
        print(f"   Description: {project['description']}")
        print(f"   Status: {project['status']}")
        print(f"   Created: {project['created_at']}")
        print(f"   Structure:")
        for directory in project['structure']['directories']:
            print(f"      📁 {directory}/")
        for file in project['structure']['files']:
            print(f"      📄 {file}")


if __name__ == "__main__":
    main()
