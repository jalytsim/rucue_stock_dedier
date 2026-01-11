"""
Générateur de PDF pour reçus - Support A6 et Thermal (58mm, 80mm)
Optimisé pour Ubuntu Server avec pagination automatique
En-tête style thermique : Client à gauche, Société à droite
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A6
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm as mm_unit
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime

class ReceiptGenerator:
    def __init__(self, settings):
        self.settings = settings
        self.paper_width = float(settings.get('paper_width', '58'))  # mm
        
        # Définir la taille de page selon le format
        if self.paper_width == 58:
            # Format thermal 58mm -> Impression A6 pour agrafage
            self.page_width = 105 * mm_unit
            self.page_height = 148 * mm_unit
        else:  # 80mm
            # Format thermal 80mm -> Impression A6 pour agrafage
            self.page_width = 105 * mm_unit
            self.page_height = 148 * mm_unit
        
        self.page_size = (self.page_width, self.page_height)
        self.margin = 3 * mm_unit
    
    def generate_receipt(self, receipt_data, output_path):
        """Générer un reçu PDF optimisé avec pagination automatique"""
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.page_size,
            leftMargin=self.margin,
            rightMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        story = []
        styles = self._get_styles()
        
        # ========== EN-TÊTE STYLE THERMIQUE (CLIENT | SOCIÉTÉ) ==========
        story.extend(self._build_thermal_style_header(receipt_data, styles))
        
        # ========== ARTICLES AVEC PAGINATION ==========
        story.extend(self._build_items_optimized(receipt_data['items'], styles))
        
        # ========== FOOTER ==========
        story.append(Spacer(1, 3 * mm_unit))
        story.append(self._create_line())
        story.append(Spacer(1, 1 * mm_unit))
        
        story.extend(self._build_total_footer(receipt_data, styles))
        
        story.append(Spacer(1, 2 * mm_unit))
        story.append(Paragraph("Merci pour votre achat!", styles['CenterSmall']))
        story.append(Paragraph("Mankasitraka Tompoko!", styles['CenterItalicSmall']))
        
        doc.build(story, onLaterPages=self._on_later_pages)
        
        return output_path
    
    def _on_later_pages(self, canvas, doc):
        """Numérotation des pages (pages 2+)"""
        canvas.saveState()
        page_num = canvas.getPageNumber()
        if page_num > 1:
            canvas.setFont('Helvetica', 6)
            canvas.drawCentredString(
                self.page_width / 2,
                8 * mm_unit,
                f"Page {page_num}"
            )
        canvas.restoreState()
    
    def _get_styles(self):
        """Styles optimisés pour A6"""
        styles = {}
        
        # En-têtes
        styles['HeaderBold'] = ParagraphStyle(
            'HeaderBold',
            fontSize=8,
            leading=9,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        )
        
        styles['HeaderBoldRight'] = ParagraphStyle(
            'HeaderBoldRight',
            fontSize=8,
            leading=9,
            alignment=TA_RIGHT,
            fontName='Helvetica-Bold'
        )
        
        # Texte très petit (infos légales)
        styles['Tiny'] = ParagraphStyle(
            'Tiny',
            fontSize=5,
            leading=6,
            alignment=TA_LEFT,
            fontName='Helvetica'
        )
        
        styles['TinyRight'] = ParagraphStyle(
            'TinyRight',
            fontSize=5,
            leading=6,
            alignment=TA_RIGHT,
            fontName='Helvetica'
        )
        
        # Texte petit (articles)
        styles['Small'] = ParagraphStyle(
            'Small',
            fontSize=6,
            leading=7,
            alignment=TA_LEFT,
            fontName='Helvetica'
        )
        
        styles['SmallBold'] = ParagraphStyle(
            'SmallBold',
            fontSize=6,
            leading=7,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        )
        
        # Centré
        styles['Center'] = ParagraphStyle(
            'Center',
            fontSize=6,
            leading=7,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        styles['CenterBold'] = ParagraphStyle(
            'CenterBold',
            fontSize=7,
            leading=8,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        styles['CenterSmall'] = ParagraphStyle(
            'CenterSmall',
            fontSize=6,
            leading=7,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        styles['CenterItalicSmall'] = ParagraphStyle(
            'CenterItalicSmall',
            fontSize=5,
            leading=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        )
        
        # Total (gros)
        styles['Total'] = ParagraphStyle(
            'Total',
            fontSize=10,
            leading=11,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        return styles
    
    def _build_thermal_style_header(self, receipt_data, styles):
        """
        En-tête style thermique : Client à gauche, Société à droite
        Format optimisé pour maximiser l'espace (8-10 articles page 1)
        """
        elements = []
        col_width = (self.page_width - (2 * self.margin)) / 2
        
        # ========== LIGNE 1 : CLIENT | NOM SOCIÉTÉ ==========
        left_col = [Paragraph("<b>CLIENT</b>", styles['HeaderBold'])]
        right_col = [Paragraph(f"<b>{self.settings.get('company_name', '')}</b>", styles['HeaderBoldRight'])]
        
        header_table = Table([[left_col, right_col]], colWidths=[col_width, col_width])
        header_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        elements.append(header_table)
        
        # ========== LIGNE 2 : NOM CLIENT | TÉL SOCIÉTÉ ==========
        client_name = receipt_data.get('client_name', '(Non spécifié)')
        company_phone = self.settings.get('company_phone', '')
        
        left_col = [Paragraph(client_name, styles['Tiny'])]
        right_col = [Paragraph(company_phone, styles['TinyRight'])]
        
        line2_table = Table([[left_col, right_col]], colWidths=[col_width, col_width])
        line2_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        elements.append(line2_table)
        
        # ========== LIGNE 3 : TÉL CLIENT | NIF SOCIÉTÉ ==========
        client_phone = receipt_data.get('client_phone', '')
        nif = self.settings.get('company_nif', '')
        
        left_col = [Paragraph(client_phone, styles['Tiny'])]
        right_col = [Paragraph(f"NIF: {nif}" if nif else "", styles['TinyRight'])]
        
        line3_table = Table([[left_col, right_col]], colWidths=[col_width, col_width])
        line3_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        elements.append(line3_table)
        
        # ========== LIGNE 4 : VIDE | STAT ==========
        stat = self.settings.get('company_stat', '')
        if stat:
            left_col = [Paragraph("", styles['Tiny'])]
            right_col = [Paragraph(f"STAT: {stat}", styles['TinyRight'])]
            
            stat_table = Table([[left_col, right_col]], colWidths=[col_width, col_width])
            stat_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
            elements.append(stat_table)
        
        # ========== LIGNES SUIVANTES : VIDE | ADRESSE ==========
        address = self.settings.get('company_address', '')
        for line in address.split('\n'):
            if line.strip():
                left_col = [Paragraph("", styles['Tiny'])]
                right_col = [Paragraph(line.strip(), styles['TinyRight'])]
                
                addr_table = Table([[left_col, right_col]], colWidths=[col_width, col_width])
                addr_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
                elements.append(addr_table)
        
        elements.append(Spacer(1, 0.5 * mm_unit))
        elements.append(self._create_line())
        elements.append(Spacer(1, 0.5 * mm_unit))
        
        # ========== N° FACTURE | DATE (SUR UNE LIGNE) ==========
        date_str = receipt_data['date']
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%d/%m/%Y')
        except:
            formatted_date = date_str
        
        left_col = [Paragraph(f"<b>No: {receipt_data['receipt_number']}</b>", styles['SmallBold'])]
        right_col = [Paragraph(f"<b>Date: {formatted_date}</b>", styles['SmallBold'])]
        
        info_table = Table([[left_col, right_col]], colWidths=[col_width, col_width])
        info_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        elements.append(info_table)
        
        elements.append(Spacer(1, 0.5 * mm_unit))
        elements.append(self._create_line())
        elements.append(Spacer(1, 1 * mm_unit))
        
        # ========== TOTAL À PAYER ==========
        currency = self.settings.get('currency', 'Ar')
        total = receipt_data['total']
        elements.append(Paragraph("TOTAL À PAYER", styles['CenterBold']))
        elements.append(Paragraph(f"{total:,.0f} {currency}", styles['Total']))
        
        elements.append(Spacer(1, 1 * mm_unit))
        elements.append(self._create_line())
        elements.append(Spacer(1, 1 * mm_unit))
        
        # ========== TITRE LISTE ARTICLES ==========
        elements.append(Paragraph("<b>LISTE DES ARTICLES</b>", styles['CenterBold']))
        elements.append(Spacer(1, 1 * mm_unit))
        
        return elements
    
    def _build_items_optimized(self, items, styles):
        """
        Articles ultra-compacts - 2 lignes par article
        Permet 8-10 articles page 1, 14+ articles pages suivantes
        """
        elements = []
        
        currency = self.settings.get('currency', 'Ar')
        
        for i, item in enumerate(items, 1):
            item_elements = []
            
            # Ligne 1: N° + Nom (tronqué si nécessaire)
            name = item['name']
            if len(name) > 35:
                name = name[:32] + "..."
            
            item_elements.append(
                Paragraph(f"{i}. {name}", styles['SmallBold'])
            )
            
            # Ligne 2: Qté x Prix = Total
            qty = item['quantity']
            unit = item['unit_price']
            total = item['total']
            
            detail = f"   {qty:.0f} x {unit:,.0f} = <b>{total:,.0f} {currency}</b>"
            item_elements.append(
                Paragraph(detail, styles['Small'])
            )
            
            # Micro-espace entre articles (0.5mm)
            item_elements.append(Spacer(1, 0.5 * mm_unit))
            
            # Garder l'article ensemble (pas de coupure entre pages)
            elements.append(KeepTogether(item_elements))
        
        return elements
    
    def _build_total_footer(self, receipt_data, styles):
        """Footer avec rappel du total"""
        elements = []
        
        currency = self.settings.get('currency', 'Ar')
        total = receipt_data['total']
        
        elements.append(Paragraph("TOTAL À PAYER", styles['CenterBold']))
        elements.append(Paragraph(f"{total:,.0f} {currency}", styles['Total']))
        
        payment_method = receipt_data.get('payment_method', 'Espèces')
        elements.append(Spacer(1, 0.5 * mm_unit))
        elements.append(Paragraph(f"Paiement: {payment_method}", styles['Center']))
        
        return elements
    
    def _create_line(self):
        """Ligne de séparation fine"""
        line_width = self.page_width - (2 * self.margin)
        
        line_table = Table([['']],colWidths=[line_width])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 0.3, colors.black),
        ]))
        
        return line_table