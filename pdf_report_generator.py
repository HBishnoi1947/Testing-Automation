"""
PDF Report Generator for Test Execution Results
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, 
                                 Paragraph, Spacer, PageBreak)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from datetime import datetime
import os


def generate_test_execution_pdf(results: dict, output_path: str = None) -> str:
    """
    Generate a professional PDF report for test execution results with pie chart.
    
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
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=15,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    # Title
    story.append(Paragraph("Test Execution Report", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Date and Module Info
    info_data = [
        [Paragraph(f"<b>Date:</b> {results['execution_time']}", styles['Normal']),
         Paragraph(f"<b>Module:</b> {results['module_name']}", styles['Normal'])]
    ]
    info_table = Table(info_data, colWidths=[3.5*inch, 3.5*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ecf0f1')),
        ('PADDING', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.4*inch))
    
    # ========== RESULTS SUMMARY WITH PIE CHART ==========
    story.append(Paragraph("Results Summary", header_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Calculate totals
    total_events = sum(f['total_events'] for f in results['feature_results'])
    passed_events = sum(f['passed_events'] for f in results['feature_results'])
    failed_events = sum(f['failed_events'] for f in results['feature_results'])
    success_rate = (passed_events / total_events * 100) if total_events > 0 else 0
    
    # Create Pie Chart
    drawing = Drawing(400, 200)
    
    pie = Pie()
    pie.x = 125
    pie.y = 15
    pie.width = 180
    pie.height = 180
    
    # Handle case where all tests pass or fail
    if failed_events == 0:
        pie.data = [passed_events, 0.001]  # Tiny slice for visual
    elif passed_events == 0:
        pie.data = [0.001, failed_events]  # Tiny slice for visual
    else:
        pie.data = [passed_events, failed_events]
    
    pie.labels = [f'Success {success_rate:.0f}%', f'Failed {100-success_rate:.0f}%']
    pie.slices[0].fillColor = colors.HexColor('#27ae60')  # Green
    pie.slices[1].fillColor = colors.HexColor('#e74c3c')  # Red
    pie.slices[0].strokeColor = colors.white
    pie.slices[1].strokeColor = colors.white
    pie.slices[0].strokeWidth = 2
    pie.slices[1].strokeWidth = 2
    pie.slices[0].labelRadius = 1.35
    pie.slices[1].labelRadius = 1.35
    pie.slices[0].fontColor = colors.black
    pie.slices[1].fontColor = colors.black
    pie.slices[0].fontSize = 12
    pie.slices[1].fontSize = 12
    
    drawing.add(pie)
    story.append(drawing)
    story.append(Spacer(1, 0.3*inch))
    
    # Summary Statistics Boxes - FIXED VISIBILITY
    summary_boxes = [
        ['TOTAL', 'SUCCESS', 'FAILED'],
        [str(total_events), str(passed_events), str(failed_events)]
    ]
    
    summary_table = Table(summary_boxes, colWidths=[2.3*inch, 2.3*inch, 2.3*inch])
    summary_table.setStyle(TableStyle([
        # Header row (labels)
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#3498db')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#27ae60')),
        ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#e74c3c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('PADDING', (0, 0), (-1, 0), 12),
        # Value row (numbers)
        ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#5dade2')),
        ('BACKGROUND', (1, 1), (1, 1), colors.HexColor('#52c77a')),
        ('BACKGROUND', (2, 1), (2, 1), colors.HexColor('#ec7063')),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.white),
        ('FONTSIZE', (0, 1), (-1, 1), 20),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('PADDING', (0, 1), (-1, 1), 15),
        # Grid and borders
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('BOX', (0, 0), (-1, -1), 2, colors.white),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.5*inch))
    
    # ========== FEATURE DETAILS ==========
    story.append(Paragraph("Feature Details", header_style))
    story.append(Spacer(1, 0.2*inch))
    
    for idx, feature in enumerate(results['feature_results'], 1):
        # Feature header with status
        status_text = "✓ Success" if feature['success'] else "✗ Failed"
        status_color = colors.HexColor('#27ae60') if feature['success'] else colors.HexColor('#e74c3c')
        
        feature_header = f"<b>Feature {idx}: {feature['feature_name']}</b> - <font color='#{status_color.hexval()[2:]}'>{status_text}</font>"
        story.append(Paragraph(feature_header, styles['Heading3']))
        story.append(Spacer(1, 0.15*inch))
        
        # Events table - ONLY 3 COLUMNS (Event, Operation, Status)
        if feature['event_results']:
            event_data = [['Event', 'Operation', 'Status']]
            
            for event in feature['event_results']:
                status = '✓ Pass' if event['success'] else '✗ Fail'
                
                event_data.append([
                    f"event {event['event_number']}",
                    event['operation'],
                    status
                ])
            
            # Table with 3 columns only
            events_table = Table(event_data, colWidths=[1.8*inch, 3*inch, 2*inch])
            
            # Build dynamic table style
            table_style = [
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                # Data rows
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('PADDING', (0, 1), (-1, -1), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]
            
            # Color code rows based on pass/fail
            for row_idx, event in enumerate(feature['event_results'], 1):
                if event['success']:
                    bg_color = colors.HexColor('#d5f4e6')  # Light green
                else:
                    bg_color = colors.HexColor('#fadbd8')  # Light red
                table_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), bg_color))
            
            events_table.setStyle(TableStyle(table_style))
            story.append(events_table)
        else:
            story.append(Paragraph("<i>No events found for this feature</i>", styles['Italic']))
        
        story.append(Spacer(1, 0.35*inch))
    
    # Build PDF
    doc.build(story)
    print(f"[✓] PDF Report generated: {output_path}")
    
    return output_path


# Test function (optional - remove in production)
if __name__ == "__main__":
    # Sample data for testing
    test_results = {
        'module_name': 'User Authentication Module',
        'execution_time': '2025-11-01 22:33:30',
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