"""
CVAT客户端封装
与CVAT标注平台交互
"""
import requests
from typing import Dict, Any, Optional

class CVATClient:
    """CVAT客户端"""
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self._authenticate()
        
    def _authenticate(self):
        """认证登录"""
        auth_response = self.session.post(
            f"{self.base_url}/auth/login",
            data={'username': self.username, 'password': self.password}
        )
        auth_response.raise_for_status()
        
    def create_task(self, name: str, labels: list, project_id: Optional[int] = None) -> int:
        """创建标注任务"""
        task_data = {
            'name': name,
            'labels': labels,
            'project_id': project_id
        }
        
        response = self.session.post(
            f"{self.base_url}/tasks",
            json=task_data
        )
        response.raise_for_status()
        return response.json()['id']
        
    def upload_data(self, task_id: int, file_path: str):
        """上传数据到任务"""
        with open(file_path, 'rb') as f:
            response = self.session.post(
                f"{self.base_url}/tasks/{task_id}/data",
                files={'client_files': f}
            )
        response.raise_for_status()
        
    def export_annotations(self, task_id: int, format: str = 'COCO 1.0') -> bytes:
        """导出标注结果"""
        response = self.session.get(
            f"{self.base_url}/tasks/{task_id}/annotations",
            params={'format': format}
        )
        response.raise_for_status()
        return response.content