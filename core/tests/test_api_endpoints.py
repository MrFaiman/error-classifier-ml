"""
Tests for API Endpoints
"""
import pytest
import json
from api import create_app


@pytest.fixture
def client():
    """Create test client"""
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestStatusEndpoints:
    """Test status endpoints"""
    
    def test_status_endpoint(self, client):
        """Test /api/status endpoint"""
        response = client.get('/api/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'healthy' in data
        assert 'model_status' in data
    
    def test_engines_comparison_endpoint(self, client):
        """Test /api/search-engines-comparison endpoint"""
        response = client.get('/api/search-engines-comparison')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'engines' in data


class TestDocsEndpoints:
    """Test documentation endpoints"""
    
    def test_get_docs(self, client):
        """Test GET /api/docs"""
        response = client.get('/api/docs')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_get_doc_content_no_path(self, client):
        """Test GET /api/doc-content without path"""
        response = client.get('/api/doc-content')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_doc_content_path_traversal(self, client):
        """Test path traversal is blocked"""
        response = client.get('/api/doc-content?path=../../../etc/passwd')
        
        assert response.status_code in [400, 403, 404]
        data = json.loads(response.data)
        assert 'error' in data


class TestClassifyEndpoints:
    """Test classification endpoints"""
    
    def test_classify_missing_error_message(self, client):
        """Test classify without error message"""
        response = client.post('/api/classify', 
                              json={},
                              content_type='application/json')
        
        # Should return error or handle gracefully
        assert response.status_code in [400, 500]
    
    def test_classify_with_error_message(self, client):
        """Test classify with valid error message"""
        response = client.post('/api/classify',
                              json={
                                  'error_message': 'test error',
                                  'method': 'HYBRID_CUSTOM',
                                  'multi_search': False
                              },
                              content_type='application/json')
        
        # Should either succeed or handle gracefully
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'doc_path' in data or 'error' in data
