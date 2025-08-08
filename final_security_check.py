#!/usr/bin/env python3
"""
Final Security Check - Sadece gerçek güvenlik açıklarını tespit eder
"""

import os
import re
from pathlib import Path

def check_real_secrets():
    """Gerçek güvenlik açıklarını kontrol et"""
    
    real_patterns = {
        'aws_access_key': r'AKIA[0-9A-Z]{16}',
        'google_api_key': r'AIzaSy[0-9A-Za-z_-]{33}',
        'openai_api_key': r'sk-[0-9A-Za-z]{48}',
        'instagram_token': r'IG[A-Z0-9]{50,}',
        'whatsapp_token': r'EAA[A-Za-z0-9]{100,}',
    }
    
    exclude_patterns = [
        r'your-.*-here',
        r'your-.*-change',
        r'placeholder',
        r'example',
        r'test',
        r'demo',
        r'sample',
    ]
    
    findings = []
    
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'venv', 'node_modules'}]
        
        for file in files:
            if file.endswith(('.py', '.md', '.txt', '.env', '.json', '.sh')):
                file_path = Path(root) / file
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    for pattern_name, pattern in real_patterns.items():
                        matches = re.finditer(pattern, content)
                        
                        for match in matches:
                            matched_text = match.group()
                            
                            # Skip safe placeholders
                            if any(re.search(exclude, matched_text, re.IGNORECASE) for exclude in exclude_patterns):
                                continue
                                
                            line_num = content[:match.start()].count('\n') + 1
                            
                            findings.append({
                                'file': str(file_path),
                                'line': line_num,
                                'pattern': pattern_name,
                                'match': matched_text[:20] + '...' if len(matched_text) > 20 else matched_text
                            })
                            
                except Exception:
                    continue
    
    return findings

def main():
    print("🔍 Final Security Check - Real threats only")
    print("=" * 50)
    
    findings = check_real_secrets()
    
    if not findings:
        print("🎉 NO REAL SECURITY THREATS FOUND!")
        print("✅ All API keys and secrets are properly secured with placeholders.")
        return 0
    else:
        print(f"🚨 {len(findings)} REAL SECURITY THREATS FOUND:")
        print("-" * 50)
        
        for finding in findings:
            print(f"❌ {finding['file']}:{finding['line']}")
            print(f"   Pattern: {finding['pattern']}")
            print(f"   Match: {finding['match']}")
            print()
        
        print("⚠️  IMMEDIATE ACTION REQUIRED!")
        return 1

if __name__ == '__main__':
    exit(main())