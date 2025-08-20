#!/usr/bin/env python3
"""
MediaScribe 测试脚本
验证各个组件是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.video_processor import VideoProcessor
from src.asr_service import ASRService
from src.llm_service import LLMService
from src.summary_generator import SummaryGenerator
from src.utils import setup_logging

def test_video_info():
    """测试视频信息获取"""
    print("=" * 50)
    print("测试视频信息获取")
    print("=" * 50)
    
    video_path = "test/500001644709044-1-192.mp4"
    if not os.path.exists(video_path):
        print(f"❌ 测试视频文件不存在: {video_path}")
        return False
    
    try:
        processor = VideoProcessor()
        info = processor.get_video_info(video_path)
        
        print(f"✅ 视频时长: {info['duration']:.2f}秒")
        print(f"✅ 文件大小: {info['size']} 字节")
        print(f"✅ 格式: {info['format_name']}")
        print(f"✅ 流数量: {len(info['streams'])}")
        
        return True
    except Exception as e:
        print(f"❌ 视频信息获取失败: {e}")
        return False

def test_asr_service():
    """测试ASR服务连接"""
    print("=" * 50)
    print("测试ASR服务连接")
    print("=" * 50)
    
    try:
        asr = ASRService()
        if asr.health_check():
            print("✅ ASR服务连接正常")
            return True
        else:
            print("❌ ASR服务连接失败")
            return False
    except Exception as e:
        print(f"❌ ASR服务测试失败: {e}")
        return False

def test_llm_service():
    """测试LLM服务连接"""
    print("=" * 50)
    print("测试LLM服务连接")
    print("=" * 50)
    
    try:
        llm = LLMService()
        if llm.health_check():
            print("✅ LLM服务连接正常")
            return True
        else:
            print("❌ LLM服务连接失败")
            return False
    except Exception as e:
        print(f"❌ LLM服务测试失败: {e}")
        return False

def test_audio_extraction():
    """测试音频提取"""
    print("=" * 50)
    print("测试音频提取")
    print("=" * 50)
    
    video_path = "test/500001644709044-1-192.mp4"
    if not os.path.exists(video_path):
        print(f"❌ 测试视频文件不存在: {video_path}")
        return False
    
    try:
        processor = VideoProcessor()
        audio_path = processor.extract_audio(video_path, "test")
        
        if os.path.exists(audio_path):
            print(f"✅ 音频提取成功: {audio_path}")
            file_size = os.path.getsize(audio_path)
            print(f"✅ 音频文件大小: {file_size} 字节")
            return True
        else:
            print("❌ 音频文件未生成")
            return False
    except Exception as e:
        print(f"❌ 音频提取失败: {e}")
        return False

def main():
    """运行所有测试"""
    setup_logging(debug=True)
    
    print("MediaScribe 组件测试")
    print("时间:", __import__('datetime').datetime.now())
    print()
    
    tests = [
        ("视频信息获取", test_video_info),
        ("音频提取", test_audio_extraction),
        ("ASR服务连接", test_asr_service),
        ("LLM服务连接", test_llm_service),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results[test_name] = False
        print()
    
    # 输出总结
    print("=" * 50)
    print("测试结果总结")
    print("=" * 50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print()
    print(f"总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！可以开始使用MediaScribe")
        return 0
    else:
        print("⚠️  部分测试失败，请检查相关服务和配置")
        return 1

if __name__ == '__main__':
    sys.exit(main())
