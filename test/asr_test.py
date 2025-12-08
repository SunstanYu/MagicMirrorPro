"""
Google ASR Client 测试文件
"""
import sys
import os
from pathlib import Path
import unittest
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from asr.google_asr_client import GoogleASRClient
from asr.models import ASRResult


class TestGoogleASRClient(unittest.TestCase):
    """GoogleASRClient 测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.test_audio_path = project_root / "resources" / "short_speech.flac"
        cls.credentials_path = project_root / "asr" / "valid-meridian-477720-a7-35a952ac4296.json"
        
        # 检查测试文件是否存在
        if not cls.test_audio_path.exists():
            print(f"⚠️ 警告: 测试音频文件不存在: {cls.test_audio_path}")
        if not cls.credentials_path.exists():
            print(f"⚠️ 警告: Google 凭证文件不存在: {cls.credentials_path}")
    
    def setUp(self):
        """每个测试方法前的初始化"""
        # 检查凭证文件是否存在，如果不存在则跳过真实 API 测试
        self.skip_real_api = not self.credentials_path.exists()
        if self.skip_real_api:
            print("⚠️ 跳过真实 API 测试（凭证文件不存在）")
    
    def test_init(self):
        """测试初始化"""
        if self.skip_real_api:
            self.skipTest("凭证文件不存在，跳过真实 API 测试")
        
        try:
            client = GoogleASRClient()
            self.assertIsNotNone(client.client)
            self.assertIsNotNone(client.credentials_path)
            print("✅ GoogleASRClient 初始化成功")
        except Exception as e:
            self.fail(f"初始化失败: {e}")
    
    def test_transcribe_with_real_audio(self):
        """测试使用真实音频文件进行转写"""
        if self.skip_real_api:
            self.skipTest("凭证文件不存在，跳过真实 API 测试")
        
        if not self.test_audio_path.exists():
            self.skipTest(f"测试音频文件不存在: {self.test_audio_path}")
        
        try:
            client = GoogleASRClient()
            result = client.transcribe(str(self.test_audio_path), language_code="en-US")
            
            # 验证返回结果类型
            self.assertIsInstance(result, ASRResult)
            
            # 验证结果字段
            self.assertIsNotNone(result.text)
            self.assertIsInstance(result.text, str)
            self.assertGreater(len(result.text), 0, "识别文本不应为空")
            
            self.assertGreaterEqual(result.confidence, 0.0)
            self.assertLessEqual(result.confidence, 1.0)
            self.assertEqual(result.language_code, "en-US")
            
            print(f"✅ 转写成功: {result.text}")
            print(f"   置信度: {result.confidence:.4f}")
            print(f"   语言: {result.language_code}")
            
        except Exception as e:
            self.fail(f"转写失败: {e}")
    
    
    def test_transcribe_file_not_found(self):
        """测试文件不存在的情况"""
        if self.skip_real_api:
            self.skipTest("凭证文件不存在，跳过真实 API 测试")
        
        try:
            client = GoogleASRClient()
            # 应该抛出 FileNotFoundError
            with self.assertRaises(FileNotFoundError):
                client.transcribe("nonexistent_file.flac")
        except Exception as e:
            # 如果初始化失败，跳过测试
            self.skipTest(f"初始化失败: {e}")
    
    
    def test_transcribe_empty_response(self):
        """测试 API 返回空结果的情况"""
        # Mock 返回空结果
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.results = []  # 空结果
        mock_client.recognize.return_value = mock_response
        
        with patch('asr.google_asr_client.speech.SpeechClient') as mock_speech_client:
            mock_speech_client.from_service_account_json.return_value = mock_client
            
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.flac', delete=False) as tmp_file:
                tmp_file.write(b'fake audio data')
                tmp_path = tmp_file.name
            
            try:
                client = GoogleASRClient()
                result = client.transcribe(tmp_path, language_code="en-US")
                
                # 应该返回默认结果
                self.assertIsInstance(result, ASRResult)
                self.assertEqual(result.text, "[Google ASR 未实现]")
                self.assertEqual(result.confidence, 0.0)
                print("✅ 空结果处理测试通过")
                
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
    


class TestGoogleASRClientIntegration(unittest.TestCase):
    """集成测试类（需要真实 API 和音频文件）"""
    
    def setUp(self):
        """初始化"""
        self.test_audio_path = project_root / "resources" / "short_speech.flac"
        self.credentials_path = project_root / "asr" / "valid-meridian-477720-a7-35a952ac4296.json"
        
        if not self.credentials_path.exists():
            self.skipTest("凭证文件不存在，跳过集成测试")
        if not self.test_audio_path.exists():
            self.skipTest("测试音频文件不存在，跳过集成测试")
    
    def test_full_integration(self):
        """完整集成测试：初始化 -> 转写 -> 验证结果"""
        try:
            # 初始化客户端
            client = GoogleASRClient()
            self.assertIsNotNone(client.client)
            
            # 执行转写
            result = client.transcribe(str(self.test_audio_path))
            
            # 验证结果
            self.assertIsInstance(result, ASRResult)
            self.assertIsNotNone(result.text)
            self.assertGreater(len(result.text), 0)
            self.assertGreater(result.confidence, 0.0)
            
            print(f"\n📝 集成测试结果:")
            print(f"   文本: {result.text}")
            print(f"   置信度: {result.confidence:.4f}")
            print(f"   语言: {result.language_code}")
            print("✅ 集成测试通过")
            
        except Exception as e:
            self.fail(f"集成测试失败: {e}")


def run_tests():
    """运行测试"""
    print("=" * 60)
    print("🧪 开始运行 Google ASR Client 测试")
    print("=" * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestGoogleASRClient))
    suite.addTests(loader.loadTestsFromTestCase(TestGoogleASRClientIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出总结
    print("\n" + "=" * 60)
    print("📊 测试总结:")
    print(f"   运行: {result.testsRun}")
    print(f"   成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   失败: {len(result.failures)}")
    print(f"   错误: {len(result.errors)}")
    print(f"   跳过: {len(result.skipped)}")
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

