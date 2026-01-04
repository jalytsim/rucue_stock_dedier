"""
Générateur de PDF pour reçus thermiques (58mm, 80mm)
Avec support multi-pages : en-tête sur page 1, footer sur dernière page
Total affiché en haut de page 1 + rappel en bas de dernière page
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm as mm_unit
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os

class ReceiptGenerator:
    def __init__(self, settings):
        self.settings = settings
        self.paper_width = float(settings.get('paper_width', '58'))  # mm
        
        # Définir la taille de page FIXE pour permettre la pagination
        # Format optimisé pour impression et agrafage
        if self.paper_width == 58:
            self.page_width = 105 * mm_unit
            self.page_height = 105 * mm_unit  # Hauteur fixe pour pagination
        else:  # 80mm
            self.page_width = 148 * mm_unit
            self.page_height = 148 * mm_unit  # Hauteur fixe pour pagination
        
        self.page_size = (self.page_width, self.page_height)
        self.margin = 3 * mm_unit
    
    def generate_receipt(self, receipt_data, output_path):
        """Générer un reçu PDF avec pagination automatique"""
        
        # Créer le document avec fonction de pagination personnalisée
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.page_size,
            leftMargin=self.margin,
            rightMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        # Construire le contenu
        story = []
        styles = self._get_styles()
        
        # ========== PAGE 1 : EN-TÊTE AVEC INFO CLIENT À GAUCHE ET ENTREPRISE À DROITE ==========
        
        # Créer un tableau pour layout côte à côte
        header_data = []
        
        # Colonne gauche : Info client
        left_content = []
        if receipt_data.get('client_name'):
            left_content.append(Paragraph("<b>CLIENT</b>", styles['LeftBold']))
            left_content.append(Paragraph(receipt_data['client_name'], styles['Left']))
            if receipt_data.get('client_phone'):
                left_content.append(Paragraph(f"Tél: {receipt_data['client_phone']}", styles['Left']))
        else:
            left_content.append(Paragraph("", styles['Left']))
        
        # Colonne droite : Info entreprise
        right_content = self._build_header(styles)
        
        # Créer le tableau avec deux colonnes
        col_width = (self.page_width - (2 * self.margin)) / 2
        header_table = Table(
            [[left_content, right_content]],
            colWidths=[col_width, col_width]
        )
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 3 * mm_unit))
        
        # Ligne de séparation
        story.append(self._create_line())
        story.append(Spacer(1, 2 * mm_unit))
        
        # Type de vente
        receipt_type = self.settings.get('receipt_type', 'Vente au détail')
        story.append(Paragraph(receipt_type, styles['Center']))
        story.append(Spacer(1, 2 * mm_unit))
        
        # Informations du reçu (N° et Date)
        story.extend(self._build_receipt_info(receipt_data, styles))
        story.append(Spacer(1, 2 * mm_unit))
        
        # Ligne de séparation
        story.append(self._create_line())
        story.append(Spacer(1, 2 * mm_unit))
        
        # ========== TOTAL À PAYER (EN HAUT DE PAGE 1) ==========
        story.extend(self._build_total_header(receipt_data, styles))
        story.append(Spacer(1, 3 * mm_unit))
        
        # Ligne de séparation
        story.append(self._create_line())
        story.append(Spacer(1, 2 * mm_unit))
        
        # ========== ARTICLES (AVEC PAGINATION AUTOMATIQUE) ==========
        story.append(Paragraph("<b>Liste des articles</b>", styles['CenterBold']))
        story.append(Spacer(1, 2 * mm_unit))
        
        # Articles - Pagination automatique, chaque article reste intact
        story.extend(self._build_items_paginated(receipt_data['items'], styles))
        
        # ========== FOOTER (UNIQUEMENT DERNIÈRE PAGE) ==========
        
        # Espacement avant footer
        story.append(Spacer(1, 5 * mm_unit))
        
        # Ligne de séparation avant footer
        story.append(self._create_line())
        story.append(Spacer(1, 2 * mm_unit))
        
        # Rappel du total (sur dernière page)
        story.extend(self._build_total_footer(receipt_data, styles))
        story.append(Spacer(1, 3 * mm_unit))
        
        # Montant en lettres (optionnel)
        if 'amount_in_words' in receipt_data:
            story.append(Paragraph(f"<i>{receipt_data['amount_in_words']}</i>", styles['Small']))
            story.append(Spacer(1, 3 * mm_unit))
        
        # Pied de page final
        story.append(self._create_line())
        story.append(Spacer(1, 2 * mm_unit))
        story.append(Paragraph("Merci pour votre achat!", styles['Center']))
        story.append(Paragraph("Mankasitraka Tompoko!", styles['CenterItalic']))
        
        # Générer le PDF avec gestion des pages
        doc.build(story, onFirstPage=self._on_first_page, onLaterPages=self._on_later_pages)
        
        return output_path
    
    def _on_first_page(self, canvas, doc):
        """Callback pour la première page - pas de footer de pagination"""
        pass
    
    def _on_later_pages(self, canvas, doc):
        """Callback pour les pages suivantes - numérotation"""
        canvas.saveState()
        
        # Numéro de page (en bas au centre)
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        
        canvas.setFont('Helvetica', 7 if self.paper_width == 58 else 8)
        canvas.drawCentredString(
            self.page_width / 2,
            10 * mm_unit,
            text
        )
        
        canvas.restoreState()
    
    def _get_styles(self):
        """Définir les styles"""
        styles = {}
        
        font_size = 7 if self.paper_width == 58 else 9
        
        styles['Header'] = ParagraphStyle(
            'Header',
            fontSize=font_size + 2,
            leading=font_size + 4,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        styles['Center'] = ParagraphStyle(
            'Center',
            fontSize=font_size,
            leading=font_size + 2,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        styles['CenterBold'] = ParagraphStyle(
            'CenterBold',
            fontSize=font_size,
            leading=font_size + 2,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        styles['CenterItalic'] = ParagraphStyle(
            'CenterItalic',
            fontSize=font_size - 1,
            leading=font_size + 1,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        )
        
        styles['Left'] = ParagraphStyle(
            'Left',
            fontSize=font_size,
            leading=font_size + 2,
            alignment=TA_LEFT,
            fontName='Helvetica'
        )
        
        styles['LeftBold'] = ParagraphStyle(
            'LeftBold',
            fontSize=font_size,
            leading=font_size + 2,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        )
        
        styles['Small'] = ParagraphStyle(
            'Small',
            fontSize=font_size - 1,
            leading=font_size + 1,
            alignment=TA_LEFT,
            fontName='Helvetica'
        )
        
        styles['Total'] = ParagraphStyle(
            'Total',
            fontSize=font_size + 3,
            leading=font_size + 5,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        return styles
    
    def _build_header(self, styles):
        """Construire l'en-tête (uniquement page 1) - retourne une liste d'éléments"""
        elements = []
        
        # Nom de l'entreprise
        company_name = self.settings.get('company_name', '')
        elements.append(Paragraph(f"<b>{company_name}</b>", styles['Header']))
        
        # Adresse
        address = self.settings.get('company_address', '').replace('\n', '<br/>')
        elements.append(Paragraph(address, styles['Center']))
        
        # Coordonnées
        phone = self.settings.get('company_phone', '')
        email = self.settings.get('company_email', '')
        if phone:
            elements.append(Paragraph(f"Tél: {phone}", styles['Center']))
        if email:
            elements.append(Paragraph(f"E-mail: {email}", styles['Center']))
        
        # Informations légales (petite taille)
        nif = self.settings.get('company_nif', '')
        stat = self.settings.get('company_stat', '')
        rc = self.settings.get('company_rc', '')
        ce = self.settings.get('company_ce', '')
        cif = self.settings.get('company_cif', '')
        
        if nif:
            elements.append(Paragraph(f"NIF: {nif}", styles['Small']))
        if stat:
            elements.append(Paragraph(f"STAT: {stat}", styles['Small']))
        if rc and ce:
            elements.append(Paragraph(f"R.C: {rc} - CE: {ce}", styles['Small']))
        if cif:
            elements.append(Paragraph(f"CIF: {cif}", styles['Small']))
        
        return elements
    
    def _build_receipt_info(self, receipt_data, styles):
        """Construire les infos du reçu"""
        elements = []
        
        # Numéro de facture
        elements.append(Paragraph(f"<b>N°: {receipt_data['receipt_number']}</b>", styles['Left']))
        
        # Date
        date_str = receipt_data['date']
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%d/%m/%Y')
        except:
            formatted_date = date_str
        
        elements.append(Paragraph(f"Date: {formatted_date}", styles['Left']))
        
        return elements
    
    def _build_client_info(self, receipt_data, styles):
        """Construire les infos client"""
        elements = []
        
        client_name = receipt_data.get('client_name', '')
        client_phone = receipt_data.get('client_phone', '')
        
        if client_name:
            elements.append(Paragraph(f"<b>Client:</b> {client_name}", styles['Left']))
        if client_phone:
            elements.append(Paragraph(f"Tél: {client_phone}", styles['Left']))
        
        return elements
    
    def _build_total_header(self, receipt_data, styles):
        """Construire l'affichage du total en haut de page 1"""
        elements = []
        
        currency = self.settings.get('currency', 'Ar')
        total = receipt_data['total']
        
        elements.append(Paragraph(f"<b>TOTAL À PAYER</b>", styles['CenterBold']))
        elements.append(Paragraph(f"<b>{total:,.2f} {currency}</b>", styles['Total']))
        
        return elements
    
    def _build_total_footer(self, receipt_data, styles):
        """Construire le rappel du total en bas de dernière page"""
        elements = []
        
        currency = self.settings.get('currency', 'Ar')
        total = receipt_data['total']
        
        elements.append(Paragraph(f"<b>TOTAL À PAYER (Rappel)</b>", styles['CenterBold']))
        elements.append(Paragraph(f"<b>{total:,.2f} {currency}</b>", styles['Total']))
        
        # Mode de paiement
        payment_method = receipt_data.get('payment_method', 'Espèces')
        elements.append(Spacer(1, 1 * mm_unit))
        elements.append(Paragraph(f"Paiement: {payment_method}", styles['Center']))
        
        return elements
    
    def _build_items_paginated(self, items, styles):
        """Construire la liste des articles avec pagination automatique"""
        elements = []
        
        currency = self.settings.get('currency', 'Ar')
        
        # Créer des groupes d'articles pour contrôler la pagination
        # Chaque article est un "bloc" qui ne sera pas coupé entre deux pages
        for i, item in enumerate(items, 1):
            # Créer un groupe pour cet article (ne sera pas coupé)
            item_elements = []
            
            # Numéro et nom du produit
            item_elements.append(Paragraph(f"<b>{i}. {item['name']}</b>", styles['Left']))
            
            # Quantité x Prix unitaire = Total
            qty_line = f"   {item['quantity']} x {item['unit_price']:,.2f} {currency} = <b>{item['total']:,.2f} {currency}</b>"
            item_elements.append(Paragraph(qty_line, styles['Left']))
            item_elements.append(Spacer(1, 2 * mm_unit))
            
            # Garder l'article ensemble (ne pas couper entre pages)
            elements.append(KeepTogether(item_elements))
        
        return elements
    
    def _create_line(self):
        """Créer une ligne de séparation"""
        line_width = self.page_width - (2 * self.margin)
        
        line_table = Table(
            [['']],
            colWidths=[line_width]
        )
        
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.black),
        ]))
        
        return line_table