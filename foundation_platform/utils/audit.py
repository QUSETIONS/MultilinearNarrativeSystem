import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List
from foundation_platform.core.extractor import AssetExtractor

class AssetAuditor:
    def __init__(self, json_path, root_dir):
        self.extractor = AssetExtractor(json_path)
        self.root_dir = root_dir

    def audit(self):
        """
        Performs a full audit of assets defined in JSON vs actual files.
        """
        all_assets = self.extractor.extract_assets()
        report: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_defined': 0,
                'found': 0,
                'missing': 0,
                'types': {}
            },
            'details': []
        }

        summary = report['summary']
        types_summary = summary['types']

        for asset_type, items in all_assets.items():
            types_summary[asset_type] = {'total': 0, 'found': 0, 'missing': 0}
            for path, desc in items.items():
                summary['total_defined'] += 1
                types_summary[asset_type]['total'] += 1
                
                clean_path = path.replace('/', os.sep)
                full_path = os.path.join(self.root_dir, clean_path)
                exists = os.path.exists(full_path)
                
                status = 'FOUND' if exists else 'MISSING'
                if exists:
                    summary['found'] += 1
                    types_summary[asset_type]['found'] += 1
                else:
                    summary['missing'] += 1
                    types_summary[asset_type]['missing'] += 1
                
                report['details'].append({
                    'type': asset_type,
                    'path': path,
                    'description': desc,
                    'status': status,
                    'full_path': full_path
                })
        
        return report

    def generate_markdown_report(self, report, output_path):
        """
        Generates a human-readable markdown report.
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# 📦 Asset Integrity Audit Report\n\n")
            f.write(f"**Generated at:** {report['timestamp']}\n\n")
            
            f.write("## 📊 Summary\n\n")
            f.write(f"- **Total Defined Assets:** {report['summary']['total_defined']}\n")
            f.write(f"- **Found on Disk:** {report['summary']['found']}\n")
            f.write(f"- **Missing Assets:** {report['summary']['missing']}\n\n")
            
            f.write("### Breakdown by Type\n\n")
            f.write("| Asset Type | Total | Found | Missing | Progress |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- |\n")
            for a_type, stats in report['summary']['types'].items():
                progress = (stats['found'] / stats['total'] * 100) if stats['total'] > 0 else 0
                f.write(f"| {a_type} | {stats['total']} | {stats['found']} | {stats['missing']} | {progress:.1f}% |\n")
            
            f.write("\n## 🔍 Top Missing Assets\n\n")
            f.write("| Type | Path | Description |\n")
            f.write("| :--- | :--- | :--- |\n")
            missing_items = [d for d in report['details'] if d['status'] == 'MISSING']
            for item in missing_items[:20]: # Show top 20
                f.write(f"| {item['type']} | `{item['path']}` | {item['description']} |\n")
            
            if len(missing_items) > 20:
                f.write(f"\n*...and {len(missing_items) - 20} more.*")

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    json_path = os.path.join(project_root, "东方快车谋杀案修复版.json")
    report_md_path = os.path.join(project_root, "asset_audit_report.md")
    report_json_path = os.path.join(project_root, "editor-web", "public", "audit_results.json")
    
    auditor = AssetAuditor(json_path, project_root)
    report_data = auditor.audit()
    
    # Generate Markdown for humans
    auditor.generate_markdown_report(report_data, report_md_path)
    
    # Generate JSON for the Workstation UI
    os.makedirs(os.path.dirname(report_json_path), exist_ok=True)
    with open(report_json_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
        
    print(f"Audit complete!")
    print(f" - Markdown: {report_md_path}")
    print(f" - JSON: {report_json_path}")
