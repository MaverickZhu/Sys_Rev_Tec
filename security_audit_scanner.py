#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全审计扫描器
执行全面的安全性检查，包括代码安全扫描、依赖漏洞检测、配置安全检查等
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecurityAuditScanner:
    """安全审计扫描器类"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.results = {
            "scan_time": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "security_checks": {},
            "vulnerabilities": [],
            "recommendations": [],
            "overall_score": 0,
            "risk_level": "UNKNOWN"
        }
        
    def run_bandit_scan(self) -> Dict[str, Any]:
        """运行Bandit安全扫描"""
        logger.info("运行Bandit安全扫描...")
        try:
            cmd = ["bandit", "-r", ".", "-f", "json", "-o", "bandit_report.json"]
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            
            if os.path.exists(self.project_root / "bandit_report.json"):
                with open(self.project_root / "bandit_report.json", 'r', encoding='utf-8') as f:
                    bandit_data = json.load(f)
                    
                return {
                    "status": "completed",
                    "issues_found": len(bandit_data.get("results", [])),
                    "high_severity": len([r for r in bandit_data.get("results", []) if r.get("issue_severity") == "HIGH"]),
                    "medium_severity": len([r for r in bandit_data.get("results", []) if r.get("issue_severity") == "MEDIUM"]),
                    "low_severity": len([r for r in bandit_data.get("results", []) if r.get("issue_severity") == "LOW"]),
                    "details": bandit_data.get("results", [])[:10]  # 只保留前10个问题
                }
            else:
                return {"status": "failed", "error": "Bandit报告文件未生成"}
                
        except Exception as e:
            logger.error(f"Bandit扫描失败: {e}")
            return {"status": "error", "error": str(e)}
    
    def check_dependency_vulnerabilities(self) -> Dict[str, Any]:
        """检查依赖包漏洞"""
        logger.info("检查依赖包漏洞...")
        try:
            # 检查requirements文件
            req_files = ["requirements.txt", "requirements-base.txt", "requirements-dev.txt"]
            vulnerabilities = []
            
            for req_file in req_files:
                req_path = self.project_root / req_file
                if req_path.exists():
                    # 模拟漏洞检查（实际应该使用safety或其他工具）
                    with open(req_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # 简单的版本检查逻辑
                            if '==' in line:
                                package, version = line.split('==')[0], line.split('==')[1]
                                # 模拟已知漏洞检查
                                if self._check_known_vulnerabilities(package, version):
                                    vulnerabilities.append({
                                        "package": package,
                                        "version": version,
                                        "file": req_file,
                                        "severity": "MEDIUM",
                                        "description": f"Package {package} version {version} may have known vulnerabilities"
                                    })
            
            return {
                "status": "completed",
                "vulnerabilities_found": len(vulnerabilities),
                "details": vulnerabilities
            }
            
        except Exception as e:
            logger.error(f"依赖漏洞检查失败: {e}")
            return {"status": "error", "error": str(e)}
    
    def _check_known_vulnerabilities(self, package: str, version: str) -> bool:
        """检查已知漏洞（简化版本）"""
        # 这里应该连接到漏洞数据库，这里只是模拟
        known_vulnerable = {
            "requests": ["2.25.0", "2.25.1"],
            "urllib3": ["1.26.0", "1.26.1"],
            "jinja2": ["2.10.0", "2.10.1"]
        }
        
        return package in known_vulnerable and version in known_vulnerable[package]
    
    def check_file_permissions(self) -> Dict[str, Any]:
        """检查文件权限"""
        logger.info("检查文件权限...")
        try:
            sensitive_files = []
            config_files = []
            
            # 查找敏感文件
            for root, dirs, files in os.walk(self.project_root):
                for file in files:
                    file_path = Path(root) / file
                    
                    # 检查敏感文件
                    if any(pattern in file.lower() for pattern in ['password', 'secret', 'key', 'token', '.env']):
                        sensitive_files.append({
                            "file": str(file_path.relative_to(self.project_root)),
                            "type": "sensitive",
                            "risk": "HIGH"
                        })
                    
                    # 检查配置文件
                    if file.endswith(('.conf', '.config', '.ini', '.yaml', '.yml', '.json')):
                        config_files.append({
                            "file": str(file_path.relative_to(self.project_root)),
                            "type": "config",
                            "risk": "MEDIUM"
                        })
            
            return {
                "status": "completed",
                "sensitive_files": len(sensitive_files),
                "config_files": len(config_files),
                "details": {
                    "sensitive": sensitive_files[:5],  # 只显示前5个
                    "config": config_files[:5]
                }
            }
            
        except Exception as e:
            logger.error(f"文件权限检查失败: {e}")
            return {"status": "error", "error": str(e)}
    
    def check_code_patterns(self) -> Dict[str, Any]:
        """检查代码中的安全模式"""
        logger.info("检查代码安全模式...")
        try:
            security_issues = []
            
            # 定义危险模式
            dangerous_patterns = [
                (r'eval\(', 'Use of eval() function', 'HIGH'),
                (r'exec\(', 'Use of exec() function', 'HIGH'),
                (r'os\.system\(', 'Use of os.system()', 'HIGH'),
                (r'subprocess\.call\(.*shell=True', 'Shell injection risk', 'HIGH'),
                (r'password\s*=\s*["\'][^"\']', 'Hardcoded password', 'MEDIUM'),
                (r'secret\s*=\s*["\'][^"\']', 'Hardcoded secret', 'MEDIUM'),
                (r'api_key\s*=\s*["\'][^"\']', 'Hardcoded API key', 'MEDIUM')
            ]
            
            import re
            
            # 扫描Python文件
            for root, dirs, files in os.walk(self.project_root):
                # 跳过某些目录
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv']]
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = Path(root) / file
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                
                            for pattern, description, severity in dangerous_patterns:
                                matches = re.finditer(pattern, content, re.IGNORECASE)
                                for match in matches:
                                    line_num = content[:match.start()].count('\n') + 1
                                    security_issues.append({
                                        "file": str(file_path.relative_to(self.project_root)),
                                        "line": line_num,
                                        "pattern": pattern,
                                        "description": description,
                                        "severity": severity,
                                        "code_snippet": content[max(0, match.start()-50):match.end()+50]
                                    })
                        except Exception as e:
                            logger.warning(f"无法读取文件 {file_path}: {e}")
            
            return {
                "status": "completed",
                "issues_found": len(security_issues),
                "high_severity": len([i for i in security_issues if i['severity'] == 'HIGH']),
                "medium_severity": len([i for i in security_issues if i['severity'] == 'MEDIUM']),
                "details": security_issues[:10]  # 只显示前10个问题
            }
            
        except Exception as e:
            logger.error(f"代码模式检查失败: {e}")
            return {"status": "error", "error": str(e)}
    
    def generate_recommendations(self) -> List[str]:
        """生成安全建议"""
        recommendations = []
        
        # 基于检查结果生成建议
        if self.results["security_checks"].get("bandit", {}).get("high_severity", 0) > 0:
            recommendations.append("修复Bandit检测到的高严重性安全问题")
        
        if self.results["security_checks"].get("dependencies", {}).get("vulnerabilities_found", 0) > 0:
            recommendations.append("更新存在漏洞的依赖包到安全版本")
        
        if self.results["security_checks"].get("file_permissions", {}).get("sensitive_files", 0) > 0:
            recommendations.append("检查敏感文件的访问权限和存储方式")
        
        if self.results["security_checks"].get("code_patterns", {}).get("high_severity", 0) > 0:
            recommendations.append("修复代码中的高风险安全模式")
        
        # 通用建议
        recommendations.extend([
            "定期更新所有依赖包到最新安全版本",
            "实施代码审查流程，重点关注安全问题",
            "配置自动化安全扫描工具",
            "建立安全事件响应流程",
            "定期进行渗透测试和安全评估"
        ])
        
        return recommendations
    
    def calculate_security_score(self) -> int:
        """计算安全评分"""
        score = 100
        
        # 根据各项检查结果扣分
        bandit_check = self.results["security_checks"].get("bandit", {})
        score -= bandit_check.get("high_severity", 0) * 15
        score -= bandit_check.get("medium_severity", 0) * 8
        score -= bandit_check.get("low_severity", 0) * 3
        
        deps_check = self.results["security_checks"].get("dependencies", {})
        score -= deps_check.get("vulnerabilities_found", 0) * 10
        
        file_check = self.results["security_checks"].get("file_permissions", {})
        score -= file_check.get("sensitive_files", 0) * 12
        
        code_check = self.results["security_checks"].get("code_patterns", {})
        score -= code_check.get("high_severity", 0) * 20
        score -= code_check.get("medium_severity", 0) * 10
        
        return max(0, score)
    
    def determine_risk_level(self, score: int) -> str:
        """确定风险等级"""
        if score >= 90:
            return "LOW"
        elif score >= 70:
            return "MEDIUM"
        elif score >= 50:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def run_full_scan(self) -> Dict[str, Any]:
        """运行完整的安全扫描"""
        logger.info("开始安全审计扫描...")
        
        # 执行各项检查
        self.results["security_checks"]["bandit"] = self.run_bandit_scan()
        self.results["security_checks"]["dependencies"] = self.check_dependency_vulnerabilities()
        self.results["security_checks"]["file_permissions"] = self.check_file_permissions()
        self.results["security_checks"]["code_patterns"] = self.check_code_patterns()
        
        # 生成建议和评分
        self.results["recommendations"] = self.generate_recommendations()
        self.results["overall_score"] = self.calculate_security_score()
        self.results["risk_level"] = self.determine_risk_level(self.results["overall_score"])
        
        # 保存报告
        report_file = self.project_root / "security_audit_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"安全审计完成，报告已保存到: {report_file}")
        return self.results

def main():
    """主函数"""
    print("🔒 安全审计扫描器")
    print("=" * 50)
    
    scanner = SecurityAuditScanner()
    results = scanner.run_full_scan()
    
    # 打印摘要
    print(f"\n📊 安全审计摘要:")
    print(f"总体评分: {results['overall_score']}/100")
    print(f"风险等级: {results['risk_level']}")
    print(f"扫描时间: {results['scan_time']}")
    
    print(f"\n🔍 检查结果:")
    for check_name, check_result in results['security_checks'].items():
        status = check_result.get('status', 'unknown')
        print(f"  {check_name}: {status}")
        
        if check_name == 'bandit':
            issues = check_result.get('issues_found', 0)
            high = check_result.get('high_severity', 0)
            print(f"    发现 {issues} 个问题 (高危: {high})")
        elif check_name == 'dependencies':
            vulns = check_result.get('vulnerabilities_found', 0)
            print(f"    发现 {vulns} 个依赖漏洞")
        elif check_name == 'file_permissions':
            sensitive = check_result.get('sensitive_files', 0)
            print(f"    发现 {sensitive} 个敏感文件")
        elif check_name == 'code_patterns':
            issues = check_result.get('issues_found', 0)
            high = check_result.get('high_severity', 0)
            print(f"    发现 {issues} 个代码安全问题 (高危: {high})")
    
    print(f"\n💡 安全建议 (前5条):")
    for i, rec in enumerate(results['recommendations'][:5], 1):
        print(f"  {i}. {rec}")
    
    print(f"\n📄 详细报告已保存到: security_audit_report.json")
    
    # 返回退出码
    if results['risk_level'] in ['CRITICAL', 'HIGH']:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())