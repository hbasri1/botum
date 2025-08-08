#!/usr/bin/env python3
"""
Security Check Script - Hardcoded secret detector
Bu script tüm dosyalarda potansiyel güvenlik açıklarını tarar
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple

class SecurityChecker:
    """Güvenlik açığı tarayıcısı"""
    
    def __init__(self):
        self.patterns = {
            'aws_access_key': r'AKIA[0-9A-Z]{16}',
            'aws_secret_key': r'[A-Za-z0-9/+=]{40}',
            'google_api_key': r'AIzaSy[0-9A-Za-z_-]{33}',
            'openai_api_key': r'sk-[0-9A-Za-z]{48}',
            'generic_api_key': r'api[_-]?key["\']?\s*[:=]\s*["\'][^"\']{20,}["\']',
            'generic_secret': r'secret[_-]?key["\']?\s*[:=]\s*["\'][^"\']{20,}["\']',
            'generic_token': r'token["\']?\s*[:=]\s*["\'][^"\']{20,}["\']',
            'generic_password': r'password["\']?\s*[:=]\s*["\'][^"\']{8,}["\']',
            'base64_encoded': r'[A-Za-z0-9+/]{50,}={0,2}',
            'hardcoded_url_with_auth': r'https?://[^:]+:[^@]+@[^/]+',
            'jwt_token': r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',
        }
        
        self.exclude_patterns = [
            r'your-.*-here',
            r'your-.*-change',
            r'placeholder',
            r'example',
            r'test',
            r'demo',
            r'sample',
            r'localhost',
            r'127\.0\.0\.1',
            r'Environment=PATH=',
            r'ExecStart=',
            r'========',
            r'https?://[^/]*\.com',  # Generic domain URLs
            r'generativelanguage\.googleapis\.com',  # Google API URLs
        ]
        
        self.exclude_files = {
            '.git', '__pycache__', 'node_modules', '.vscode', '.idea',
            'venv', 'env', '.env.example', 'security_check.py', 'security_report.json'
        }
        
        self.exclude_extensions = {
            '.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico',
            '.mp3', '.mp4', '.avi', '.mov', '.wav',
            '.zip', '.tar', '.gz', '.rar', '.7z'
        }
    
    def is_excluded_content(self, content: str) -> bool:
        """İçeriğin güvenli placeholder olup olmadığını kontrol et"""
        content_lower = content.lower()
        return any(re.search(pattern, content_lower) for pattern in self.exclude_patterns)
    
    def scan_file(self, file_path: Path) -> List[Dict]:
        """Tek dosyayı tara"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            for pattern_name, pattern in self.patterns.items():
                matches = re.finditer(pattern, content, re.IGNORECASE)
                
                for match in matches:
                    matched_text = match.group()
                    
                    # Güvenli placeholder'ları atla
                    if self.is_excluded_content(matched_text):
                        continue
                    
                    # Satır numarasını bul
                    line_num = content[:match.start()].count('\n') + 1
                    
                    # Bağlamı al
                    lines = content.split('\n')
                    context_start = max(0, line_num - 2)
                    context_end = min(len(lines), line_num + 1)
                    context = '\n'.join(lines[context_start:context_end])
                    
                    findings.append({
                        'file': str(file_path),
                        'line': line_num,
                        'pattern': pattern_name,
                        'match': matched_text[:50] + '...' if len(matched_text) > 50 else matched_text,
                        'context': context,
                        'severity': self.get_severity(pattern_name)
                    })
                    
        except Exception as e:
            print(f"⚠️  Error scanning {file_path}: {e}")
            
        return findings
    
    def get_severity(self, pattern_name: str) -> str:
        """Pattern'e göre önem derecesi belirle"""
        high_risk = ['aws_access_key', 'aws_secret_key', 'google_api_key', 'openai_api_key']
        medium_risk = ['generic_api_key', 'generic_secret', 'jwt_token']
        
        if pattern_name in high_risk:
            return 'HIGH'
        elif pattern_name in medium_risk:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def scan_directory(self, directory: Path = None) -> List[Dict]:
        """Dizini tarayarak tüm dosyaları kontrol et"""
        if directory is None:
            directory = Path('.')
            
        all_findings = []
        
        for root, dirs, files in os.walk(directory):
            # Exclude directories
            dirs[:] = [d for d in dirs if d not in self.exclude_files]
            
            for file in files:
                file_path = Path(root) / file
                
                # Skip excluded files and extensions
                if (file in self.exclude_files or 
                    file_path.suffix in self.exclude_extensions or
                    any(excluded in str(file_path) for excluded in self.exclude_files)):
                    continue
                
                findings = self.scan_file(file_path)
                all_findings.extend(findings)
        
        return all_findings
    
    def generate_report(self, findings: List[Dict]) -> str:
        """Rapor oluştur"""
        if not findings:
            return "🎉 No security issues found!"
        
        report = f"🚨 SECURITY SCAN REPORT - {len(findings)} issues found\n"
        report += "=" * 60 + "\n\n"
        
        # Severity'ye göre grupla
        by_severity = {'HIGH': [], 'MEDIUM': [], 'LOW': []}
        for finding in findings:
            by_severity[finding['severity']].append(finding)
        
        for severity in ['HIGH', 'MEDIUM', 'LOW']:
            if by_severity[severity]:
                report += f"🔴 {severity} RISK ({len(by_severity[severity])} issues):\n"
                report += "-" * 40 + "\n"
                
                for finding in by_severity[severity]:
                    report += f"File: {finding['file']}:{finding['line']}\n"
                    report += f"Pattern: {finding['pattern']}\n"
                    report += f"Match: {finding['match']}\n"
                    report += f"Context:\n{finding['context']}\n"
                    report += "-" * 40 + "\n"
                
                report += "\n"
        
        return report
    
    def save_report(self, findings: List[Dict], filename: str = 'security_report.json'):
        """Raporu JSON olarak kaydet"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(findings, f, indent=2, ensure_ascii=False)
        print(f"📄 Detailed report saved to {filename}")

def main():
    """Ana fonksiyon"""
    print("🔍 Starting security scan...")
    
    checker = SecurityChecker()
    findings = checker.scan_directory()
    
    # Konsol raporu
    report = checker.generate_report(findings)
    print(report)
    
    # JSON raporu
    if findings:
        checker.save_report(findings)
        print("\n⚠️  SECURITY ISSUES FOUND! Please review and fix immediately.")
        return 1
    else:
        print("✅ Security scan completed successfully - no issues found!")
        return 0

if __name__ == '__main__':
    exit(main())