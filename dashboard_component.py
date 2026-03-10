import io
from typing import Any, Callable, Dict

import pandas as pd
import plotly.express as px
import streamlit as st


def render_dashboard(
    df: pd.DataFrame,
    analysis_results: Dict[str, Any],
    round_decimals: int,
    subject_pass_marks: Dict[str, float],
    global_pass_percentage: float,
    matches_identifier: Callable[[str], bool],
    analyzer: Any,
    report_generator: Any,
) -> None:
    st.markdown('<div class="section-banner">📊 Executive Dashboard</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Students", analysis_results['total_students'], delta=None)

    with col2:
        st.metric("Total Subjects", analysis_results['total_subjects'], delta=None)

    with col3:
        pass_rate = analysis_results['department_pass_rate']
        st.metric(
            "Pass Rate",
            f"{pass_rate:.{round_decimals}f}%",
            delta=f"{pass_rate - 50:.1f}%" if pass_rate >= 50 else None,
        )

    with col4:
        avg_score = analysis_results['average_score']
        st.metric("Avg Score", f"{avg_score:.{round_decimals}f}%", delta=None)

    st.markdown("---")

    col_main1, col_main2 = st.columns([2, 1])

    with col_main1:
        st.markdown('<div class="section-banner">📈 Overall Performance Trends</div>', unsafe_allow_html=True)

        score_ranges = ['0-40', '41-60', '61-80', '81-100']
        range_counts = [0, 0, 0, 0]

        for _, row in df.iterrows():
            subject_cols = [col for col in df.columns if not matches_identifier(col)]
            scores = [row[col] for col in subject_cols if pd.notna(row[col])]

            for score in scores:
                if score <= 40:
                    range_counts[0] += 1
                elif score <= 60:
                    range_counts[1] += 1
                elif score <= 80:
                    range_counts[2] += 1
                else:
                    range_counts[3] += 1

        fig_dist = px.bar(
            x=score_ranges,
            y=range_counts,
            title="Score Distribution",
            labels={'x': 'Score Range', 'y': 'Frequency'},
            color=range_counts,
            text=range_counts,
        )
        fig_dist.update_traces(textposition='auto')
        st.plotly_chart(fig_dist, use_container_width=True)

    with col_main2:
        st.markdown('<div class="section-banner">🎯 Pass/Fail Status</div>', unsafe_allow_html=True)

        pass_rate = analysis_results['department_pass_rate']
        fail_rate = 100 - pass_rate

        fig_pie = px.pie(
            values=[pass_rate, fail_rate],
            names=['✅ Pass', '❌ Fail'],
            title="Overall Status",
            hole=0.4,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    st.markdown('<div class="section-banner">📚 Subject-wise Performance</div>', unsafe_allow_html=True)

    subject_stats = analysis_results['subject_wise_stats']
    subject_names = list(subject_stats.keys())
    pass_rates = [subject_stats[subject]['pass_rate'] for subject in subject_names]
    avg_scores = [subject_stats[subject]['average_score'] for subject in subject_names]

    col_sub1, col_sub2 = st.columns(2)

    with col_sub1:
        fig_bar_pass = px.bar(
            x=subject_names,
            y=pass_rates,
            title="Subject-wise Pass Rates",
            labels={'x': 'Subject', 'y': 'Pass Rate (%)'},
            color=pass_rates,
            text=[f"{pass_value:.1f}%" for pass_value in pass_rates],
        )
        fig_bar_pass.update_traces(textposition='auto')
        fig_bar_pass.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_bar_pass, use_container_width=True)

    with col_sub2:
        fig_bar_avg = px.bar(
            x=subject_names,
            y=avg_scores,
            title="Subject-wise Average Scores",
            labels={'x': 'Subject', 'y': 'Average Score (%)'},
            color=avg_scores,
            text=[f"{score:.1f}" for score in avg_scores],
        )
        fig_bar_avg.update_traces(textposition='auto')
        fig_bar_avg.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_bar_avg, use_container_width=True)

    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👥 Student Analysis",
        "🏆 Top Performers",
        "📋 Data Preview",
        "📊 Advanced Charts",
        "📄 Reports",
    ])

    with tab1:
        st.markdown('<div class="section-banner">👥 Student Performance Analysis</div>', unsafe_allow_html=True)

        col_s1, col_s2 = st.columns(2)

        with col_s1:
            st.subheader("Students Performance Distribution")

            subject_cols = [col for col in df.columns if not matches_identifier(col)]
            student_pass_counts = []

            for _, row in df.iterrows():
                pass_count = 0
                for subject in subject_cols:
                    subject_pass_mark = subject_pass_marks.get(subject, global_pass_percentage)
                    if pd.notna(row[subject]) and row[subject] >= subject_pass_mark:
                        pass_count += 1
                student_pass_counts.append(pass_count)

            pass_dist = [
                len([count for count in student_pass_counts if count == i])
                for i in range(len(subject_cols) + 1)
            ]

            fig_student = px.bar(
                x=[f"{i} Subjects" for i in range(len(subject_cols) + 1)],
                y=pass_dist,
                title="Students by Number of Subjects Passed",
                labels={'x': 'Subjects Passed', 'y': 'Number of Students'},
                color=pass_dist,
                text=pass_dist,
            )
            fig_student.update_traces(textposition='auto')
            st.plotly_chart(fig_student, use_container_width=True)

        with col_s2:
            st.subheader("Student Status Summary")

            students_passed_all = analysis_results['students_passed_all']
            students_failed_any = analysis_results['students_failed_any']

            status_df = pd.DataFrame(
                {
                    'Status': ['Passed All', 'Failed Any'],
                    'Count': [students_passed_all, students_failed_any],
                }
            )

            fig_status = px.pie(
                values=status_df['Count'],
                names=status_df['Status'],
                title="Overall Student Status",
            )
            st.plotly_chart(fig_status, use_container_width=True)

    with tab2:
        st.markdown('<div class="section-banner">🏆 Top Performers</div>', unsafe_allow_html=True)

        overall_top = analysis_results['overall_top_student']
        if overall_top:
            st.success(
                f"🥇 **Overall Top Performer:** {overall_top['name']} "
                f"(Average: {overall_top['average']:.{round_decimals}f}%)"
            )

        col_top1, col_top2 = st.columns(2)

        with col_top1:
            st.subheader("Subject-wise Toppers 🎯")

            toppers_data = []
            for subject, stats in analysis_results['subject_wise_stats'].items():
                if stats['topper']:
                    toppers_data.append(
                        {
                            'Subject': subject,
                            'Topper': stats['topper']['name'],
                            'Score': f"{stats['topper']['score']:.{round_decimals}f}",
                        }
                    )

            if toppers_data:
                toppers_df = pd.DataFrame(toppers_data)
                st.dataframe(toppers_df, use_container_width=True)

        with col_top2:
            st.subheader("Top 10 Students 🏅")

            top_students = analysis_results['top_students'][:10]

            if top_students:
                top_students_data = []
                for index, student in enumerate(top_students, 1):
                    top_students_data.append(
                        {
                            'Rank': f"#{index}",
                            'Student': student['name'],
                            'Avg': f"{student['average']:.{round_decimals}f}%",
                        }
                    )

                st.dataframe(pd.DataFrame(top_students_data), use_container_width=True)

    with tab3:
        st.markdown('<div class="section-banner">📋 Data Preview & Details</div>', unsafe_allow_html=True)

        col_data1, col_data2 = st.columns([3, 1])

        with col_data1:
            st.subheader("Raw Data")
            st.dataframe(df.head(15), use_container_width=True)

        with col_data2:
            st.subheader("Data Summary")
            st.write(f"**Total Records:** {len(df)}")
            st.write(f"**Total Columns:** {len(df.columns)}")
            st.write(
                f"**Subject Columns:** {len([col for col in df.columns if not matches_identifier(col)])}"
            )

    with tab4:
        st.markdown('<div class="section-banner">📊 Advanced Visualizations</div>', unsafe_allow_html=True)

        st.subheader("Student Scores Heatmap")

        subject_cols = [col for col in df.columns if not matches_identifier(col)]
        heatmap_data = df[['Student_Name'] + subject_cols].set_index('Student_Name')

        if len(heatmap_data) <= 50:
            fig_heatmap = px.imshow(
                heatmap_data,
                labels=dict(color='Score'),
                title='Student Scores Heatmap',
                aspect='auto',
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.info("Too many students to display heatmap. Please filter data.")

        st.subheader("Score Distribution by Subject (Box Plot)")

        box_data = []
        for subject in subject_cols:
            scores = df[subject].dropna()
            for score in scores:
                box_data.append({'Subject': subject, 'Score': score})

        if box_data:
            box_df = pd.DataFrame(box_data)
            fig_box = px.box(
                box_df,
                x='Subject',
                y='Score',
                title='Score Distribution by Subject',
                points='outliers',
                color='Subject',
            )
            st.plotly_chart(fig_box, use_container_width=True)

    with tab5:
        st.markdown('<div class="section-banner">📄 Reports & Exports</div>', unsafe_allow_html=True)

        report_content = report_generator.generate_report(analysis_results, True)

        st.subheader("Report Preview")
        st.markdown(report_content[:500] + "...")

        col_export1, col_export2, col_export3 = st.columns(3)

        with col_export1:
            export_data = analyzer.prepare_export_data(df, analysis_results, True)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                export_data['summary'].to_excel(writer, sheet_name='Summary', index=False)
                export_data['subject_analysis'].to_excel(writer, sheet_name='Subject Analysis', index=False)
                export_data['student_performance'].to_excel(
                    writer, sheet_name='Student Performance', index=False
                )

            st.download_button(
                label="📊 Export to Excel",
                data=output.getvalue(),
                file_name="examination_analysis_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        with col_export2:
            st.download_button(
                label="📄 Download Report (MD)",
                data=report_content,
                file_name="examination_analysis_report.md",
                mime="text/markdown",
            )

        with col_export3:
            pdf_data = analyzer.export_to_pdf(df, analysis_results)
            st.download_button(
                label="📕 Download Report (PDF)",
                data=pdf_data,
                file_name="examination_analysis_report.pdf",
                mime="application/pdf",
            )
