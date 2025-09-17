"""
Commande Django pour construire l'index RAG.
"""

from django.core.management.base import BaseCommand, CommandError
from ml.rag import RAGAssistant, RAGDocument
from ml.manifest import ml_manifest
import os
import json


class Command(BaseCommand):
    help = 'Construit l\'index RAG pour l\'assistant'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la reconstruction même si l\'index existe',
        )
        parser.add_argument(
            '--data-dir',
            type=str,
            default='data/rag',
            help='Répertoire contenant les documents RAG',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🤖 Début de la construction de l\'index RAG...')
        )
        
        try:
            # Créer l'assistant RAG
            rag_assistant = RAGAssistant()
            
            # Charger les documents depuis le répertoire
            data_dir = options['data_dir']
            if not os.path.exists(data_dir):
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Répertoire {data_dir} non trouvé. Création des documents de démonstration...')
                )
                self._create_demo_documents(rag_assistant)
            else:
                self._load_documents_from_dir(rag_assistant, data_dir)
            
            # Enregistrer dans le manifest
            self.stdout.write('📋 Mise à jour du manifest...')
            ml_manifest.register_index(
                name='rag_index',
                index_type='faiss_rag',
                file_path=str(rag_assistant.rag_index.rag_index_path),
                document_count=len(rag_assistant.rag_index.documents),
                metadata={
                    'chunk_size': 500,
                    'chunk_overlap': 50,
                    'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2',
                }
            )
            
            self.stdout.write(
                self.style.SUCCESS('✅ Index RAG construit avec succès')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors de la construction: {e}')
            )
            raise CommandError(f'Échec de la construction de l\'index RAG: {e}')
    
    def _create_demo_documents(self, rag_assistant):
        """Crée des documents de démonstration pour le RAG."""
        
        demo_documents = [
            RAGDocument(
                content="""
                Politique de retour SmartMarket
                
                Vous avez 30 jours pour retourner un produit non alimentaire en parfait état.
                Les produits alimentaires ne peuvent pas être retournés pour des raisons d'hygiène.
                
                Pour effectuer un retour :
                1. Connectez-vous à votre compte
                2. Allez dans "Mes commandes"
                3. Sélectionnez la commande concernée
                4. Cliquez sur "Demander un retour"
                
                Les frais de retour sont à votre charge, sauf en cas de défaut du produit.
                Le remboursement sera effectué sous 5-7 jours ouvrés après réception du retour.
                """,
                metadata={
                    'type': 'policy',
                    'category': 'returns',
                    'title': 'Politique de retour',
                    'version': '1.0',
                }
            ),
            
            RAGDocument(
                content="""
                Livraison et expédition SmartMarket
                
                Nous livrons partout en France métropolitaine.
                Délais de livraison :
                - Standard : 3-5 jours ouvrés
                - Express : 1-2 jours ouvrés
                - Point relais : 2-4 jours ouvrés
                
                Frais de livraison :
                - Gratuit à partir de 50€ d'achat
                - Standard : 4.90€
                - Express : 9.90€
                - Point relais : 2.90€
                
                Vous recevrez un email de confirmation avec le numéro de suivi.
                """,
                metadata={
                    'type': 'policy',
                    'category': 'shipping',
                    'title': 'Livraison et expédition',
                    'version': '1.0',
                }
            ),
            
            RAGDocument(
                content="""
                Guide d'achat - Électronique
                
                Avant d'acheter un produit électronique, vérifiez :
                - La compatibilité avec vos appareils existants
                - Les spécifications techniques
                - La garantie constructeur
                - Les avis clients
                
                Nos produits électroniques sont garantis 2 ans minimum.
                En cas de problème, contactez notre service client.
                
                Conseils d'utilisation :
                - Lisez toujours le manuel d'utilisation
                - Respectez les conditions d'utilisation
                - Évitez les chocs et l'humidité
                """,
                metadata={
                    'type': 'guide',
                    'category': 'electronics',
                    'title': 'Guide d\'achat électronique',
                    'version': '1.0',
                }
            ),
            
            RAGDocument(
                content="""
                Guide d'achat - Mode et vêtements
                
                Pour bien choisir vos vêtements :
                - Consultez notre guide des tailles
                - Vérifiez la composition des matières
                - Lisez les conseils d'entretien
                
                Tailles disponibles :
                - Homme : XS à XXL
                - Femme : 34 à 48
                - Enfant : 2 ans à 16 ans
                
                Retour gratuit sous 30 jours pour les vêtements.
                Essayez vos vêtements avant de retirer les étiquettes.
                """,
                metadata={
                    'type': 'guide',
                    'category': 'fashion',
                    'title': 'Guide d\'achat mode',
                    'version': '1.0',
                }
            ),
            
            RAGDocument(
                content="""
                FAQ SmartMarket
                
                Q: Comment créer un compte ?
                R: Cliquez sur "S'inscrire" en haut à droite, remplissez le formulaire.
                
                Q: Comment modifier ma commande ?
                R: Vous pouvez modifier votre commande tant qu'elle n'est pas expédiée.
                
                Q: Comment contacter le service client ?
                R: Par email à contact@smartmarket.fr ou par téléphone au 01 23 45 67 89.
                
                Q: Puis-je annuler ma commande ?
                R: Oui, dans les 2 heures suivant la commande.
                
                Q: Quels moyens de paiement acceptez-vous ?
                R: Carte bancaire, PayPal, virement bancaire, chèque.
                """,
                metadata={
                    'type': 'faq',
                    'category': 'general',
                    'title': 'FAQ générale',
                    'version': '1.0',
                }
            ),
        ]
        
        self.stdout.write(f'📄 Ajout de {len(demo_documents)} documents de démonstration...')
        rag_assistant.add_knowledge_base(demo_documents)
    
    def _load_documents_from_dir(self, rag_assistant, data_dir):
        """Charge les documents depuis un répertoire."""
        
        documents = []
        
        for filename in os.listdir(data_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(data_dir, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        for item in data:
                            doc = RAGDocument(
                                content=item.get('content', ''),
                                metadata=item.get('metadata', {})
                            )
                            documents.append(doc)
                    else:
                        doc = RAGDocument(
                            content=data.get('content', ''),
                            metadata=data.get('metadata', {})
                        )
                        documents.append(doc)
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Erreur lors du chargement de {filename}: {e}')
                    )
        
        if documents:
            self.stdout.write(f'📄 Ajout de {len(documents)} documents...')
            rag_assistant.add_knowledge_base(documents)
        else:
            self.stdout.write(
                self.style.WARNING('⚠️ Aucun document trouvé. Création des documents de démonstration...')
            )
            self._create_demo_documents(rag_assistant)

