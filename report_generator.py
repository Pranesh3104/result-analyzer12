from typing import Dict, Any
import pandas as pd

class ReportGenerator:
    """
    Generates comprehensive reports from analysis results
    """
    
    def __init__(self, decimal_places: int = 2):
        self.decimal_places = decimal_places
    
    def generate_report(self, analysis_results: Dict[str, Any], show_student_ids: bool = False) -> str:
        """
        Generate a comprehensive markdown report
        
        Args:
            analysis_results: Dictionary containing analysis results
            show_student_ids: Whether to show student IDs or anonymize them
            
        Returns:
            Formatted markdown report string
        """
        report = []
        
        # Header
        report.append("# 📊 Student Examination Results Analysis Report")
        report.append("=" * 60)
        report.append("")
        
        # Executive Summary
        report.append("## 📋 Executive Summary")
        report.append("")
        report.append(f"**Total Students Analyzed:** {analysis_results['total_students']}")
        report.append(f"**Total Subjects:** {analysis_results['total_subjects']}")
        report.append(f"**Department Pass Rate:** {analysis_results['department_pass_rate']:.{self.decimal_places}f}%")
        report.append(f"**Pass Criteria:** {analysis_results['pass_percentage']}% minimum per subject")
        report.append("")
        
        # Key Findings
        report.append("## 🔍 Key Findings")
        report.append("")
        
        # Department Performance
        report.append("### Department Performance")
        report.append(f"- **{analysis_results['students_passed_all']}** students passed all subjects")
        report.append(f"- **{analysis_results['students_failed_any']}** students failed at least one subject")
        report.append(f"- **Average score across all subjects:** {analysis_results['average_score']:.{self.decimal_places}f}%")
        report.append("")
        
        # Overall Top Performer
        if analysis_results['overall_top_student']:
            top_student = analysis_results['overall_top_student']
            student_name = top_student['name']
            if not show_student_ids:
                student_name = f"Student_{hash(str(student_name)) % 10000:04d}"
            
            report.append("### 🏆 Overall Top Performer")
            report.append(f"**{student_name}** with an average score of **{top_student['average']:.{self.decimal_places}f}%**")
            report.append("")
        
        # Subject-wise Analysis
        report.append("## 📈 Subject-wise Analysis")
        report.append("")
        
        subject_stats = analysis_results['subject_wise_stats']
        
        # Subject performance table
        report.append("### Subject Performance Summary")
        report.append("")
        report.append("| Subject | Students | Pass Rate | Fail Rate | Avg Score | Highest | Topper |")
        report.append("|---------|----------|-----------|-----------|-----------|---------|--------|")
        
        for subject, stats in subject_stats.items():
            topper_name = stats['topper']['name']
            if not show_student_ids:
                topper_name = f"Student_{hash(str(topper_name)) % 10000:04d}"
            
            report.append(f"| {subject} | {stats['total_count']} | "
                         f"{stats['pass_rate']:.{self.decimal_places}f}% | "
                         f"{stats['fail_rate']:.{self.decimal_places}f}% | "
                         f"{stats['average_score']:.{self.decimal_places}f} | "
                         f"{stats['highest_score']:.{self.decimal_places}f} | "
                         f"{topper_name} |")
        
        report.append("")
        
        # Subject-wise detailed analysis
        report.append("### Detailed Subject Analysis")
        report.append("")
        
        for subject, stats in subject_stats.items():
            report.append(f"#### {subject}")
            report.append(f"- **Total Students:** {stats['total_count']}")
            report.append(f"- **Passed:** {stats['passed_count']} ({stats['pass_rate']:.{self.decimal_places}f}%)")
            report.append(f"- **Failed:** {stats['failed_count']} ({stats['fail_rate']:.{self.decimal_places}f}%)")
            report.append(f"- **Average Score:** {stats['average_score']:.{self.decimal_places}f}")
            report.append(f"- **Score Range:** {stats['lowest_score']:.{self.decimal_places}f} - {stats['highest_score']:.{self.decimal_places}f}")
            
            topper_name = stats['topper']['name']
            if not show_student_ids:
                topper_name = f"Student_{hash(str(topper_name)) % 10000:04d}"
            
            report.append(f"- **Top Performer:** {topper_name} ({stats['topper']['score']:.{self.decimal_places}f}%)")
            report.append("")
        
        # Top Students
        report.append("## 🎯 Top Performing Students")
        report.append("")
        
        top_students = analysis_results['top_students'][:10]  # Top 10
        
        if top_students:
            report.append("| Rank | Student | Average Score |")
            report.append("|------|---------|---------------|")
            
            for i, student in enumerate(top_students, 1):
                student_name = student['name']
                if not show_student_ids:
                    student_name = f"Student_{hash(str(student_name)) % 10000:04d}"
                
                report.append(f"| {i} | {student_name} | {student['average']:.{self.decimal_places}f}% |")
        
        report.append("")
        
        # Anomalies and Concerns
        if analysis_results['anomalies']:
            report.append("## ⚠️ Anomalies and Concerns")
            report.append("")
            
            for anomaly in analysis_results['anomalies']:
                report.append(f"- **{anomaly['type'].replace('_', ' ').title()}:** {anomaly['description']}")
            
            report.append("")
        
        # Recommendations
        report.append("## 💡 Recommendations")
        report.append("")
        
        recommendations = self._generate_recommendations(analysis_results)
        for recommendation in recommendations:
            report.append(f"- {recommendation}")
        
        report.append("")
        
        # Report Footer
        report.append("---")
        report.append("*This report was generated automatically by the Student Examination Results Analysis System*")
        report.append("")
        
        return "\n".join(report)
    
    def _generate_recommendations(self, analysis_results: Dict[str, Any]) -> list:
        """Generate recommendations based on analysis results"""
        recommendations = []
        
        # Overall department performance
        dept_pass_rate = analysis_results['department_pass_rate']
        if dept_pass_rate < 50:
            recommendations.append("**Critical:** Department pass rate is below 50%. Consider reviewing curriculum and teaching methods.")
        elif dept_pass_rate < 70:
            recommendations.append("Department pass rate needs improvement. Focus on identifying struggling students early.")
        
        # Subject-specific recommendations
        subject_stats = analysis_results['subject_wise_stats']
        low_performing_subjects = []
        
        for subject, stats in subject_stats.items():
            if stats['pass_rate'] < 40:
                low_performing_subjects.append(subject)
                recommendations.append(f"**{subject}:** Very low pass rate ({stats['pass_rate']:.1f}%). Consider additional support or curriculum review.")
            elif stats['pass_rate'] < 60:
                recommendations.append(f"**{subject}:** Below-average performance. Consider targeted interventions.")
        
        # Student support recommendations
        failed_students = analysis_results['students_failed_any']
        total_students = analysis_results['total_students']
        
        if failed_students > total_students * 0.3:
            recommendations.append("High number of students failing subjects. Consider implementing peer tutoring or additional support systems.")
        
        # Anomaly-based recommendations
        anomalies = analysis_results['anomalies']
        for anomaly in anomalies:
            if anomaly['type'] == 'zero_scores':
                recommendations.append(f"Investigate zero scores in {anomaly['subject']}. May indicate attendance or assessment issues.")
            elif anomaly['type'] == 'excessive_perfect_scores':
                recommendations.append(f"Review assessment difficulty in {anomaly['subject']} due to high number of perfect scores.")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Overall performance is satisfactory. Continue monitoring and supporting student progress.")
        
        recommendations.append("Regular monitoring and early intervention for at-risk students is recommended.")
        recommendations.append("Consider subject-wise faculty meetings to discuss improvement strategies.")
        
        return recommendations
