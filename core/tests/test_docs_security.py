"""
Security Tests for Documentation Controller
"""
import pytest
import os
from api.controllers import docs_controller


class TestDocsSecurity:
    """Test security measures in docs controller"""
    
    def test_path_traversal_prevention(self):
        """Test path traversal attacks are blocked"""
        malicious_paths = [
            "../../../etc/passwd",
            "../../.env",
            "../constants.py",
            "/etc/passwd",
            "data/../../../etc/passwd",
        ]
        
        for path in malicious_paths:
            result, error = docs_controller.get_doc_content(path)
            
            # Should return error
            assert result is None
            assert error is not None
            assert any(keyword in error.lower() for keyword in 
                      ['traversal', 'invalid', 'access denied'])
    
    def test_absolute_path_prevention(self):
        """Test absolute paths are blocked"""
        result, error = docs_controller.get_doc_content('/etc/passwd')
        
        assert result is None
        assert error is not None
    
    def test_file_type_restriction(self):
        """Test only .md files are allowed"""
        invalid_extensions = [
            "test.txt",
            "config.json",
            "script.py",
            ".env",
        ]
        
        for filepath in invalid_extensions:
            result, error = docs_controller.get_doc_content(filepath)
            
            assert result is None
            assert error is not None
            # Error can be either file type or access denied
            assert any(keyword in error.lower() for keyword in ['file type', 'access denied', 'invalid'])
    
    def test_directory_access_blocked(self, temp_docs_dir):
        """Test accessing directories is blocked"""
        result, error = docs_controller.get_doc_content(temp_docs_dir)
        
        # Should not allow directory access
        assert result is None or error is not None
    
    def test_empty_path(self):
        """Test empty path is rejected"""
        result, error = docs_controller.get_doc_content('')
        
        assert result is None
        assert error is not None
        assert 'required' in error.lower()
    
    def test_none_path(self):
        """Test None path is rejected"""
        result, error = docs_controller.get_doc_content(None)
        
        assert result is None
        assert error is not None
    
    def test_update_path_traversal(self):
        """Test update operation blocks path traversal"""
        success, message = docs_controller.update_doc(
            "../../../etc/passwd",
            "malicious content"
        )
        
        assert success == False
        assert any(keyword in message.lower() for keyword in 
                  ['traversal', 'invalid', 'access denied'])
    
    def test_update_file_type_restriction(self):
        """Test update only allows .md files"""
        success, message = docs_controller.update_doc(
            "test.txt",
            "content"
        )
        
        assert success == False
        # Error can be either file type or access denied
        assert any(keyword in message.lower() for keyword in ['file type', 'access denied', 'invalid'])
    
    def test_create_service_validation(self):
        """Test create operation validates service names"""
        malicious_services = [
            "../../../tmp",
            "/etc",
            "service/../../../etc",
        ]
        
        for service in malicious_services:
            filepath, error = docs_controller.create_doc(
                service,
                "test",
                "content"
            )
            
            assert filepath is None
            assert error is not None
            assert any(keyword in error.lower() for keyword in 
                      ['invalid', 'dangerous', 'access denied'])
    
    def test_create_category_validation(self):
        """Test create operation validates category names"""
        filepath, error = docs_controller.create_doc(
            "service",
            "../../../passwd",
            "content"
        )
        
        assert filepath is None
        assert error is not None
        assert 'invalid' in error.lower()
