"""
Utilitaire pour formater les noms de clients
Supporte les personnes et les organisations
"""
import re


class NameFormatter:
    """Classe pour formater intelligemment les noms de clients"""
    
    # Mots-clés indiquant une organisation
    ORGANIZATION_KEYWORDS = [
        'EPP', 'CEG', 'LYCEE', 'LYCÉE', 'COLLEGE', 'COLLÈGE',
        'ECOLE', 'ÉCOLE', 'UNIVERSITE', 'UNIVERSITÉ',
        'ASSOCIATION', 'ONG', 'SARL', 'SA', 'EURL',
        'SOCIETE', 'SOCIÉTÉ', 'ENTREPRISE', 'MAGASIN',
        'BOUTIQUE', 'CENTRE', 'INSTITUT', 'CABINET',
        'HOPITAL', 'HÔPITAL', 'CLINIQUE', 'PHARMACIE',
        'ÉGLISE', 'EGLISE', 'TEMPLE', 'MOSQUÉE', 'MOSQUEE'
    ]
    
    @staticmethod
    def is_organization(name):
        """Déterminer si le nom est une organisation"""
        name_upper = name.upper()
        
        # Vérifier si un mot-clé d'organisation est présent
        for keyword in NameFormatter.ORGANIZATION_KEYWORDS:
            if keyword in name_upper:
                return True
        
        return False
        
    @staticmethod
    def format_person_name(name, max_total_length=20):
        """
        Formater un nom de personne
        Format: NOM Prénom1 P2.
        Si Nom+Prénom dépasse max_total_length, tronque le prénom pour que le total ≤ max_total_length

        Exemples:
        - "Rabearisoa Marie Monique" → "RABEARISOA Marie M."
        - "Rakoto Jean Paul" → "RAKOTO Jean P."
        """
        if not name or not name.strip():
            return name

        parts = name.strip().split()
        if len(parts) == 0:
            return name

        # Premier mot = NOM (en majuscule)
        nom = parts[0].upper()
        formatted_parts = [nom]

        # Déterminer le prénom
        prenom = parts[1].capitalize() if len(parts) >= 2 else ""

        # Tronquer le prénom si Nom+Prénom dépasse max_total_length
        if prenom:
            total_len = len(nom) + 1 + len(prenom)  # +1 pour l'espace
            if total_len > max_total_length:
                allowed_prenom_len = max_total_length - len(nom) - 1
                if allowed_prenom_len > 0:
                    prenom = prenom[:allowed_prenom_len]
                else:
                    prenom = ""
            formatted_parts.append(prenom)

        # Troisième mot et suivants = Initiales
        if len(parts) >= 3:
            for i in range(2, len(parts)):
                initial = parts[i][0].upper() + '.'
                formatted_parts.append(initial)

        return ' '.join(formatted_parts)

    
    @staticmethod
    def format_organization_name(name):
        """
        Formater un nom d'organisation
        Garde le format original mais nettoie les espaces
        
        Exemples:
        - "EPP Ambohipo" → "EPP Ambohipo"
        - "lycee technique" → "Lycée Technique"
        """
        if not name or not name.strip():
            return name
        
        # Nettoyer les espaces multiples
        name = ' '.join(name.split())
        
        # Capitaliser chaque mot pour les organisations
        words = name.split()
        formatted_words = []
        
        for word in words:
            # Garder les acronymes en majuscule
            if word.upper() in NameFormatter.ORGANIZATION_KEYWORDS:
                formatted_words.append(word.upper())
            else:
                formatted_words.append(word.capitalize())
        
        return ' '.join(formatted_words)
    
    @staticmethod
    def format_client_name(name):
        """
        Point d'entrée principal pour formater un nom de client
        Détecte automatiquement si c'est une personne ou une organisation
        """
        if not name or not name.strip():
            return name
        
        name = name.strip()
        
        if NameFormatter.is_organization(name):
            return NameFormatter.format_organization_name(name)
        else:
            return NameFormatter.format_person_name(name)


# Fonction helper pour utilisation simple
def format_client_name(name):
    """Fonction helper pour formater un nom de client"""
    return NameFormatter.format_client_name(name)


if __name__ == "__main__":
    # Tests
    test_cases = [
        "Rabearisoa Marie Monique",
        "rakoto jean paul",
        "ANDRIA Michel",
        "EPP Ambohipo",
        "lycee technique ampefiloha",
        "CEG Miarinarivo",
        "Association des Parents",
        "RASOANIRINA Paul",
        "Église Catholique",
        "pharmacie centrale"
    ]
    
    print("Tests de formatage:")
    print("=" * 60)
    for test in test_cases:
        formatted = format_client_name(test)
        org_marker = "📋 ORG" if NameFormatter.is_organization(test) else "👤 PERS"
        print(f"{org_marker} | {test:30s} → {formatted}")