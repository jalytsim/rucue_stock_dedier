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
        # Comparer mot par mot : une recherche de sous-chaîne classait à tort
        # "RASOANIRINA" (contient "SA") ou "RAKOTONGA" (contient "ONG") en organisation
        words = re.findall(r"[\wÀ-ÿ]+", name.upper())
        keywords = set(NameFormatter.ORGANIZATION_KEYWORDS)
        return any(word in keywords for word in words)
    
    @staticmethod
    def format_person_name(name):
        """
        Formater un nom de personne
        Format: NOM Prénom1 P2.
        
        Exemples:
        - "Rabearisoa Marie Monique" → "RABEARISOA Marie M."
        - "rakoto jean paul" → "RAKOTO Jean P."
        - "ANDRIA Michel" → "ANDRIA Michel"
        """
        if not name or not name.strip():
            return name
        
        parts = name.strip().split()
        
        if len(parts) == 0:
            return name
        
        # Premier mot = NOM (en majuscule)
        formatted_parts = [parts[0].upper()]
        
        if len(parts) >= 2:
            # Deuxième mot = Prénom (capitalize)
            formatted_parts.append(parts[1].capitalize())
        
        if len(parts) >= 3:
            # Troisième mot et suivants = Initiales
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