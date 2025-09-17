"""
Manifest et versioning des artefacts ML.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from .config import ML_ARTIFACTS_DIR


class MLManifest:
    """Gestionnaire du manifest des artefacts ML."""
    
    def __init__(self):
        self.manifest_path = ML_ARTIFACTS_DIR / "manifest.json"
        self.manifest_data = self._load_manifest()
    
    def _load_manifest(self) -> Dict[str, Any]:
        """Charge le manifest existant ou crée un nouveau."""
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erreur lors du chargement du manifest: {e}")
        
        return {
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "artifacts": {},
            "models": {},
            "indexes": {},
        }
    
    def _save_manifest(self):
        """Sauvegarde le manifest."""
        try:
            self.manifest_data["updated_at"] = datetime.now().isoformat()
            
            with open(self.manifest_path, 'w', encoding='utf-8') as f:
                json.dump(self.manifest_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du manifest: {e}")
    
    def register_artifact(
        self,
        name: str,
        artifact_type: str,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Enregistre un artefact dans le manifest.
        
        Args:
            name: Nom de l'artefact
            artifact_type: Type d'artefact (model, index, embedding, etc.)
            file_path: Chemin du fichier
            metadata: Métadonnées supplémentaires
        """
        if metadata is None:
            metadata = {}
        
        artifact_info = {
            "name": name,
            "type": artifact_type,
            "file_path": file_path,
            "created_at": datetime.now().isoformat(),
            "file_size": Path(file_path).stat().st_size if Path(file_path).exists() else 0,
            "metadata": metadata,
        }
        
        self.manifest_data["artifacts"][name] = artifact_info
        self._save_manifest()
    
    def register_model(
        self,
        name: str,
        model_type: str,
        version: str,
        file_path: str,
        parameters: Optional[Dict[str, Any]] = None
    ):
        """
        Enregistre un modèle dans le manifest.
        
        Args:
            name: Nom du modèle
            model_type: Type de modèle (tfidf, embedding, etc.)
            version: Version du modèle
            file_path: Chemin du fichier
            parameters: Paramètres du modèle
        """
        if parameters is None:
            parameters = {}
        
        model_info = {
            "name": name,
            "type": model_type,
            "version": version,
            "file_path": file_path,
            "created_at": datetime.now().isoformat(),
            "file_size": Path(file_path).stat().st_size if Path(file_path).exists() else 0,
            "parameters": parameters,
        }
        
        self.manifest_data["models"][name] = model_info
        self._save_manifest()
    
    def register_index(
        self,
        name: str,
        index_type: str,
        file_path: str,
        document_count: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Enregistre un index dans le manifest.
        
        Args:
            name: Nom de l'index
            index_type: Type d'index (faiss, etc.)
            file_path: Chemin du fichier
            document_count: Nombre de documents indexés
            metadata: Métadonnées supplémentaires
        """
        if metadata is None:
            metadata = {}
        
        index_info = {
            "name": name,
            "type": index_type,
            "file_path": file_path,
            "document_count": document_count,
            "created_at": datetime.now().isoformat(),
            "file_size": Path(file_path).stat().st_size if Path(file_path).exists() else 0,
            "metadata": metadata,
        }
        
        self.manifest_data["indexes"][name] = index_info
        self._save_manifest()
    
    def get_artifact_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations d'un artefact.
        
        Args:
            name: Nom de l'artefact
            
        Returns:
            Informations de l'artefact ou None
        """
        return self.manifest_data["artifacts"].get(name)
    
    def get_model_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations d'un modèle.
        
        Args:
            name: Nom du modèle
            
        Returns:
            Informations du modèle ou None
        """
        return self.manifest_data["models"].get(name)
    
    def get_index_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations d'un index.
        
        Args:
            name: Nom de l'index
            
        Returns:
            Informations de l'index ou None
        """
        return self.manifest_data["indexes"].get(name)
    
    def list_artifacts(self) -> Dict[str, Any]:
        """
        Liste tous les artefacts.
        
        Returns:
            Dictionnaire des artefacts
        """
        return self.manifest_data["artifacts"]
    
    def list_models(self) -> Dict[str, Any]:
        """
        Liste tous les modèles.
        
        Returns:
            Dictionnaire des modèles
        """
        return self.manifest_data["models"]
    
    def list_indexes(self) -> Dict[str, Any]:
        """
        Liste tous les index.
        
        Returns:
            Dictionnaire des index
        """
        return self.manifest_data["indexes"]
    
    def get_manifest_summary(self) -> Dict[str, Any]:
        """
        Retourne un résumé du manifest.
        
        Returns:
            Résumé du manifest
        """
        return {
            "version": self.manifest_data["version"],
            "created_at": self.manifest_data["created_at"],
            "updated_at": self.manifest_data["updated_at"],
            "total_artifacts": len(self.manifest_data["artifacts"]),
            "total_models": len(self.manifest_data["models"]),
            "total_indexes": len(self.manifest_data["indexes"]),
            "artifacts": list(self.manifest_data["artifacts"].keys()),
            "models": list(self.manifest_data["models"].keys()),
            "indexes": list(self.manifest_data["indexes"].keys()),
        }
    
    def validate_artifacts(self) -> Dict[str, Any]:
        """
        Valide l'existence des artefacts enregistrés.
        
        Returns:
            Rapport de validation
        """
        validation_report = {
            "valid": True,
            "missing_files": [],
            "total_size": 0,
        }
        
        # Vérifier les artefacts
        for name, info in self.manifest_data["artifacts"].items():
            file_path = Path(info["file_path"])
            if not file_path.exists():
                validation_report["missing_files"].append(info["file_path"])
                validation_report["valid"] = False
            else:
                validation_report["total_size"] += file_path.stat().st_size
        
        # Vérifier les modèles
        for name, info in self.manifest_data["models"].items():
            file_path = Path(info["file_path"])
            if not file_path.exists():
                validation_report["missing_files"].append(info["file_path"])
                validation_report["valid"] = False
            else:
                validation_report["total_size"] += file_path.stat().st_size
        
        # Vérifier les index
        for name, info in self.manifest_data["indexes"].items():
            file_path = Path(info["file_path"])
            if not file_path.exists():
                validation_report["missing_files"].append(info["file_path"])
                validation_report["valid"] = False
            else:
                validation_report["total_size"] += file_path.stat().st_size
        
        return validation_report


# Instance globale du manifest
ml_manifest = MLManifest()

