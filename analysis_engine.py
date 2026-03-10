import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_agg import FigureCanvasAgg
import base64

class ExamAnalyzer:
    """
    Core analysis engine for processing student examination results
    """
    
    def __init__(self, pass_percentage: float = 40.0, subject_pass_marks: Dict[str, float] = None):
        self.pass_percentage = pass_percentage  # Default pass percentage
        self.subject_pass_marks = subject_pass_marks or {}  # Subject-specific pass marks
    
    def _normalize_column_name(self, col_name: str) -> str:
        """Normalize column name for flexible matching"""
        return col_name.lower().strip().replace(' ', '_').replace('-', '_')
    
    def _matches_identifier(self, col_name: str) -> bool:
        """Check if column matches any identifier column"""
        normalized = self._normalize_column_name(col_name)
        
        identifier_patterns = [
            'student_id', 'studentid', 'student id',
            'student_name', 'studentname', 'student name',
            'reg_no', 'regno', 'reg no', 'registration_no', 'registrationno',
            'roll_no', 'rollno', 'roll no', 'roll_number', 'rollnumber',
            'total', 'grand_total', 'grandtotal', 'sum',
            'average', 'avg', 'mean',
            'percentage', 'percent', '%'
        ]
        
        return normalized in identifier_patterns
        
    def set_subject_pass_marks(self, pass_marks: Dict[str, float]):
        """Set subject-specific pass marks."""
        self.subject_pass_marks = pass_marks
        
    def get_pass_mark(self, subject: str) -> float:
        """Get pass mark for a specific subject."""
        return self.subject_pass_marks.get(subject, self.pass_percentage)
        
    def analyze_results(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Perform comprehensive analysis on examination results
        
        Args:
            df: DataFrame containing student examination data
            
        Returns:
            Dictionary containing all analysis results
        """
        # Add default Student_ID and Student_Name if they don't exist
        if 'Student_ID' not in df.columns:
            df['Student_ID'] = [f"Student_{i+1}" for i in range(len(df))]
        if 'Student_Name' not in df.columns:
            df['Student_Name'] = df['Student_ID']
        
        # Get subject columns (exclude identifier columns - Student_ID, Student_Name, REG NO, Roll No)
        subject_cols = [col for col in df.columns if not self._matches_identifier(col)]
        
        # Basic statistics
        total_students = len(df)
        total_subjects = len(subject_cols)
        
        # Calculate subject-wise statistics
        subject_wise_stats = self._calculate_subject_stats(df, subject_cols)
        
        # Calculate department pass rate
        department_pass_rate = self._calculate_department_pass_rate(df, subject_cols)
        
        # Find top performers
        overall_top_student = self._find_overall_top_student(df, subject_cols)
        top_students = self._find_top_students(df, subject_cols)
        
        # Calculate students who passed all subjects
        students_passed_all = self._count_students_passed_all(df, subject_cols)
        students_failed_any = total_students - students_passed_all
        
        # Calculate average score across all subjects
        all_scores = []
        for col in subject_cols:
            all_scores.extend(df[col].dropna().tolist())
        average_score = np.mean(all_scores) if all_scores else 0
        
        # Detect anomalies
        anomalies = self._detect_anomalies(df, subject_cols)
        
        return {
            'total_students': total_students,
            'total_subjects': total_subjects,
            'subject_wise_stats': subject_wise_stats,
            'department_pass_rate': department_pass_rate,
            'overall_top_student': overall_top_student,
            'top_students': top_students,
            'students_passed_all': students_passed_all,
            'students_failed_any': students_failed_any,
            'average_score': average_score,
            'anomalies': anomalies,
            'pass_percentage': self.pass_percentage
        }
    
    def _calculate_subject_stats(self, df: pd.DataFrame, subject_cols: List[str]) -> Dict[str, Dict]:
        """Calculate statistics for each subject, including list of students who passed"""
        subject_stats = {}
        for subject in subject_cols:
            scores = df[subject].dropna()
            if len(scores) == 0:
                continue
            pass_mark = self.get_pass_mark(subject)
            passed_mask = scores >= pass_mark
            passed_count = passed_mask.sum()
            failed_count = (~passed_mask).sum()
            total_count = len(scores)
            pass_rate = (passed_count / total_count) * 100 if total_count > 0 else 0
            fail_rate = (failed_count / total_count) * 100 if total_count > 0 else 0
            average_score = scores.mean()
            highest_score = scores.max()
            lowest_score = scores.min()
            topper_idx = scores.idxmax()
            topper_name = df.loc[topper_idx, 'Student_Name'] if 'Student_Name' in df.columns else 'Unknown'
            topper_score = scores.max()
            # List of students who passed this subject
            cols_to_select = []
            if 'Student_ID' in df.columns:
                cols_to_select.append('Student_ID')
            if 'Student_Name' in df.columns:
                cols_to_select.append('Student_Name')
            
            if cols_to_select:
                passed_students = df.loc[scores.index[passed_mask], cols_to_select].to_dict('records')
            else:
                passed_students = []
            subject_stats[subject] = {
                'passed_count': passed_count,
                'failed_count': failed_count,
                'total_count': total_count,
                'pass_rate': pass_rate,
                'fail_rate': fail_rate,
                'average_score': average_score,
                'highest_score': highest_score,
                'lowest_score': lowest_score,
                'topper': {
                    'name': topper_name,
                    'score': topper_score
                },
                'passed_students': passed_students
            }
        return subject_stats
    
    def _calculate_department_pass_rate(self, df: pd.DataFrame, subject_cols: List[str]) -> float:
        """Calculate overall department pass rate"""
        students_passed_all = self._count_students_passed_all(df, subject_cols)
        total_students = len(df)
        
        return (students_passed_all / total_students) * 100 if total_students > 0 else 0
    
    def _count_students_passed_all(self, df: pd.DataFrame, subject_cols: List[str]) -> int:
        """Count students who passed all subjects"""
        passed_all_count = 0
        
        for _, row in df.iterrows():
            passed_all = True
            for subject in subject_cols:
                pass_mark = self.get_pass_mark(subject)
                if pd.isna(row[subject]) or row[subject] < pass_mark:
                    passed_all = False
                    break
            
            if passed_all:
                passed_all_count += 1
        
        return passed_all_count
    
    def _find_overall_top_student(self, df: pd.DataFrame, subject_cols: List[str]) -> Optional[Dict]:
        """Find the overall top performing student"""
        student_averages = []
        
        for _, row in df.iterrows():
            scores = [row[col] for col in subject_cols if pd.notna(row[col])]
            if scores:
                average = np.mean(scores)
                student_name = row.get('Student_Name', row.get('Student_ID', 'Unknown Student'))
                student_averages.append({
                    'name': student_name,
                    'average': average,
                    'scores': scores
                })
        
        if not student_averages:
            return None
        
        # Sort by average score
        student_averages.sort(key=lambda x: x['average'], reverse=True)
        
        return student_averages[0]
    
    def _find_top_students(self, df: pd.DataFrame, subject_cols: List[str], top_n: int = 10) -> List[Dict]:
        """Find top N students by overall performance"""
        student_averages = []
        
        for _, row in df.iterrows():
            scores = [row[col] for col in subject_cols if pd.notna(row[col])]
            if scores:
                average = np.mean(scores)
                student_name = row.get('Student_Name', row.get('Student_ID', 'Unknown Student'))
                student_averages.append({
                    'name': student_name,
                    'average': average,
                    'total_subjects': len(scores)
                })
        
        # Sort by average score
        student_averages.sort(key=lambda x: x['average'], reverse=True)
        
        return student_averages[:top_n]
    
    def _detect_anomalies(self, df: pd.DataFrame, subject_cols: List[str]) -> List[Dict]:
        """Detect anomalies in the data"""
        anomalies = []
        
        for subject in subject_cols:
            scores = df[subject].dropna()
            
            if len(scores) == 0:
                anomalies.append({
                    'type': 'empty_subject',
                    'subject': subject,
                    'description': f"No valid scores found for {subject}"
                })
                continue
            
            # Check for perfect scores (might indicate data entry issues)
            perfect_scores = len(scores[scores == 100])
            if perfect_scores > len(scores) * 0.3:  # More than 30% perfect scores
                anomalies.append({
                    'type': 'excessive_perfect_scores',
                    'subject': subject,
                    'count': perfect_scores,
                    'description': f"Unusually high number of perfect scores in {subject} ({perfect_scores} students)"
                })
            
            # Check for zero scores
            zero_scores = len(scores[scores == 0])
            if zero_scores > 0:
                anomalies.append({
                    'type': 'zero_scores',
                    'subject': subject,
                    'count': zero_scores,
                    'description': f"{zero_scores} students have zero scores in {subject}"
                })
            
            # Check for very low pass rates
            pass_mark = self.get_pass_mark(subject)
            pass_rate = len(scores[scores >= pass_mark]) / len(scores) * 100
            if pass_rate < 20:  # Less than 20% pass rate
                anomalies.append({
                    'type': 'low_pass_rate',
                    'subject': subject,
                    'pass_rate': pass_rate,
                    'description': f"Very low pass rate in {subject} ({pass_rate:.1f}%)"
                })
        
        return anomalies
    
    def _create_chart_image(self, fig, width=6, height=4):
        """Convert matplotlib figure to reportlab Image"""
        # Set figure size
        fig.set_size_inches(width, height)
        
        # Save to bytes buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        buf.seek(0)
        
        # Create reportlab Image
        img = Image(buf, width=width*inch, height=height*inch)
        plt.close(fig)  # Clean up
        return img
    
    def _create_pass_rate_chart(self, analysis_results):
        """Create pass rate bar chart"""
        fig, ax = plt.subplots(figsize=(8, 5))
        
        subjects = list(analysis_results['subject_wise_stats'].keys())
        pass_rates = [stats['pass_rate'] for stats in analysis_results['subject_wise_stats'].values()]
        
        bars = ax.bar(subjects, pass_rates, color='steelblue', alpha=0.7)
        ax.set_ylabel('Pass Rate (%)')
        ax.set_title('Subject-wise Pass Rates', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 100)
        
        # Add value labels on bars
        for bar, rate in zip(bars, pass_rates):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{rate:.1f}%', ha='center', va='bottom', fontsize=9)
        
        # Rotate x-axis labels if too long
        if len(max(subjects, key=len)) > 8:
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        return fig
    
    def _create_score_distribution_chart(self, analysis_results):
        """Create average score distribution chart"""
        fig, ax = plt.subplots(figsize=(8, 5))
        
        subjects = list(analysis_results['subject_wise_stats'].keys())
        avg_scores = [stats['average_score'] for stats in analysis_results['subject_wise_stats'].values()]
        
        bars = ax.bar(subjects, avg_scores, color='lightcoral', alpha=0.7)
        ax.set_ylabel('Average Score')
        ax.set_title('Subject-wise Average Scores', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 100)
        
        # Add value labels on bars
        for bar, score in zip(bars, avg_scores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{score:.1f}', ha='center', va='bottom', fontsize=9)
        
        # Rotate x-axis labels if too long
        if len(max(subjects, key=len)) > 8:
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        return fig
    
    def _create_performance_comparison_chart(self, analysis_results):
        """Create pass vs fail comparison chart"""
        fig, ax = plt.subplots(figsize=(8, 6))
        
        subjects = list(analysis_results['subject_wise_stats'].keys())
        passed_counts = [stats['passed_count'] for stats in analysis_results['subject_wise_stats'].values()]
        failed_counts = [stats['failed_count'] for stats in analysis_results['subject_wise_stats'].values()]
        
        x = range(len(subjects))
        width = 0.35
        
        bars1 = ax.bar([i - width/2 for i in x], passed_counts, width, 
                      label='Passed', color='green', alpha=0.7)
        bars2 = ax.bar([i + width/2 for i in x], failed_counts, width,
                      label='Failed', color='red', alpha=0.7)
        
        ax.set_xlabel('Subjects')
        ax.set_ylabel('Number of Students')
        ax.set_title('Pass vs Fail Comparison by Subject', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(subjects)
        ax.legend()
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       f'{int(height)}', ha='center', va='bottom', fontsize=8)
        
        # Rotate x-axis labels if too long
        if len(max(subjects, key=len)) > 8:
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        return fig
    
    def _create_score_range_chart(self, analysis_results):
        """Create score range (min-max) chart"""
        fig, ax = plt.subplots(figsize=(8, 5))
        
        subjects = list(analysis_results['subject_wise_stats'].keys())
        min_scores = [stats['lowest_score'] for stats in analysis_results['subject_wise_stats'].values()]
        max_scores = [stats['highest_score'] for stats in analysis_results['subject_wise_stats'].values()]
        avg_scores = [stats['average_score'] for stats in analysis_results['subject_wise_stats'].values()]
        
        x = range(len(subjects))
        
        # Plot min-max range as error bars
        ax.errorbar(x, avg_scores, 
                   yerr=[np.array(avg_scores) - np.array(min_scores),
                         np.array(max_scores) - np.array(avg_scores)],
                   fmt='o', capsize=5, capthick=2, elinewidth=2,
                   color='blue', alpha=0.7)
        
        ax.set_xlabel('Subjects')
        ax.set_ylabel('Scores')
        ax.set_title('Score Range by Subject (Min-Average-Max)', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(subjects)
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.3)
        
        # Rotate x-axis labels if too long
        if len(max(subjects, key=len)) > 8:
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        return fig
    
    def _create_department_overview_chart(self, analysis_results):
        """Create department overview pie chart"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
        
        # Overall Pass/Fail pie chart
        passed_all = analysis_results['students_passed_all']
        failed_any = analysis_results['students_failed_any']
        
        if passed_all > 0 or failed_any > 0:
            labels1 = ['Passed All Subjects', 'Failed At Least One']
            sizes1 = [passed_all, failed_any]
            colors1 = ['lightgreen', 'lightcoral']
            
            ax1.pie(sizes1, labels=labels1, colors=colors1, autopct='%1.1f%%',
                   startangle=90, textprops={'fontsize': 10})
            ax1.set_title('Overall Department Performance', fontsize=12, fontweight='bold')
        
        # Subject count pie chart showing difficulty
        subject_stats = analysis_results['subject_wise_stats']
        if subject_stats:
            pass_rates = [stats['pass_rate'] for stats in subject_stats.values()]
            
            # Categorize subjects by difficulty
            easy_subjects = sum(1 for rate in pass_rates if rate >= 80)
            medium_subjects = sum(1 for rate in pass_rates if 50 <= rate < 80)
            hard_subjects = sum(1 for rate in pass_rates if rate < 50)
            
            if easy_subjects > 0 or medium_subjects > 0 or hard_subjects > 0:
                labels2 = []
                sizes2 = []
                colors2 = []
                
                if easy_subjects > 0:
                    labels2.append(f'Easy Subjects (≥80%)')
                    sizes2.append(easy_subjects)
                    colors2.append('lightgreen')
                
                if medium_subjects > 0:
                    labels2.append(f'Medium Subjects (50-79%)')
                    sizes2.append(medium_subjects)
                    colors2.append('gold')
                
                if hard_subjects > 0:
                    labels2.append(f'Hard Subjects (<50%)')
                    sizes2.append(hard_subjects)
                    colors2.append('lightcoral')
                
                ax2.pie(sizes2, labels=labels2, colors=colors2, autopct='%1.0f',
                       startangle=90, textprops={'fontsize': 10})
                ax2.set_title('Subject Difficulty Distribution', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        return fig
    
    def prepare_export_data(self, df: pd.DataFrame, analysis_results: Dict, show_student_ids: bool) -> Dict[str, pd.DataFrame]:
        """Prepare data for export"""
        # Add default Student_ID and Student_Name if they don't exist
        if 'Student_ID' not in df.columns:
            df = df.copy()
            df['Student_ID'] = [f"Student_{i+1}" for i in range(len(df))]
        if 'Student_Name' not in df.columns:
            df = df.copy()
            df['Student_Name'] = df['Student_ID']
        
        # Get subject columns using flexible matching
        subject_cols = [col for col in df.columns if not self._matches_identifier(col)]
        
        # Summary data
        summary_data = {
            'Metric': [
                'Total Students',
                'Total Subjects',
                'Department Pass Rate (%)',
                'Students Passed All Subjects',
                'Students Failed At Least One Subject',
                'Average Score Across All Subjects (%)'
            ],
            'Value': [
                analysis_results['total_students'],
                analysis_results['total_subjects'],
                f"{analysis_results['department_pass_rate']:.2f}",
                analysis_results['students_passed_all'],
                analysis_results['students_failed_any'],
                f"{analysis_results['average_score']:.2f}"
            ]
        }
        
        # Subject analysis data
        subject_analysis_data = []
        for subject, stats in analysis_results['subject_wise_stats'].items():
            subject_analysis_data.append({
                'Subject': subject,
                'Total Students': stats['total_count'],
                'Passed': stats['passed_count'],
                'Failed': stats['failed_count'],
                'Pass Rate (%)': f"{stats['pass_rate']:.2f}",
                'Fail Rate (%)': f"{stats['fail_rate']:.2f}",
                'Average Score': f"{stats['average_score']:.2f}",
                'Highest Score': f"{stats['highest_score']:.2f}",
                'Lowest Score': f"{stats['lowest_score']:.2f}",
                'Topper': stats['topper']['name'] if not show_student_ids else f"Student_{hash(str(stats['topper']['name'])) % 10000:04d}"
            })
        
        # Student performance data
        student_performance_data = []
        for _, row in df.iterrows():
            student_data = {
                'Student_ID': row['Student_ID'] if show_student_ids else f"Student_{hash(str(row['Student_ID'])) % 10000:04d}",
                'Student_Name': row['Student_Name'] if show_student_ids else f"Student_{hash(str(row['Student_Name'])) % 10000:04d}"
            }
            
            # Add subject scores
            for subject in subject_cols:
                student_data[subject] = row[subject] if pd.notna(row[subject]) else 'N/A'
            
            # Calculate overall performance
            scores = [row[col] for col in subject_cols if pd.notna(row[col])]
            if scores:
                student_data['Average Score'] = f"{np.mean(scores):.2f}"
                # Check if passed all subjects using subject-specific pass marks
                passed_all = True
                for i, subject in enumerate(subject_cols):
                    if pd.notna(row[subject]):
                        pass_mark = self.get_pass_mark(subject)
                        if row[subject] < pass_mark:
                            passed_all = False
                            break
                student_data['Passed All Subjects'] = 'Yes' if passed_all else 'No'
            else:
                student_data['Average Score'] = 'N/A'
                student_data['Passed All Subjects'] = 'N/A'
            
            student_performance_data.append(student_data)
        
        return {
            'summary': pd.DataFrame(summary_data),
            'subject_analysis': pd.DataFrame(subject_analysis_data),
            'student_performance': pd.DataFrame(student_performance_data)
        }
    
    def export_to_pdf(self, df: pd.DataFrame, analysis_results: Dict) -> bytes:
        """Generate PDF report of the analysis results"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        # Title
        title = Paragraph("Student Examination Results Analysis Report", title_style)
        elements.append(title)
        
        # Generation date
        date_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        date_para = Paragraph(f"Generated on: {date_str}", styles['Normal'])
        elements.append(date_para)
        elements.append(Spacer(1, 20))
        
        # Summary Section
        summary_heading = Paragraph("Executive Summary", heading_style)
        elements.append(summary_heading)
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Students', str(analysis_results['total_students'])],
            ['Total Subjects', str(analysis_results['total_subjects'])],
            ['Department Pass Rate', f"{analysis_results['department_pass_rate']:.2f}%"],
            ['Students Passed All Subjects', str(analysis_results['students_passed_all'])],
            ['Students Failed At Least One Subject', str(analysis_results['students_failed_any'])],
            ['Average Score Across All Subjects', f"{analysis_results['average_score']:.2f}%"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Department Overview Charts
        dept_overview_heading = Paragraph("Department Performance Overview", heading_style)
        elements.append(dept_overview_heading)
        
        # Add department overview chart
        try:
            dept_chart = self._create_department_overview_chart(analysis_results)
            dept_chart_img = self._create_chart_image(dept_chart, width=7, height=3.5)
            elements.append(dept_chart_img)
            elements.append(Spacer(1, 15))
        except Exception as e:
            elements.append(Paragraph(f"Chart generation error: {str(e)}", styles['Normal']))
        
        elements.append(PageBreak())
        
        # Subject-wise Analysis
        subject_heading = Paragraph("Subject-wise Performance Analysis", heading_style)
        elements.append(subject_heading)
        
        # Add pass rate chart
        try:
            pass_rate_chart = self._create_pass_rate_chart(analysis_results)
            pass_rate_img = self._create_chart_image(pass_rate_chart, width=7, height=4)
            elements.append(pass_rate_img)
            elements.append(Spacer(1, 15))
        except Exception as e:
            elements.append(Paragraph(f"Pass rate chart error: {str(e)}", styles['Normal']))
        
        # Add performance comparison chart
        try:
            comparison_chart = self._create_performance_comparison_chart(analysis_results)
            comparison_img = self._create_chart_image(comparison_chart, width=7, height=4.5)
            elements.append(comparison_img)
            elements.append(Spacer(1, 15))
        except Exception as e:
            elements.append(Paragraph(f"Comparison chart error: {str(e)}", styles['Normal']))
        
        elements.append(PageBreak())
        
        # Subject-wise Analysis
        subject_heading = Paragraph("Detailed Subject Analysis", heading_style)
        elements.append(subject_heading)
        
        subject_data = [['Subject', 'Total', 'Passed', 'Failed', 'Pass Rate', 'Avg Score', 'Highest', 'Lowest', 'Topper']]
        
        for subject, stats in analysis_results['subject_wise_stats'].items():
            # Truncate subject name if too long
            subject_name = subject[:20] + "..." if len(subject) > 20 else subject
            topper_name = stats['topper']['name'][:12] + "..." if len(stats['topper']['name']) > 12 else stats['topper']['name']
            
            subject_data.append([
                subject_name,
                str(stats['total_count']),
                str(stats['passed_count']),
                str(stats['failed_count']),
                f"{stats['pass_rate']:.1f}%",
                f"{stats['average_score']:.1f}",
                f"{stats['highest_score']:.1f}",
                f"{stats['lowest_score']:.1f}",
                topper_name
            ])
        
        # Adjust column widths to better accommodate subject names
        subject_table = Table(subject_data, colWidths=[1.4*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.6*inch, 0.6*inch, 0.6*inch, 0.6*inch, 1.0*inch])
        subject_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('WORDWRAP', (0, 0), (-1, -1), True)
        ]))
        
        elements.append(subject_table)
        elements.append(Spacer(1, 20))
        
        # Add score distribution chart
        try:
            score_dist_chart = self._create_score_distribution_chart(analysis_results)
            score_dist_img = self._create_chart_image(score_dist_chart, width=7, height=4)
            elements.append(score_dist_img)
            elements.append(Spacer(1, 15))
        except Exception as e:
            elements.append(Paragraph(f"Score distribution chart error: {str(e)}", styles['Normal']))

        # Add score range chart
        try:
            score_range_chart = self._create_score_range_chart(analysis_results)
            score_range_img = self._create_chart_image(score_range_chart, width=7, height=4)
            elements.append(score_range_img)
            elements.append(Spacer(1, 15))
        except Exception as e:
            elements.append(Paragraph(f"Score range chart error: {str(e)}", styles['Normal']))

        # Add passed students per subject section
        passed_students_heading = Paragraph("Students Who Passed Each Subject", heading_style)
        elements.append(passed_students_heading)
        for subject, stats in analysis_results['subject_wise_stats'].items():
            subject_name = subject[:20] + "..." if len(subject) > 20 else subject
            elements.append(Paragraph(f"<b>{subject_name}</b>", styles['Normal']))
            passed_students = stats.get('passed_students', [])
            if passed_students:
                # Show up to 10 students per subject, add note if more
                max_display = 10
                table_data = [["Student ID", "Student Name"]]
                for student in passed_students[:max_display]:
                    table_data.append([str(student.get('Student_ID', '')), str(student.get('Student_Name', ''))])
                if len(passed_students) > max_display:
                    table_data.append(["...", f"and {len(passed_students) - max_display} more"])
                table = Table(table_data, colWidths=[1.5*inch, 2.5*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 8))
            else:
                elements.append(Paragraph("No students passed this subject.", styles['Normal']))
                elements.append(Spacer(1, 8))
        elements.append(PageBreak())
        
        # Top Performers Section
        top_heading = Paragraph("Top Performers", heading_style)
        elements.append(top_heading)
        
        # Overall top student
        overall_top = analysis_results['overall_top_student']
        if overall_top:
            top_student_para = Paragraph(
                f"<b>Overall Top Performer:</b> {overall_top['name']} (Average: {overall_top['average']:.2f}%)",
                styles['Normal']
            )
            elements.append(top_student_para)
            elements.append(Spacer(1, 10))
        
        # Top 10 students
        top_students = analysis_results['top_students'][:10]
        if top_students:
            top_students_data = [['Rank', 'Student Name', 'Average Score']]
            for i, student in enumerate(top_students, 1):
                top_students_data.append([
                    str(i),
                    student['name'],
                    f"{student['average']:.2f}%"
                ])
            
            top_students_table = Table(top_students_data, colWidths=[0.8*inch, 3*inch, 1.5*inch])
            top_students_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(top_students_table)
            elements.append(Spacer(1, 20))
        
        # Anomalies Section
        if analysis_results['anomalies']:
            anomalies_heading = Paragraph("Data Quality Issues and Anomalies", heading_style)
            elements.append(anomalies_heading)
            
            for anomaly in analysis_results['anomalies']:
                anomaly_para = Paragraph(f"• {anomaly['description']}", styles['Normal'])
                elements.append(anomaly_para)
            
            elements.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(elements)
        
        buffer.seek(0)
        return buffer.getvalue()
