import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from pathlib import Path
import os
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import json

logger = logging.getLogger(__name__)

class MLTrainer:
    def __init__(self, model_path: str = None):
        # Always save model.pkl in the same directory as this script
        base_dir = Path(__file__).parent.resolve()
        if model_path is None:
            self.model_path = base_dir / "model.pkl"
        else:
            self.model_path = Path(model_path)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        
        self.label_encoder = LabelEncoder()
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.is_trained = False
        
    async def prepare_training_data(self, file_metadata_list: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data from file metadata"""
        if len(file_metadata_list) < 5:
            raise ValueError("Insufficient training data. Need at least 5 files.")
        
        logger.info(f"Preparing training data from {len(file_metadata_list)} files")        # Convert to DataFrame
        df = pd.DataFrame(file_metadata_list)

        # Feature engineering
        features_df = self._extract_features(df)

        # Generate labels based on file characteristics
        labels = self._generate_labels(df)

        # Encode categorical features
        features_encoded = self._encode_features(features_df)

        # Store feature columns for consistency
        self.feature_columns = features_encoded.columns.tolist()

        # Scale features
        features_scaled = self.scaler.fit_transform(features_encoded)

        # Encode labels
        labels_encoded = self.label_encoder.fit_transform(labels)

        logger.info(f"Training data prepared: {features_scaled.shape[0]} samples, {features_scaled.shape[1]} features")

        return features_scaled, labels_encoded
    
    def _extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract features from file metadata"""
        features = pd.DataFrame()

        # File size features
        features['file_size'] = df['size'].fillna(0)
        features['file_size_log'] = np.log1p(features['file_size'])
        features['size_category'] = pd.cut(features['file_size'],
                                          bins=[0, 1024, 1024*1024, 10*1024*1024, float('inf')],
                                          labels=['tiny', 'small', 'medium', 'large'])

        # Extension features (for encoding only)
        features['extension'] = df['extension'].fillna('')
        features['has_extension'] = (features['extension'] != '').astype(int)

        # MIME type features (for encoding only)
        features['mime_type'] = df['mime_type'].fillna('unknown')
        features['mime_category'] = features['mime_type'].apply(self._categorize_mime_type)

        # Entropy features (measure of randomness/encryption)
        features['entropy'] = df['entropy'].fillna(0)
        features['high_entropy'] = (features['entropy'] > 7.0).astype(int)

        # Time features
        if 'modified_time' in df.columns:
            # Robust datetime parsing for mixed formats
            df['modified_time'] = pd.to_datetime(df['modified_time'], format='mixed', errors='coerce')
            features['days_since_modified'] = (datetime.now() - df['modified_time']).dt.days
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

        # Hash features (if available)
        if 'hash_md5' in df.columns:
            features['has_hash'] = (df['hash_md5'].notna() & (df['hash_md5'] != '')).astype(int)
        else:
            features['has_hash'] = 0

        # Drop raw string columns after encoding step in _encode_features
        return features
    
    def _categorize_mime_type(self, mime_type: str) -> str:
        """Categorize MIME types into broad categories"""
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
    
    def _generate_labels(self, df: pd.DataFrame) -> List[str]:
        """Generate training labels based on file characteristics"""
        labels = []
        
        for _, row in df.iterrows():
            extension = row.get('extension', '').lower()
            size = row.get('size', 0)
            entropy = row.get('entropy', 0)
            mime_type = row.get('mime_type', '').lower()
            
            # Rule-based labeling for training
            if extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
                labels.append('images')
            elif extension in ['.mp4', '.avi', '.mkv', '.mov', '.wmv']:
                labels.append('videos')
            elif extension in ['.mp3', '.wav', '.flac', '.aac', '.ogg']:
                labels.append('audio')
            elif extension in ['.pdf', '.doc', '.docx', '.txt', '.rtf']:
                labels.append('documents')
            elif extension in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                labels.append('archives')
            elif extension in ['.py', '.js', '.html', '.css', '.cpp', '.java']:
                labels.append('code')
            elif extension in ['.exe', '.msi', '.dmg', '.deb', '.app']:
                labels.append('executables')
            elif size == 0:
                labels.append('empty')
            elif extension in ['.tmp', '.temp', '.log', '.cache']:
                labels.append('temporary')
            elif entropy > 7.5 and size > 1024:  # High entropy, potentially encrypted/packed
                labels.append('others')  # Map high-entropy files to others instead of suspicious
            else:
                labels.append('others')
        
        return labels
    
    def _encode_features(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Encode categorical features and drop raw string columns"""
        encoded_df = features_df.copy()

        # One-hot encode categorical columns
        categorical_columns = ['size_category', 'extension', 'mime_category']

        for col in categorical_columns:
            if col in encoded_df.columns:
                dummies = pd.get_dummies(encoded_df[col], prefix=col)
                encoded_df = pd.concat([encoded_df, dummies], axis=1)
                encoded_df.drop(col, axis=1, inplace=True)

        # Drop any remaining raw string columns (e.g., 'mime_type', 'extension' if not encoded)
        for col in list(encoded_df.columns):
            if encoded_df[col].dtype == object:
                encoded_df.drop(col, axis=1, inplace=True)

        # Convert boolean columns to int
        bool_columns = encoded_df.select_dtypes(include=[bool]).columns
        encoded_df[bool_columns] = encoded_df[bool_columns].astype(int)

        return encoded_df
    
    async def train_model(self, file_metadata_list: List[Dict]) -> Dict:
        """Train the ML model"""
        start_time = datetime.now()
        logger.info("Starting ML model training...")
        
        try:
            # Prepare training data
            X, y = await self.prepare_training_data(file_metadata_list)
            
            # Split data - check if stratification is possible
            try:
                # Count samples per class
                unique_labels, counts = np.unique(y, return_counts=True)
                min_class_size = min(counts)
                
                # Only use stratification if all classes have at least 2 samples
                if min_class_size >= 2:
                    X_train, X_test, y_train, y_test = train_test_split(
                        X, y, test_size=0.2, random_state=42, stratify=y
                    )
                else:
                    logger.warning(f"Smallest class has only {min_class_size} sample(s). Skipping stratification.")
                    X_train, X_test, y_train, y_test = train_test_split(
                        X, y, test_size=0.2, random_state=42
                    )
            except Exception as e:
                logger.warning(f"Stratification failed: {e}. Using random split.")
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
            
            # Train model
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Save model and encoders
            model_data = {
                'model': self.model,
                'label_encoder': self.label_encoder,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns,
                'training_metadata': {
                    'accuracy': accuracy,
                    'training_samples': len(X_train),
                    'test_samples': len(X_test),
                    'features_count': X.shape[1],
                    'classes': self.label_encoder.classes_.tolist(),
                    'trained_at': datetime.now().isoformat()
                }
            }
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            self.is_trained = True
            training_duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Model training completed. Accuracy: {accuracy:.3f}, Duration: {training_duration:.2f}s")
            
            return {
                'success': True,
                'accuracy': accuracy,
                'training_duration': training_duration,
                'features_count': X.shape[1],
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'model_version': '1.0'
            }
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'training_duration': (datetime.now() - start_time).total_seconds()
            }
    
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
            self.is_trained = True
            
            logger.info("Model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def get_model_info(self) -> Dict:
        """Get information about the current model"""
        if not self.is_trained:
            return {'trained': False}
        
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            return {
                'trained': True,
                'metadata': model_data.get('training_metadata', {}),
                'model_path': str(self.model_path),
                'feature_count': len(self.feature_columns)
            }
            
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {'trained': False, 'error': str(e)}

# Global trainer instance
ml_trainer = MLTrainer()

# CLI entry point for direct training
if __name__ == "__main__":
    import sys
    import asyncio
    from pathlib import Path


    # Try to find the latest scan CSV in logs/
    import glob
    import csv
    logs_dir = Path(__file__).parent.parent / "logs"
    csv_files = sorted(logs_dir.glob("scan_*.csv"), reverse=True)
    file_metadata_list = []

    if csv_files:
        latest_csv = csv_files[0]
        print(f"Loading scan data from: {latest_csv}")
        with open(latest_csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric fields
                for k in ["size", "entropy"]:
                    if k in row and row[k] != '':
                        try:
                            row[k] = float(row[k])
                        except Exception:
                            row[k] = 0
                file_metadata_list.append(row)

    if not file_metadata_list:
        print("No scan CSV data found in logs/. Please run a scan first.")
        sys.exit(1)

    # Train the model
    print(f"Training model on {len(file_metadata_list)} files...")
    result = asyncio.run(ml_trainer.train_model(file_metadata_list))
    if result.get("success"):
        print(f"Model trained successfully! Accuracy: {result['accuracy']:.2%}")
    else:
        print(f"Model training failed: {result.get('error')}")