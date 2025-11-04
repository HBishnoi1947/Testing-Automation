"""
Professional Invoice-Style PDF Report Generator for Test Execution Results
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, 
                                 Paragraph, Spacer, PageBreak, KeepTogether)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.piecharts import Pie
from datetime import datetime
import os


def generate_test_execution_pdf(results: dict, output_path: str = None) -> str:
    """
    Generate a professional invoice-style PDF report for test execution results.
    
    Args:
        results: Dict containing module execution results
        output_path: Optional custom path for PDF
        
    Returns:
        str: Path to generated PDF file
    """
    # Create reports directory
    if not output_path:
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(reports_dir, f"test_report_{timestamp}.pdf")
    
    # Create PDF document
    doc = SimpleDocTemplate(output_path, pagesize=A4, 
                           topMargin=0.5*inch, bottomMargin=0.5*inch,
                           leftMargin=0.75*inch, rightMargin=0.75*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold',
        borderColor=colors.HexColor('#3498db'),
        borderWidth=2,
        borderPadding=8,
        backColor=colors.HexColor('#f8f9fa')
    )
    
    # ========== HEADER SECTION ==========
    story.append(Paragraph("TEST EXECUTION REPORT", title_style))
    story.append(Paragraph("Automated Testing Summary", subtitle_style))
    
    # Horizontal divider line
    divider_data = [['']]
    divider_table = Table(divider_data, colWidths=[7*inch])
    divider_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 2, colors.HexColor('#3498db')),
    ]))
    story.append(divider_table)
    story.append(Spacer(1, 0.2*inch))
    
    # ========== MODULE INFO SECTION ==========
    info_data = [
        [Paragraph("<b>Module:</b>", styles['Normal']), 
         Paragraph(results['module_name'], styles['Normal'])],
        [Paragraph("<b>Execution Date:</b>", styles['Normal']), 
         Paragraph(results['execution_time'], styles['Normal'])],
        [Paragraph("<b>Report ID:</b>", styles['Normal']), 
         Paragraph(f"RPT-{datetime.now().strftime('%Y%m%d-%H%M%S')}", styles['Normal'])]
    ]
    
    info_table = Table(info_data, colWidths=[1.5*inch, 5.5*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ffffff')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#e0e0e0')),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.4*inch))
    
    # ========== SUMMARY SECTION WITH DONUT CHART AND STATS ==========
    story.append(Paragraph("EXECUTION SUMMARY", header_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Calculate totals
    total_events = sum(f['total_events'] for f in results['feature_results'])
    passed_events = sum(f['passed_events'] for f in results['feature_results'])
    failed_events = sum(f['failed_events'] for f in results['feature_results'])
    total_features = len(results['feature_results'])
    passed_features = sum(1 for f in results['feature_results'] if f['success'])
    failed_features = total_features - passed_features
    success_rate = (passed_events / total_events * 100) if total_events > 0 else 0
    fail_rate = 100 - success_rate
    
    # LEFT SIDE: Summary Statistics
    summary_stats = [
        ['', 'TOTAL', 'PASSED', 'FAILED'],
        ['Features', str(total_features), str(passed_features), str(failed_features)],
        ['Events', str(total_events), str(passed_events), str(failed_events)],
        ['Success Rate', f'{success_rate:.1f}%', '', '']
    ]
    
    stats_table = Table(summary_stats, colWidths=[1*inch, 0.8*inch, 0.8*inch, 0.8*inch])
    stats_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#95a5a6')),
        ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#28a745')),
        ('BACKGROUND', (3, 0), (3, 0), colors.HexColor('#dc3545')),
        ('TEXTCOLOR', (1, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
        ('PADDING', (0, 0), (-1, 0), 8),
        # Data rows
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#ecf0f1')),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('PADDING', (0, 1), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # Grid
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#7f8c8d')),
        # Success rate row highlight
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#d5dbdb')),
        ('SPAN', (1, 3), (-1, 3)),
        ('FONTNAME', (1, 3), (1, 3), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 3), (1, 3), 12),
    ]))
    
    # RIGHT SIDE: Donut Chart with Legend
    drawing = Drawing(280, 200)
    
    # Create donut chart
    donut = Pie()
    donut.x = 50
    donut.y = 25
    donut.width = 150
    donut.height = 150
    donut.innerRadiusFraction = 0.6  # Creates the donut hole
    
    # Handle edge cases
    if failed_events == 0:
        donut.data = [passed_events, 0.001]
    elif passed_events == 0:
        donut.data = [0.001, failed_events]
    else:
        donut.data = [passed_events, failed_events]
    
    # Standard colors - Green and Red
    donut.slices[0].fillColor = colors.HexColor('#28a745')  # Bootstrap success green
    donut.slices[1].fillColor = colors.HexColor('#dc3545')  # Bootstrap danger red
    donut.slices[0].strokeColor = colors.white
    donut.slices[1].strokeColor = colors.white
    donut.slices[0].strokeWidth = 3
    donut.slices[1].strokeWidth = 3
    
    # Remove labels from slices
    donut.labels = None
    donut.simpleLabels = 0
    
    drawing.add(donut)
    
    # Add center text showing success rate
    center_text = String(125, 100, f'{success_rate:.1f}%',
                        fontSize=24, fontName='Helvetica-Bold',
                        textAnchor='middle', fillColor=colors.HexColor('#1a1a1a'))
    drawing.add(center_text)
    
    center_label = String(125, 82, 'Success',
                         fontSize=11, fontName='Helvetica',
                         textAnchor='middle', fillColor=colors.HexColor('#666666'))
    drawing.add(center_label)
    
    # Add manual legend below chart
    # Add manual legend below chart
    legend_y = 5  # lowered from 15 to 10 for a slightly lower position

    # Pass legend item
    pass_box = Rect(65, legend_y, 12, 12, fillColor=colors.HexColor('#28a745'), 
                    strokeColor=colors.HexColor('#28a745'))
    drawing.add(pass_box)
    pass_text = String(83, legend_y + 3, f'Pass {success_rate:.1f}%',
                    fontSize=11, fontName='Helvetica-Bold',
                    fillColor=colors.HexColor('#1a1a1a'))
    drawing.add(pass_text)

    # Fail legend item
    fail_box = Rect(165, legend_y, 12, 12, fillColor=colors.HexColor('#dc3545'),
                    strokeColor=colors.HexColor('#dc3545'))
    drawing.add(fail_box)
    fail_text = String(183, legend_y + 3, f'Fail {fail_rate:.1f}%',
                    fontSize=11, fontName='Helvetica-Bold',
                    fillColor=colors.HexColor('#1a1a1a'))
    drawing.add(fail_text)

    
    # Combine stats and chart in single row
    summary_layout = [[stats_table, drawing]]
    layout_table = Table(summary_layout, colWidths=[3.5*inch, 3.5*inch])
    layout_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
    ]))
    
    story.append(layout_table)
    story.append(Spacer(1, 0.5*inch))
    
    # ========== FEATURE DETAILS ==========
    story.append(Paragraph("FEATURE DETAILS", header_style))
    story.append(Spacer(1, 0.2*inch))
    
    for idx, feature in enumerate(results['feature_results'], 1):
        # Feature header box
        status_symbol = "✓" if feature['success'] else "✗"
        status_color = colors.HexColor('#28a745') if feature['success'] else colors.HexColor('#dc3545')
        status_bg = colors.HexColor('#d4edda') if feature['success'] else colors.HexColor('#f8d7da')
        
        feature_header_data = [[
            Paragraph(f"<b>Feature {idx}: {feature['feature_name']}</b>", styles['Normal']),
            Paragraph(f"<b>{status_symbol} {'PASS' if feature['success'] else 'FAIL'}</b>", 
                     ParagraphStyle('status', parent=styles['Normal'], textColor=status_color, alignment=TA_RIGHT))
        ]]
        
        feature_header_table = Table(feature_header_data, colWidths=[5.5*inch, 1.5*inch])
        feature_header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), status_bg),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 2, status_color),
        ]))
        story.append(feature_header_table)
        story.append(Spacer(1, 0.1*inch))
        
        # Events table
        if feature['event_results']:
            event_data = [['Event #', 'Operation', 'Status']]
            
            for event in feature['event_results']:
                status = '✓ Pass' if event['success'] else '✗ Fail'
                event_data.append([
                    str(event['event_number']),
                    event['operation'],
                    status
                ])
            
            events_table = Table(event_data, colWidths=[1*inch, 4.5*inch, 1.5*inch])
            
            table_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#7f8c8d')),
            ]
            
            # Alternate row colors
            for row_idx in range(1, len(event_data)):
                if row_idx % 2 == 0:
                    bg_color = colors.HexColor('#f8f9fa')
                else:
                    bg_color = colors.white
                table_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), bg_color))
            
            # Status column coloring
            for row_idx, event in enumerate(feature['event_results'], 1):
                if event['success']:
                    text_color = colors.HexColor('#28a745')
                else:
                    text_color = colors.HexColor('#dc3545')
                table_style.append(('TEXTCOLOR', (2, row_idx), (2, row_idx), text_color))
                table_style.append(('FONTNAME', (2, row_idx), (2, row_idx), 'Helvetica-Bold'))
            
            events_table.setStyle(TableStyle(table_style))
            story.append(events_table)
        else:
            story.append(Paragraph("<i>No events recorded</i>", styles['Italic']))
        
        story.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer_line = Table([['']], colWidths=[7*inch])
    footer_line.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
    ]))
    story.append(footer_line)
    story.append(Spacer(1, 0.1*inch))
    
    footer_text = ParagraphStyle('footer', parent=styles['Normal'], 
                                 fontSize=8, textColor=colors.HexColor('#7f8c8d'),
                                 alignment=TA_CENTER)
    story.append(Paragraph(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Confidential", footer_text))
    
    # Build PDF
    doc.build(story)
    print(f"[✓] Professional PDF Report generated: {output_path}")
    
    return output_path


# Test function
if __name__ == "__main__":
    test_results = {
        'module_name': 'User Authentication Module',
        'execution_time': '2025-11-03 14:30:45',
        'total_features': 2,
        'passed_features': 1,
        'failed_features': 1,
        'feature_results': [
            {
                'feature_name': 'User Login',
                'success': True,
                'total_events': 4,
                'passed_events': 4,
                'failed_events': 0,
                'event_results': [
                    {'event_number': 1, 'operation': 'input_text', 'success': True},
                    {'event_number': 2, 'operation': 'input_text', 'success': True},
                    {'event_number': 3, 'operation': 'click', 'success': True},
                    {'event_number': 4, 'operation': 'verify_element', 'success': True},
                ]
            },
            {
                'feature_name': 'Password Reset',
                'success': False,
                'total_events': 3,
                'passed_events': 2,
                'failed_events': 1,
                'event_results': [
                    {'event_number': 1, 'operation': 'input_text', 'success': True},
                    {'event_number': 2, 'operation': 'input_text', 'success': True},
                    {'event_number': 3, 'operation': 'click', 'success': False},
                ]
            }
        ]
    }
    
    pdf_path = generate_test_execution_pdf(test_results)
    print(f"Test PDF generated at: {pdf_path}")