"""
Astra API-Backed Model Integration
FastAPI server for ChatGPT Astra opensource model integration
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
import httpx
import json
import logging
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Astra Project Generator API",
    description="API for creating projects using Astra opensource model",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProjectType(str, Enum):
    """Supported project types"""
    WEB = "web"
    API = "api"
    ML = "ml"
    DATA = "data"
    FULLSTACK = "fullstack"


class ProjectRequest(BaseModel):
    """Request model for project creation"""
    project_name: str
    project_type: ProjectType
    description: Optional[str] = ""
    tech_stack: Optional[List[str]] = None
    use_ai_generation: Optional[bool] = True


class ProjectResponse(BaseModel):
    """Response model for project details"""
    id: int
    name: str
    type: str
    description: str
    created_at: str
    status: str
    structure: Dict
    config: Dict
    ai_generated: bool


class AstraAPIClient:
    """Client for interacting with Astra model API"""
    
    def __init__(self, api_endpoint: str = None, api_key: str = None):
        """
        Initialize Astra API client
        
        Args:
            api_endpoint: Base URL for Astra model API
            api_key: API key for authentication
        """
        # Support both OpenAI-like and custom endpoints
        self.api_endpoint = api_endpoint or "https://api.openai.com/v1"
        self.api_key = api_key or "sk-default-key"
        self.model = "gpt-3.5-turbo"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_project_structure(self, project_name: str, 
                                        project_type: str, 
                                        description: str) -> Dict:
        """
        Use AI to generate project structure
        
        Args:
            project_name: Name of the project
            project_type: Type of project
            description: Project description
            
        Returns:
            Generated project structure
        """
        prompt = f"""
        Generate a professional project structure for a {project_type} project named '{project_name}'.
        Description: {description}
        
        Provide the response in JSON format with the following structure:
        {{
            "directories": ["list", "of", "directories"],
            "files": ["list", "of", "files"],
            "config": {{"key": "value"}},
            "dependencies": ["list", "of", "dependencies"]
        }}
        """
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_endpoint}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are a software architect helping create project structures."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1000
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    # Parse JSON from response
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        return self._get_default_structure(project_type)
                else:
                    logger.warning(f"API response status: {response.status_code}")
                    return self._get_default_structure(project_type)
        except Exception as e:
            logger.error(f"Error calling Astra API: {str(e)}")
            return self._get_default_structure(project_type)
    
    async def generate_readme(self, project_name: str, project_type: str, 
                             description: str) -> str:
        """
        Generate a project README
        
        Args:
            project_name: Name of the project
            project_type: Type of project
            description: Project description
            
        Returns:
            Generated README content
        """
        prompt = f"""
        Generate a professional README.md for a {project_type} project named '{project_name}'.
        Description: {description}
        
        Include sections for: Overview, Features, Installation, Usage, Contributing, and License.
        """
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_endpoint}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are a technical writer creating project documentation."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 2000
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return f"# {project_name}\n\n{description}"
        except Exception as e:
            logger.error(f"Error generating README: {str(e)}")
            return f"# {project_name}\n\n{description}"
    
    def _get_default_structure(self, project_type: str) -> Dict:
        """Get default structure for project type"""
        structures = {
            "web": {
                "directories": ["src", "public", "components", "tests", "docs"],
                "files": ["README.md", "package.json", ".gitignore", "src/index.html", "src/App.js"],
                "dependencies": ["react", "react-dom", "axios"],
                "config": {"framework": "React", "build_tool": "Vite"}
            },
            "api": {
                "directories": ["src", "routes", "models", "middleware", "tests", "docs"],
                "files": ["README.md", "requirements.txt", ".gitignore", "src/main.py"],
                "dependencies": ["fastapi", "uvicorn", "sqlalchemy"],
                "config": {"framework": "FastAPI", "database": "PostgreSQL"}
            },
            "ml": {
                "directories": ["data", "models", "notebooks", "src", "tests", "docs"],
                "files": ["README.md", "requirements.txt", ".gitignore", "setup.py"],
                "dependencies": ["numpy", "pandas", "scikit-learn", "torch"],
                "config": {"framework": "PyTorch", "dataset": "custom"}
            },
            "data": {
                "directories": ["raw", "processed", "scripts", "queries", "docs"],
                "files": ["README.md", ".gitignore"],
                "dependencies": ["pandas", "numpy", "sqlalchemy"],
                "config": {"database": "PostgreSQL", "version_control": "dvc"}
            },
            "fullstack": {
                "directories": ["frontend", "backend", "shared", "tests", "docs", "deployment"],
                "files": ["README.md", ".gitignore", "docker-compose.yml"],
                "dependencies": ["react", "fastapi", "postgresql", "docker"],
                "config": {"frontend": "React", "backend": "FastAPI"}
            }
        }
        return structures.get(project_type, structures["web"])


class ProjectManager:
    """Manages project lifecycle"""
    
    def __init__(self):
        self.projects: Dict[int, Dict] = {}
        self.project_counter = 0
        self.astra_client = AstraAPIClient()
    
    async def create_project(self, request: ProjectRequest, use_ai: bool = True) -> ProjectResponse:
        """
        Create a new project
        
        Args:
            request: Project creation request
            use_ai: Whether to use AI for generation
            
        Returns:
            Created project response
        """
        self.project_counter += 1
        project_id = self.project_counter
        
        # Generate structure
        if use_ai and request.use_ai_generation:
            structure = await self.astra_client.generate_project_structure(
                request.project_name,
                request.project_type,
                request.description
            )
        else:
            structure = self.astra_client._get_default_structure(request.project_type)
        
        project = {
            "id": project_id,
            "name": request.project_name,
            "type": request.project_type,
            "description": request.description,
            "created_at": datetime.now().isoformat(),
            "status": "initialized",
            "structure": structure,
            "config": {
                "tech_stack": request.tech_stack or [],
                "ai_generated": use_ai and request.use_ai_generation
            },
            "ai_generated": use_ai and request.use_ai_generation
        }
        
        self.projects[project_id] = project
        logger.info(f"Project {project_id} created: {request.project_name}")
        
        return ProjectResponse(**project)
    
    def get_project(self, project_id: int) -> Optional[ProjectResponse]:
        """Get project by ID"""
        if project_id in self.projects:
            return ProjectResponse(**self.projects[project_id])
        return None
    
    def list_projects(self) -> List[ProjectResponse]:
        """List all projects"""
        return [ProjectResponse(**p) for p in self.projects.values()]
    
    async def generate_readme(self, project_id: int) -> str:
        """Generate README for a project"""
        if project_id not in self.projects:
            raise ValueError(f"Project {project_id} not found")
        
        project = self.projects[project_id]
        return await self.astra_client.generate_readme(
            project["name"],
            project["type"],
            project["description"]
        )


# Initialize project manager
project_manager = ProjectManager()


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Astra Project Generator API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "create_project": "POST /projects",
            "list_projects": "GET /projects",
            "get_project": "GET /projects/{project_id}",
            "generate_readme": "GET /projects/{project_id}/readme",
            "health": "GET /health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Astra Project Generator"
    }


@app.post("/projects", response_model=ProjectResponse)
async def create_project(request: ProjectRequest, background_tasks: BackgroundTasks):
    """
    Create a new project with AI-powered structure generation
    
    Args:
        request: Project creation request
        
    Returns:
        Created project details
    """
    try:
        project = await project_manager.create_project(request)
        return project
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects", response_model=List[ProjectResponse])
async def list_projects(skip: int = 0, limit: int = 100):
    """
    List all projects
    
    Args:
        skip: Number of projects to skip
        limit: Maximum number of projects to return
        
    Returns:
        List of projects
    """
    projects = project_manager.list_projects()
    return projects[skip:skip + limit]


@app.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int):
    """
    Get project details by ID
    
    Args:
        project_id: ID of the project
        
    Returns:
        Project details
    """
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.get("/projects/{project_id}/readme")
async def get_project_readme(project_id: int):
    """
    Generate and get README for a project
    
    Args:
        project_id: ID of the project
        
    Returns:
        Generated README content
    """
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        readme = await project_manager.generate_readme(project_id)
        return {
            "project_id": project_id,
            "project_name": project.name,
            "readme": readme,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating README: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/projects/{project_id}/regenerate")
async def regenerate_project_structure(project_id: int):
    """
    Regenerate project structure using AI
    
    Args:
        project_id: ID of the project
        
    Returns:
        Updated project details
    """
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        new_structure = await project_manager.astra_client.generate_project_structure(
            project.name,
            project.type,
            project.description
        )
        project_manager.projects[project_id]["structure"] = new_structure
        return project_manager.get_project(project_id)
    except Exception as e:
        logger.error(f"Error regenerating structure: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
