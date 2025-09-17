"""
Prétraitement des textes pour le ML.
"""

import re
import string
from typing import List, Optional

import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer

# Télécharger les ressources NLTK nécessaires
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Configuration
FRENCH_STOPWORDS = set(stopwords.words('french'))
STEMMER = SnowballStemmer('french')


def clean_text(text: str) -> str:
    """
    Nettoie un texte en supprimant la ponctuation et normalisant.
    
    Args:
        text: Texte à nettoyer
        
    Returns:
        Texte nettoyé
    """
    if not text:
        return ""
    
    # Convertir en minuscules
    text = text.lower()
    
    # Supprimer la ponctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Supprimer les chiffres
    text = re.sub(r'\d+', '', text)
    
    # Supprimer les espaces multiples
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def tokenize_text(text: str) -> List[str]:
    """
    Tokenise un texte en mots.
    
    Args:
        text: Texte à tokeniser
        
    Returns:
        Liste des tokens
    """
    if not text:
        return []
    
    # Nettoyer le texte
    text = clean_text(text)
    
    # Tokeniser
    tokens = nltk.word_tokenize(text, language='french')
    
    # Supprimer les stopwords et les tokens vides
    tokens = [
        token for token in tokens 
        if token not in FRENCH_STOPWORDS and len(token) > 2
    ]
    
    return tokens


def stem_tokens(tokens: List[str]) -> List[str]:
    """
    Applique le stemming sur une liste de tokens.
    
    Args:
        tokens: Liste des tokens
        
    Returns:
        Liste des tokens stemmés
    """
    return [STEMMER.stem(token) for token in tokens]


def preprocess_text(text: str, stem: bool = True) -> str:
    """
    Prétraite un texte complet.
    
    Args:
        text: Texte à prétraiter
        stem: Si True, applique le stemming
        
    Returns:
        Texte prétraité
    """
    if not text:
        return ""
    
    # Tokeniser
    tokens = tokenize_text(text)
    
    # Appliquer le stemming si demandé
    if stem:
        tokens = stem_tokens(tokens)
    
    return " ".join(tokens)


def create_product_text(product) -> str:
    """
    Crée un texte composite pour un produit en combinant différents champs.
    
    Args:
        product: Instance du modèle Product
        
    Returns:
        Texte composite du produit
    """
    # Pondération des champs
    title_weight = 3
    category_weight = 2
    description_weight = 1
    
    # Construire le texte pondéré
    text_parts = []
    
    # Titre (pondéré)
    if product.name:
        text_parts.extend([product.name] * title_weight)
    
    # Catégorie (pondéré)
    if product.category and product.category.name:
        text_parts.extend([product.category.name] * category_weight)
    
    # Description (pondérée)
    if product.description:
        text_parts.extend([product.description] * description_weight)
    
    # Combiner tous les éléments
    combined_text = " ".join(text_parts)
    
    return preprocess_text(combined_text, stem=True)

