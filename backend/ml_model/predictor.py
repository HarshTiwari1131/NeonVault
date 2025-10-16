import pickle
import numpy as np
import pandas as pd
from pathlib import Path
import logging
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)

class MLPredictor:
    def __init__(self, model_path: str = None):
        # Always load model.pkl from the ml_model directory, relative to this file
        base_dir = Path(__file__).parent.resolve()
        if model_path is None:
            self.model_path = base_dir / "model.pkl"
        else:
            self.model_path = Path(model_path)
        self.model = None
        self.label_encoder = None
        self.scaler = None
        self.feature_columns = []
        self.is_loaded = False
        # Try to load model on initialization
        self.load_model()
    
    def load_model(self) -> bool:
        """Load trained model from disk"""
        try:
            if not self.model_path.exists():
                logger.warning(f"Model file not found: {self.model_path}")
                return False
            
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.label_encoder = model_data['label_encoder']
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            self.is_loaded = True
            
            logger.info("ML model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            self.is_loaded = False
            return False
    
    def is_model_available(self) -> bool:
        """Check if model is loaded and ready for predictions"""
        return self.is_loaded and self.model is not None
    
    def predict_category(self, file_metadata: Dict) -> Dict:
        """Predict file category using ML model"""
        if not self.is_model_available():
            logger.warning("ML model not available for prediction")
            return {
                'category': 'others',
                'confidence': 0.0,
                'method': 'fallback',
                'probabilities': {}
            }
        
        try:
            # Extract and prepare features
            features = self._extract_features([file_metadata])
            features_encoded = self._encode_features(features)
            
            # Ensure feature columns match training data
            features_aligned = self._align_features(features_encoded)
            
            # Scale features
            features_scaled = self.scaler.transform(features_aligned)
            
            # Make prediction
            prediction = self.model.predict(features_scaled)[0]
            probabilities = self.model.predict_proba(features_scaled)[0]
            
            # Get category name
            category = self.label_encoder.inverse_transform([prediction])[0]
            confidence = max(probabilities)
            
            # Get all class probabilities
            class_probabilities = {}
            for i, prob in enumerate(probabilities):
                class_name = self.label_encoder.inverse_transform([i])[0]
                class_probabilities[class_name] = float(prob)
            
            return {
                'category': category,
                'confidence': float(confidence),
                'method': 'ml_model',
                'probabilities': class_probabilities
            }
            
        except Exception as e:
            logger.error(f"Error in ML prediction: {e}")
            # Fallback to rule-based prediction
            return self._fallback_prediction(file_metadata)
    
    def predict_anomaly(self, file_metadata: Dict) -> float:
        """Predict anomaly score (0-1, higher = more anomalous)"""
        if not self.is_model_available():
            return 0.0
        
        try:
            # Get prediction probabilities
            result = self.predict_category(file_metadata)
            probabilities = result['probabilities']
            
            # Calculate anomaly score based on:
            # 1. Low confidence in any category
            # 2. High entropy
            # 3. Suspicious characteristics
            
            max_probability = max(probabilities.values())
            entropy = file_metadata.get('entropy', 0)
            size = file_metadata.get('size', 0)
            extension = file_metadata.get('extension', '').lower()
            
            anomaly_score = 0.0
            
            # Low confidence indicates anomaly
            if max_probability < 0.5:
                anomaly_score += 0.3
            
            # High entropy (encrypted/packed files)
            if entropy > 7.5:
                anomaly_score += 0.4
            
            # Suspicious extensions
            suspicious_extensions = ['.exe', '.scr', '.bat', '.cmd', '.com', '.pif', '.vbs']
            if extension in suspicious_extensions:
                anomaly_score += 0.2
            
            # Very small or very large files
            if size < 100 or size > 100 * 1024 * 1024:  # < 100 bytes or > 100MB
                anomaly_score += 0.1
            
            return min(anomaly_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error in anomaly prediction: {e}")
            return 0.0
    
    def _extract_features(self, file_metadata_list: List[Dict]) -> pd.DataFrame:
        """Extract features from file metadata (same as trainer)"""
        df = pd.DataFrame(file_metadata_list)
        features = pd.DataFrame()
        
        # File size features
        features['file_size'] = df['size'].fillna(0)
        features['file_size_log'] = np.log1p(features['file_size'])
        features['size_category'] = pd.cut(features['file_size'], 
                                          bins=[0, 1024, 1024*1024, 10*1024*1024, float('inf')],
                                          labels=['tiny', 'small', 'medium', 'large'])
        
        # Extension features
        features['extension'] = df['extension'].fillna('')
        features['has_extension'] = (features['extension'] != '').astype(int)
        
        # MIME type features
        features['mime_type'] = df['mime_type'].fillna('unknown')
        features['mime_category'] = features['mime_type'].apply(self._categorize_mime_type)
        
        # Entropy features
        features['entropy'] = df['entropy'].fillna(0)
        features['high_entropy'] = (features['entropy'] > 7.0).astype(int)
        
        # Time features
        if 'modified_time' in df.columns:
            df['modified_time'] = pd.to_datetime(df['modified_time'])
            features['days_since_modified'] = (pd.Timestamp.now() - df['modified_time']).dt.days
            features['is_recent'] = (features['days_since_modified'] < 30).astype(int)
        else:
            features['days_since_modified'] = 0
            features['is_recent'] = 0
        
        # Path features
        if 'path' in df.columns:
            features['path_depth'] = df['path'].apply(lambda x: str(x).count(os.sep) if pd.notna(x) else 0)
            features['in_temp_folder'] = df['path'].apply(
                lambda x: any(temp in str(x).lower() for temp in ['temp', 'tmp', 'cache']) if pd.notna(x) else 0
            ).astype(int)
        else:
            features['path_depth'] = 0
            features['in_temp_folder'] = 0
        
        # Hash features
        if 'hash_md5' in df.columns:
            features['has_hash'] = (df['hash_md5'].notna() & (df['hash_md5'] != '')).astype(int)
        else:
            features['has_hash'] = 0
        
        return features
    
    def _categorize_mime_type(self, mime_type: str) -> str:
        """Categorize MIME types (same as trainer)"""
        if not mime_type or mime_type == 'unknown':
            return 'unknown'
        
        mime_lower = mime_type.lower()
        
        if mime_lower.startswith('image/'):
            return 'image'
        elif mime_lower.startswith('video/'):
            return 'video'
        elif mime_lower.startswith('audio/'):
            return 'audio'
        elif mime_lower.startswith('text/'):
            return 'text'
        elif 'pdf' in mime_lower:
            return 'document'
        elif 'office' in mime_lower or 'word' in mime_lower or 'excel' in mime_lower:
            return 'office'
        elif 'zip' in mime_lower or 'archive' in mime_lower:
            return 'archive'
        elif 'executable' in mime_lower or mime_lower.startswith('application/x-'):
            return 'executable'
        else:
            return 'other'
    
    def _encode_features(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Encode categorical features (same as trainer)"""
        encoded_df = features_df.copy()
        
        # One-hot encode categorical columns
        categorical_columns = ['size_category', 'extension', 'mime_category']
        
        for col in categorical_columns:
            if col in encoded_df.columns:
                dummies = pd.get_dummies(encoded_df[col], prefix=col)
                encoded_df = pd.concat([encoded_df, dummies], axis=1)
                encoded_df.drop(col, axis=1, inplace=True)
        
        # Convert boolean columns to int
        bool_columns = encoded_df.select_dtypes(include=[bool]).columns
        encoded_df[bool_columns] = encoded_df[bool_columns].astype(int)
        
        return encoded_df
    
    def _align_features(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Align features with training data columns"""
        # Add missing columns with zeros
        for col in self.feature_columns:
            if col not in features_df.columns:
                features_df[col] = 0
        
        # Remove extra columns and reorder to match training
        features_df = features_df[self.feature_columns]
        
        return features_df
    
    def _fallback_prediction(self, file_metadata: Dict) -> Dict:
        """Fallback rule-based prediction when ML model is not available"""
        extension = file_metadata.get('extension', '').lower()
        
        # Rule-based categorization
        if extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
            category = 'images'
        elif extension in ['.mp4', '.avi', '.mkv', '.mov', '.wmv']:
            category = 'videos'
        elif extension in ['.mp3', '.wav', '.flac', '.aac', '.ogg']:
            category = 'audio'
        elif extension in ['.pdf', '.doc', '.docx', '.txt', '.rtf']:
            category = 'documents'
        elif extension in ['.zip', '.rar', '.7z', '.tar', '.gz']:
            category = 'archives'
        elif extension in ['.py', '.js', '.html', '.css', '.cpp', '.java']:
            category = 'code'
        elif extension in ['.exe', '.msi', '.dmg', '.deb', '.app']:
            category = 'executables'
        else:
            category = 'others'
        
        return {
            'category': category,
            'confidence': 0.8,  # High confidence for rule-based
            'method': 'rule_based',
            'probabilities': {category: 0.8}
        }
    
    def get_feature_importance(self) -> Dict:
        """Get feature importance from the model"""
        if not self.is_model_available():
            return {}
        
        try:
            importances = self.model.feature_importances_
            feature_importance = {}
            
            for i, importance in enumerate(importances):
                if i < len(self.feature_columns):
                    feature_importance[self.feature_columns[i]] = float(importance)
            
            # Sort by importance
            sorted_importance = dict(sorted(feature_importance.items(), 
                                          key=lambda x: x[1], reverse=True))
            
            return sorted_importance
            
        except Exception as e:
            logger.error(f"Error getting feature importance: {e}")
            return {}

# Global predictor instance
ml_predictor = MLPredictor()