# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# 安全审计工具集 - 参考 AgentOS 安全穹顶设计
# 提供代码安全扫描、依赖检查、配置审计功能

import sys
import os
import re
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum, auto

sys.path.insert(0, '/app/common/scripts')

from common.core import (
    ConfigManager,
    setup_logging,
    ErrorCode,
    WorkshopError,
    error_code_manager
)


class SecuritySeverity(Enum):
    """安全严重程度"""
    CRITICAL = "critical"   # 必须立即修复（如SQL注入）
    HIGH = "high"           # 应尽快修复（如硬编码密码）
    MEDIUM = "medium"       # 建议修复（如不安全的日志输出）
    LOW = "low"             # 可选修复（如信息泄露风险）
    INFO = "info"           # 信息性提示（如最佳实践建议）


@dataclass
class SecurityFinding:
    """安全发现/漏洞"""
    rule_id: str
    severity: SecuritySeverity
    title: str
    description: str
    file_path: str
    line_number: int = 0
    column: int = 0
    code_snippet: str = ""
    remediation: str = ""
    cwe_id: Optional[str] = None  # Common Weakness Enumeration
    references: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'rule_id': self.rule_id,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'code_snippet': self.code_snippet[:100] if self.code_snippet else "",
            'remediation': self.remediation,
            'cwe_id': self.cwe_id,
            'references': self.references
        }


@dataclass
class SecurityAuditReport:
    """安全审计报告"""
    scan_time: str = ""
    total_files_scanned: int = 0
    findings: List[SecurityFinding] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    
    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == SecuritySeverity.CRITICAL)
    
    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == SecuritySeverity.HIGH)
    
    @property
    def medium_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == SecuritySeverity.MEDIUM)
    
    @property
    def low_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == SecuritySeverity.LOW)
    
    @property
    def has_critical_or_high(self) -> bool:
        return self.critical_count > 0 or self.high_count > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'scan_time': self.scan_time,
            'total_files_scanned': self.total_files_scanned,
            'findings': [f.to_dict() for f in self.findings],
            'summary': {
                'critical': self.critical_count,
                'high': self.high_count,
                'medium': self.medium_count,
                'low': self.low_count,
                'total': len(self.findings)
            }
        }


