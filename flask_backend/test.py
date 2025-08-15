#!/usr/bin/env python3
"""
Comprehensive multimodal input test for the deployed endpoint at http://3.94.93.155/
Tests text + image + audio combinations and various multimodal scenarios.
Uses existing test files from app/tests/ directory.
"""

import requests
import json
import base64
import tempfile
import os
import time
from datetime import datetime
import uuid

# Configuration
BASE_URL = "http://3.94.93.155"
TIMEOUT = 60  # Longer timeout for multimodal requests

# Test file paths
TEST_IMAGE_PATH = "app/tests/test_image.jpeg"
TEST_AUDIO_PATH = "app/tests/test_audio.wav"

class MultimodalTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        
        # Generate unique test credentials
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.test_username = f"multimodal_test_{timestamp}"
        self.test_password = f"testpass_{timestamp}"
        self.test_email = f"multimodal_{timestamp}@example.com"
        
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", response=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        result = {
            "timestamp": timestamp,
            "test": test_name,
            "status": status,
            "details": details,
            "response_code": response.status_code if response else None,
            "response_time": response.elapsed.total_seconds() if response else None
        }
        
        self.test_results.append(result)
        print(f"[{timestamp}] {status} - {test_name}")
        if details:
            print(f"    Details: {details}")
        if response and not success:
            print(f"    Response: {response.status_code} - {response.text[:200]}...")
        print()
    
    def get_test_image(self) -> str:
        """Get the existing test image file path"""
        if os.path.exists(TEST_IMAGE_PATH):
            return TEST_IMAGE_PATH
        else:
            raise FileNotFoundError(f"Test image not found at {TEST_IMAGE_PATH}")
    
    def get_test_audio(self) -> str:
        """Get the existing test audio file path"""
        if os.path.exists(TEST_AUDIO_PATH):
            return TEST_AUDIO_PATH
        else:
            raise FileNotFoundError(f"Test audio not found at {TEST_AUDIO_PATH}")
    
    def file_to_base64(self, file_path: str) -> str:
        """Convert file to base64 string"""
        with open(file_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def setup_authentication(self) -> bool:
        """Setup authentication for testing"""
        print("🔐 Setting up authentication...")
        
        # Register user
        register_url = f"{self.base_url}/api/auth/register"
        register_data = {
            "username": self.test_username,
            "password": self.test_password,
            "email": self.test_email
        }
        
        try:
            response = self.session.post(register_url, json=register_data, timeout=TIMEOUT)
            if response.status_code not in [200, 201, 409]:  # 409 = user already exists
                self.log_test("Setup Registration", False, f"Failed: {response.status_code}", response)
                return False
        except Exception as e:
            self.log_test("Setup Registration", False, f"Exception: {str(e)}")
            return False
        
        # Login and get token
        login_url = f"{self.base_url}/api/auth/login"
        login_data = {
            "username": self.test_username,
            "password": self.test_password
        }
        
        try:
            response = self.session.post(login_url, json=login_data, timeout=TIMEOUT)
            if response.status_code == 200:
                response_data = response.json()
                self.token = (
                    response_data.get("token") or
                    response_data.get("data", {}).get("attributes", {}).get("token") or
                    response_data.get("data", {}).get("token")
                )
                if self.token:
                    self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                    print(f"✅ Authentication setup complete. Token: {self.token[:20]}...")
                    return True
                else:
                    self.log_test("Setup Login", False, "No token in response", response)
                    return False
            else:
                self.log_test("Setup Login", False, f"Failed: {response.status_code}", response)
                return False
        except Exception as e:
            self.log_test("Setup Login", False, f"Exception: {str(e)}")
            return False
    
    def test_text_only(self) -> bool:
        """Test text-only input"""
        url = f"{self.base_url}/api/chat/v1/mobile"
        data = {
            "model": "im-chat",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello! This is a text-only message. Please respond with a simple greeting."
                }
            ]
        }
        
        try:
            response = self.session.post(url, json=data, timeout=TIMEOUT)
            success = response.status_code == 200
            
            if success:
                try:
                    chat_response = response.json()
                    choices = chat_response.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        details = f"Response: {content[:100]}..."
                    else:
                        details = "No choices in response"
                        success = False
                except json.JSONDecodeError:
                    details = "Invalid JSON response"
                    success = False
            else:
                details = f"Request failed: {response.status_code}"
            
            self.log_test("Text Only", success, details, response)
            return success
        except Exception as e:
            self.log_test("Text Only", False, f"Exception: {str(e)}")
            return False
    
    def test_image_only(self) -> bool:
        """Test image-only input"""
        url = f"{self.base_url}/api/chat/v1/mobile"
        
        # Use existing test image
        test_image_path = self.get_test_image()
        try:
            img_b64 = self.file_to_base64(test_image_path)
            
            data = {
                "model": "im-chat",
                "messages": [
                    {
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_b64}"
                                }
                            }
                        ],
                        "role": "user"
                    }
                ]
            }
            
            response = self.session.post(url, json=data, timeout=TIMEOUT)
            success = response.status_code == 200
            
            if success:
                try:
                    chat_response = response.json()
                    choices = chat_response.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        details = f"Response: {content[:100]}..."
                    else:
                        details = "No choices in response"
                        success = False
                except json.JSONDecodeError:
                    details = "Invalid JSON response"
                    success = False
            else:
                details = f"Request failed: {response.status_code}"
            
            self.log_test("Image Only", success, details, response)
            return success
            
        except Exception as e:
            self.log_test("Image Only", False, f"Exception: {str(e)}")
            return False
    
    def test_audio_only(self) -> bool:
        """Test audio-only input"""
        url = f"{self.base_url}/api/chat/v1/mobile"
        
        # Use existing test audio
        test_audio_path = self.get_test_audio()
        try:
            aud_b64 = self.file_to_base64(test_audio_path)
            
            data = {
                "model": "im-chat",
                "messages": [
                    {
                        "content": [
                            {
                                "type": "audio_url",
                                "audio_url": {
                                    "url": f"data:audio/wav;base64,{aud_b64}"
                                }
                            }
                        ],
                        "role": "user"
                    }
                ]
            }
            
            response = self.session.post(url, json=data, timeout=TIMEOUT)
            success = response.status_code == 200
            
            if success:
                try:
                    chat_response = response.json()
                    choices = chat_response.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        details = f"Response: {content[:100]}..."
                    else:
                        details = "No choices in response"
                        success = False
                except json.JSONDecodeError:
                    details = "Invalid JSON response"
                    success = False
            else:
                details = f"Request failed: {response.status_code}"
            
            self.log_test("Audio Only", success, details, response)
            return success
            
        except Exception as e:
            self.log_test("Audio Only", False, f"Exception: {str(e)}")
            return False
    
    def test_text_and_image(self) -> bool:
        """Test text + image input"""
        url = f"{self.base_url}/api/chat/v1/mobile"
        
        # Use existing test image
        test_image_path = self.get_test_image()
        try:
            img_b64 = self.file_to_base64(test_image_path)
            
            data = {
                "model": "im-chat",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "What do you see in this image? Please describe it in detail."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_b64}"
                                }
                            }
                        ]
                    }
                ]
            }
            
            response = self.session.post(url, json=data, timeout=TIMEOUT)
            success = response.status_code == 200
            
            if success:
                try:
                    chat_response = response.json()
                    choices = chat_response.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        details = f"Response: {content[:100]}..."
                    else:
                        details = "No choices in response"
                        success = False
                except json.JSONDecodeError:
                    details = "Invalid JSON response"
                    success = False
            else:
                details = f"Request failed: {response.status_code}"
            
            self.log_test("Text + Image", success, details, response)
            return success
            
        except Exception as e:
            self.log_test("Text + Image", False, f"Exception: {str(e)}")
            return False
    
    def test_text_and_audio(self) -> bool:
        """Test text + audio input"""
        url = f"{self.base_url}/api/chat/v1/mobile"
        
        # Use existing test audio
        test_audio_path = self.get_test_audio()
        try:
            aud_b64 = self.file_to_base64(test_audio_path)
            
            data = {
                "model": "im-chat",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "I'm sending you an audio message. Please respond to what I said."
                            },
                            {
                                "type": "audio_url",
                                "audio_url": {
                                    "url": f"data:audio/wav;base64,{aud_b64}"
                                }
                            }
                        ]
                    }
                ]
            }
            
            response = self.session.post(url, json=data, timeout=TIMEOUT)
            success = response.status_code == 200
            
            if success:
                try:
                    chat_response = response.json()
                    choices = chat_response.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        details = f"Response: {content[:100]}..."
                    else:
                        details = "No choices in response"
                        success = False
                except json.JSONDecodeError:
                    details = "Invalid JSON response"
                    success = False
            else:
                details = f"Request failed: {response.status_code}"
            
            self.log_test("Text + Audio", success, details, response)
            return success
            
        except Exception as e:
            self.log_test("Text + Audio", False, f"Exception: {str(e)}")
            return False
    
    def test_image_and_audio(self) -> bool:
        """Test image + audio input"""
        url = f"{self.base_url}/api/chat/v1/mobile"
        
        # Use existing test files
        test_image_path = self.get_test_image()
        test_audio_path = self.get_test_audio()
        try:
            img_b64 = self.file_to_base64(test_image_path)
            aud_b64 = self.file_to_base64(test_audio_path)
            
            data = {
                "model": "im-chat",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_b64}"
                                }
                            },
                            {
                                "type": "audio_url",
                                "audio_url": {
                                    "url": f"data:audio/wav;base64,{aud_b64}"
                                }
                            }
                        ]
                    }
                ]
            }
            
            response = self.session.post(url, json=data, timeout=TIMEOUT)
            success = response.status_code == 200
            
            if success:
                try:
                    chat_response = response.json()
                    choices = chat_response.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        details = f"Response: {content[:100]}..."
                    else:
                        details = "No choices in response"
                        success = False
                except json.JSONDecodeError:
                    details = "Invalid JSON response"
                    success = False
            else:
                details = f"Request failed: {response.status_code}"
            
            self.log_test("Image + Audio", success, details, response)
            return success
            
        except Exception as e:
            self.log_test("Image + Audio", False, f"Exception: {str(e)}")
            return False
    
    def test_text_image_audio(self) -> bool:
        """Test text + image + audio input (full multimodal)"""
        url = f"{self.base_url}/api/chat/v1/mobile"
        
        # Use existing test files
        test_image_path = self.get_test_image()
        test_audio_path = self.get_test_audio()
        try:
            img_b64 = self.file_to_base64(test_image_path)
            aud_b64 = self.file_to_base64(test_audio_path)
            
            data = {
                "model": "im-chat",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "I'm sending you an image and an audio message. Please analyze both and respond."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_b64}"
                                }
                            },
                            {
                                "type": "audio_url",
                                "audio_url": {
                                    "url": f"data:audio/wav;base64,{aud_b64}"
                                }
                            }
                        ]
                    }
                ]
            }
            
            response = self.session.post(url, json=data, timeout=TIMEOUT)
            success = response.status_code == 200
            
            if success:
                try:
                    chat_response = response.json()
                    choices = chat_response.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        details = f"Response: {content[:100]}..."
                    else:
                        details = "No choices in response"
                        success = False
                except json.JSONDecodeError:
                    details = "Invalid JSON response"
                    success = False
            else:
                details = f"Request failed: {response.status_code}"
            
            self.log_test("Text + Image + Audio", success, details, response)
            return success
            
        except Exception as e:
            self.log_test("Text + Image + Audio", False, f"Exception: {str(e)}")
            return False
    
    def test_conversation_history(self) -> bool:
        """Test multimodal input with conversation history"""
        url = f"{self.base_url}/api/chat/v1/mobile"
        
        # Use existing test image
        test_image_path = self.get_test_image()
        try:
            img_b64 = self.file_to_base64(test_image_path)
            
            data = {
                "model": "im-chat",
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello! I'm starting a conversation."
                    },
                    {
                        "role": "assistant",
                        "content": "Hello! I'm here to help you. What would you like to discuss?"
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Can you analyze this image and tell me what you see?"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_b64}"
                                }
                            }
                        ]
                    }
                ]
            }
            
            response = self.session.post(url, json=data, timeout=TIMEOUT)
            success = response.status_code == 200
            
            if success:
                try:
                    chat_response = response.json()
                    choices = chat_response.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        details = f"Conversation with history. Response: {content[:100]}..."
                    else:
                        details = "No choices in response"
                        success = False
                except json.JSONDecodeError:
                    details = "Invalid JSON response"
                    success = False
            else:
                details = f"Request failed: {response.status_code}"
            
            self.log_test("Conversation History", success, details, response)
            return success
            
        except Exception as e:
            self.log_test("Conversation History", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all multimodal tests"""
        print(f"🚀 Starting Multimodal Endpoint Tests")
        print(f"📡 Target: {self.base_url}")
        print(f"👤 Test User: {self.test_username}")
        print(f"🖼️  Test Image: {TEST_IMAGE_PATH}")
        print(f"🎵 Test Audio: {TEST_AUDIO_PATH}")
        print("="*80)
        
        # Setup authentication first
        if not self.setup_authentication():
            print("❌ Authentication setup failed. Cannot proceed with tests.")
            return 0, 0
        
        print("\n🧪 Running Multimodal Tests...")
        print("="*80)
        
        # Test sequence
        tests = [
            ("Text Only", self.test_text_only),
            ("Image Only", self.test_image_only),
            ("Audio Only", self.test_audio_only),
            ("Text + Image", self.test_text_and_image),
            ("Text + Audio", self.test_text_and_audio),
            ("Image + Audio", self.test_image_and_audio),
            ("Text + Image + Audio", self.test_text_image_audio),
            ("Conversation History", self.test_conversation_history),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                time.sleep(1)  # Brief pause between tests
            except Exception as e:
                self.log_test(test_name, False, f"Test crashed: {str(e)}")
        
        # Generate summary
        print("="*80)
        print(f"📊 MULTIMODAL TEST SUMMARY")
        print("="*80)
        print(f"Base URL: {self.base_url}")
        print(f"Test User: {self.test_username}")
        print(f"Test Files Used:")
        print(f"  - Image: {TEST_IMAGE_PATH}")
        print(f"  - Audio: {TEST_AUDIO_PATH}")
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {((passed / total) * 100):.1f}%")
        
        if passed == total:
            print("🎉 All multimodal tests passed! The endpoint handles all input types perfectly.")
        elif passed > total * 0.8:
            print("✅ Most multimodal tests passed! The endpoint is working well.")
        elif passed > total * 0.5:
            print("⚠️  Some multimodal tests failed. Check the details above.")
        else:
            print("❌ Most multimodal tests failed. The endpoint may have issues.")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"multimodal_test_results_{timestamp}.json"
        
        summary = {
            "base_url": self.base_url,
            "timestamp": datetime.now().isoformat(),
            "test_user": self.test_username,
            "test_files": {
                "image": TEST_IMAGE_PATH,
                "audio": TEST_AUDIO_PATH
            },
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": (passed / total) * 100 if total > 0 else 0,
            "results": self.test_results
        }
        
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return passed, total

def main():
    """Main function to run the multimodal tests"""
    tester = MultimodalTester(BASE_URL)
    passed, total = tester.run_all_tests()
    
    return (passed / total) >= 0.8  # Return True if 80%+ tests passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 