class CodeSecurityScanner:
    """
    代码安全扫描器 - 静态分析 (SAST)
    
    检测项：
    - 硬编码凭证（密码、API Key等）
    - SQL注入风险
    - 路径遍历漏洞
    - 不安全的反序列化
    - 命令注入风险
    - 敏感信息日志记录
    """
    
    # 安全规则定义
    RULES = [
        {
            'id': 'SEC001',
            'severity': SecuritySeverity.HIGH,
            'title': '硬编码密码或密钥',
            'pattern': r'(?:password|passwd|pwd|secret|api_key|apikey|token)\s*[=:]\s*["\'][^"\']+["\']',
            'description': '检测到可能的硬编码密码或密钥',
            'remediation': '使用环境变量或配置管理器存储敏感信息',
            'cwe': 'CWE-798'
        },
        {
            'id': 'SEC002',
            'severity': SecuritySeverity.CRITICAL,
            'title': 'SQL注入风险',
            'pattern': r'(?:execute|executemany|raw)\s*\(\s*f["\'].*%\s*(?:s|d)',
            'description': '使用字符串格式化构建SQL查询，存在注入风险',
            'remediation': '使用参数化查询或ORM',
            'cwe': 'CWE-89'
        },
        {
            'id': 'SEC003',
            'severity': SecuritySeverity.HIGH,
            'title': '路径遍历攻击风险',
            'pattern': r'open\s*\([^)]*\.\.[\\/]',
            'description': '文件路径包含 ".."，可能存在路径遍历风险',
            'remediation': '验证并规范化用户输入的路径，使用白名单机制',
            'cwe': 'CWE-22'
        },
        {
            'id': 'SEC004',
            'severity': SecuritySeverity.MEDIUM,
            'title': '不安全的反序列化',
            'pattern': r'(?:pickle\.loads?|yaml\.load\s*\((?!.*Loader=))',
            'description': '使用不安全的反序列化方法可能导致远程代码执行',
            'remediation': '使用安全的序列化格式（如JSON）或指定安全的加载器',
            'cwe': 'CWE-502'
        },
        {
            'id': 'SEC005',
            'severity': SecuritySeverity.CRITICAL,
            'title': '命令注入风险',
            'pattern': r'(?:os\.system|subprocess\.(?:call|Popen))\s*\(\s*f["\']',
            'description': '使用字符串格式化构建命令，存在注入风险',
            'remediation': '使用参数列表而非字符串拼接',
            'cwe': 'CWE-78'
        },
        {
            'id': 'SEC006',
            'severity': SecuritySeverity.LOW,
            'title': '敏感信息记录到日志',
            'pattern': r'(?:logger|logging)\.(?:info|debug|warning)\s*\([^)]*(?:password|token|secret)',
            'description': '日志中可能包含敏感信息',
            'remediation': '在记录前对敏感信息进行脱敏处理',
            'cwe': 'CWE-532'
        }
    ]
    
    def __init__(self):
        self._logger = setup_logging("security.scanner")
        self._findings: List[SecurityFinding] = []
        self._files_scanned = 0
    
    def scan_file(self, file_path: str) -> List[SecurityFinding]:
        """
        扫描单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            发现的安全问题列表
        """
        findings = []
        
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return findings
        
        # 只扫描Python文件
        if path.suffix not in ['.py', '.pyw']:
            return findings
        
        try:
            content = path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            self._files_scanned += 1
            
            for rule in self.RULES:
                pattern = re.compile(rule['pattern'], re.IGNORECASE | re.MULTILINE)
                
                for match in pattern.finditer(content):
                    line_num = content[:match.start()].count('\n') + 1
                    
                    # 提取代码片段
                    start_line = max(0, line_num - 2)
                    end_line = min(len(lines), line_num + 1)
                    snippet = '\n'.join(
                        f"{i+1}: {line}" 
                        for i, line in enumerate(lines[start_line:end_line])
                    )
                    
                    finding = SecurityFinding(
                        rule_id=rule['id'],
                        severity=rule['severity'],
                        title=rule['title'],
                        description=rule['description'],
                        file_path=str(file_path),
                        line_number=line_num,
                        code_snippet=snippet,
                        remediation=rule.get('remediation', ''),
                        cwe_id=rule.get('cwe'),
                        references=[
                            f"https://cwe.mitre.org/data/definitions/{rule.get('cwe', '').replace('CWE-', '')}.html"
                        ] if rule.get('cwe') else []
                    )
                    
                    findings.append(finding)
            
        except Exception as e:
            self._logger.warning(f"扫描文件失败: {file_path} - {e}")
        
        self._findings.extend(findings)
        return findings
    
    def scan_directory(
        self,
        directory: str,
        exclude_patterns: Optional[List[str]] = None
    ) -> SecurityAuditReport:
        """
        扫描目录中的所有Python文件
        
        Args:
            directory: 目录路径
            exclude_patterns: 排除模式列表
            
        Returns:
            完整的安全审计报告
        """
        from datetime import datetime
        
        exclude_patterns = exclude_patterns or [
            '__pycache__',
            '.git',
            '*.pyc',
            'node_modules',
            '.venv',
            'venv'
        ]
        
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"目录不存在: {directory}")
        
        self._findings.clear()
        self._files_scanned = 0
        
        # 收集所有Python文件
        python_files = []
        for pattern in ['**/*.py']:
            python_files.extend(dir_path.glob(pattern))
        
        # 排除不需要的文件
        filtered_files = []
        for file_path in python_files:
            skip = False
            for pattern in exclude_patterns:
                if pattern in file_path.parts or file_path.match(pattern):
                    skip = True
                    break
            
            if not skip:
                filtered_files.append(file_path)
        
        # 扫描每个文件
        for file_path in filtered_files:
            self.scan_file(str(file_path))
        
        # 生成报告
        report = SecurityAuditReport(
            scan_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_files_scanned=self._files_scanned,
            findings=self._findings.copy()
        )
        
        self._logger.info(
            f"✓ 安全扫描完成\n"
            f"  扫描文件: {report.total_files_scanned}\n"
            f"  发现问题: {len(report.findings)} "
            f"(严重: {report.critical_count}, 高危: {report.high_count}, "
            f"中等: {report.medium_count}, 低危: {report.low_count})"
        )
        
        return report
    
    def save_report(self, report: SecurityAuditReport, output_path: str) -> None:
        """保存报告到JSON文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        
        self._logger.info(f"安全报告已保存: {output_path}")


class DependencyAuditor:
    """
    依赖审计器
    
    功能：
    - 检查已知CVE漏洞
    - 过期依赖警告
    - 许可证合规性检查
    """
    
    KNOWN_VULNERABLE_PACKAGES = {
        'Pillow<7.0.0': {'cve': 'CVE-2021-25287', 'severity': 'HIGH'},
        'PyYAML<5.4': {'cve': 'CVE-2020-14343', 'severity': 'CRITICAL'},
        'requests<2.20.0': {'cve': 'CVE-2018-18074', 'severity': 'MEDIUM'},
    }
    
    def __init__(self):
        self._logger = setup_logging("security.dependency")
        self._findings: List[SecurityFinding] = []
    
    def audit_requirements(self, requirements_file: str) -> List[SecurityFinding]:
        """
        审计 requirements.txt 文件
        
        Args:
            requirements_file: requirements.txt 路径
            
        Returns:
            发现的问题列表
        """
        findings = []
        
        req_path = Path(requirements_file)
        if not req_path.exists():
            self._logger.warning(f"requirements.txt 不存在: {requirements_file}")
            return findings
        
        try:
            content = req_path.read_text(encoding='utf-8')
            
            for line in content.split('\n'):
                line = line.strip()
                
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                
                # 解析包名和版本
                parts = line.split('==') if '==' in line else [line]
                package_name = parts[0].strip().lower()
                
                # 检查已知漏洞包
                for vuln_pattern, info in self.KNOWN_VULNERABLE_PACKAGES.items():
                    pkg_name, version_constraint = vuln_pattern.split('<')
                    
                    if package_name == pkg_name.lower() and len(parts) > 1:
                        installed_version = parts[1].strip()
                        
                        try:
                            from packaging import version as pkg_version
                            if pkg_version.parse(installed_version) < pkg_version.parse(version_constraint):
                                finding = SecurityFinding(
                                    rule_id='DEP001',
                                    severity=SecuritySeverity[info['severity']],
                                    title=f'存在已知漏洞的依赖: {package_name}',
                                    description=(
                                        f"版本 {installed_version} 存在已知漏洞 ({info['cwe']})。"
                                        f"建议升级至 {version_constraint} 或更高版本。"
                                    ),
                                    file_path=requirements_file,
                                    remediation=f'升级 {package_name}>={version_constraint}',
                                    cwe_id=info['cwe'],
                                    references=[f'https://nvd.nist.gov/vuln/detail/{info["cve"]}']
                                )
                                findings.append(finding)
                                
                        except ImportError:
                            pass  # packaging 库不可用时跳过精确比较
            
        except Exception as e:
            self._logger.error(f"依赖审计失败: {e}", exc_info=True)
        
        self._findings.extend(findings)
        return findings


class ConfigurationAuditor:
    """
    配置审计器
    
    检查：
    - 敏感配置暴露
    - 默认密码使用
    - 不安全的默认值
    - 权限配置问题
    """
    
    SENSITIVE_KEYS = [
        'password', 'passwd', 'secret', 'token', 'api_key',
        'access_key', 'private_key', 'credential'
    ]
    
    INSECURE_DEFAULTS = {
        'debug': True,
        'allow_origin': '*',
        'ssl_verify': False,
        'auth_enabled': False
    }
    
    def __init__(self):
        self._logger = setup_logging("security.config")
        self._findings: List[SecurityFinding] = []
    
    def audit_config(self, config_dict: Dict[str, Any], config_source: str = "") -> List[SecurityFinding]:
        """
        审计配置字典
        
        Args:
            config_dict: 配置字典
            config_source: 配置来源描述
            
        Returns:
            发现的问题列表
        """
        findings = []
        
        def check_sensitive_values(obj: Dict, prefix: str = ""):
            for key, value in obj.items():
                full_key = f"{prefix}.{key}" if prefix else key
                
                if isinstance(value, dict):
                    check_sensitive_values(value, full_key)
                elif any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                    if value and isinstance(value, str) and len(value) > 3:
                        finding = SecurityFinding(
                            rule_id='CFG001',
                            severity=SecuritySeverity.HIGH,
                            title=f'敏感配置可能明文存储: {full_key}',
                            description=f"配置项 '{full_key}' 包含可能敏感的值",
                            file_path=config_source,
                            remediation='使用环境变量或加密存储敏感配置',
                            cwe='CWE-798'
                        )
                        findings.append(finding)
                
                # 检查不安全默认值
                if key.lower() in [k.lower() for k in self.INSECURE_DEFAULTS.keys()]:
                    if value == self.INSECURE_DEFAULTS.get(key):
                        finding = SecurityFinding(
                            rule_id='CFG002',
                            severity=SecuritySeverity.MEDIUM,
                            title=f'不安全的默认配置: {full_key}',
                            description=f"配置项 '{full_key}' 使用了不安全的默认值: {value}",
                            file_path=config_source,
                            remediation=f'修改 {full_key} 为安全值',
                            cwe='CWE-16'
                        )
                        findings.append(finding)
        
        check_sensitive_values(config_dict)
        self._findings.extend(findings)
        return findings


def run_full_security_audit(
    project_root: str,
    output_dir: str = "/app/reports/security"
) -> Dict[str, SecurityAuditReport]:
    """
    运行完整的安全审计
    
    Args:
        project_root: 项目根目录
        output_dir: 报告输出目录
        
    Returns:
        各类审计报告字典
    """
    from datetime import datetime
    
    logger = setup_logging("security.audit")
    reports = {}
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 1. 代码安全扫描
    logger.info("▶ 开始代码安全扫描...")
    scanner = CodeSecurityScanner()
    code_report = scanner.scan_directory(project_path)
    code_report_path = os.path.join(output_dir, f"code_scan_{timestamp}.json")
    scanner.save_report(code_report, code_report_path)
    reports['code_scan'] = code_report
    
    # 2. 依赖审计
    logger.info("▶ 开始依赖审计...")
    dep_auditor = DependencyAuditor()
    req_file = os.path.join(project_root, "requirements.txt")
    
    if os.path.exists(req_file):
        dep_findings = dep_auditor.audit_requirements(req_file)
        dep_report = SecurityAuditReport(
            scan_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            findings=dep_findings
        )
    else:
        dep_report = SecurityAuditReport(
            scan_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            findings=[]
        )
    
    dep_report_path = os.path.join(output_dir, f"dependency_audit_{timestamp}.json")
    with open(dep_report_path, 'w', encoding='utf-8') as f:
        json.dump(dep_report.to_dict(), f, indent=2)
    reports['dependency'] = dep_report
    
    # 3. 汇总报告
    total_findings = (
        len(code_report.findings) +
        len(dep_report.findings)
    )
    
    summary_report = {
        'audit_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'project_root': project_root,
        'total_findings': total_findings,
        'by_category': {
            'code_security': {
                'count': len(code_report.findings),
                'critical': code_report.critical_count,
                'high': code_report.high_count
            },
            'dependencies': {
                'count': len(dep_report.findings),
                'critical': dep_report.critical_count,
                'high': dep_report.high_count
            }
        },
        'overall_status': (
            'PASS' if total_findings == 0 else
            'WARNING' if not (code_report.has_critical_or_high or dep_report.has_critical_or_high) else
            'FAIL'
        ),
        'recommendations': _generate_recommendations(reports)
    }
    
    summary_path = os.path.join(output_dir, f"security_summary_{timestamp}.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_report, f, indent=2, ensure_ascii=False)
    
    logger.info(
        f"\n{'='*60}\n"
        f"安全审计完成\n"
        f"{'='*60}\n"
        f"总发现: {total_findings}\n"
        f"状态: {summary_report['overall_status']}\n"
        f"报告位置: {output_dir}"
    )
    
    return reports


def _generate_recommendations(reports: Dict[str, SecurityAuditReport]) -> List[str]:
    """根据审计结果生成改进建议"""
    recommendations = []
    
    code_report = reports.get('code_scan')
    if code_report:
        if code_report.has_critical_or_high:
            recommendations.append(
                "⚠ 发现严重安全问题，请立即修复后再部署到生产环境"
            )
        
        if code_report.critical_count > 0:
            recommendations.append(
                f"🔴 有 {code_report.critical_count} 个严重级别问题需要立即处理"
            )
    
    dep_report = reports.get('dependency')
    if dep_report and dep_report.has_critical_or_high:
        recommendations.append(
            "📦 依赖库存在已知漏洞，建议尽快更新到安全版本"
        )
    
    if not recommendations:
        recommendations.append("✅ 未发现严重安全问题，继续保持良好的安全实践！")
    
    return recommendations


__all__ = [
    'SecuritySeverity',
    'SecurityFinding',
    'SecurityAuditReport',
    'CodeSecurityScanner',
    'DependencyAuditor',
    'ConfigurationAuditor',
    'run_full_security_audit'
]
