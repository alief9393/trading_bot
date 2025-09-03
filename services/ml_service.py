# services/ml_service.py

import pandas as pd
import joblib

class MLService:
    """
    Service responsible for making predictions using a pre-trained ML model.
    This is the production version.
    """
    def __init__(self, model_path: str):
        try:
            self.model = joblib.load(model_path)
            # We need to know the feature names the model was trained on
            if hasattr(self.model, 'feature_names_in_'):
                self.feature_names = self.model.feature_names_in_
            else: # Fallback for older scikit-learn/xgboost versions
                self.feature_names = self.model.get_booster().feature_names
            print(f"MLService: Model loaded successfully from {model_path}.")
        except FileNotFoundError:
            print(f"MLService: FATAL ERROR - Model file not found at {model_path}.")
            self.model = None
        except Exception as e:
            print(f"MLService: An error occurred while loading the model: {e}")
            self.model = None

    # In services/ml_service.py

    def get_prediction(self, df: pd.DataFrame) -> int:
        if self.model is None or df is None or df.empty:
            print("MLService: Model not loaded or DataFrame is empty. Returning HOLD.")
            return 0

        # --- NEW: Set a confidence threshold ---
        CONFIDENCE_THRESHOLD = 0.60  # We will only trade if the model is 60% confident or more.
        # ------------------------------------

        latest_data = df.iloc[-1:]
        features_for_model = latest_data[self.feature_names]
        
        # --- NEW: Get probabilities instead of just the final prediction ---
        probabilities = self.model.predict(features_for_model)[0]
        # The output is an array like [prob_HOLD, prob_BUY, prob_SELL]
        # Example: [0.2, 0.7, 0.1]
        # -----------------------------------------------------------

        # Find the highest probability and its corresponding class
        max_probability = probabilities.max()
        predicted_class_mapped = probabilities.argmax()

        # --- NEW: The decision logic ---
        if max_probability < CONFIDENCE_THRESHOLD:
            # If the model is not confident enough, we override its decision to HOLD.
            print(f"MLService: Model prediction ({max_probability:.2f}) is below confidence threshold. Forcing HOLD.")
            return 0 # HOLD
        else:
            # If confidence is high enough, we use the model's prediction.
            if predicted_class_mapped == 1:
                prediction = 1 # BUY
            elif predicted_class_mapped == 2:
                prediction = -1 # SELL
            else:
                prediction = 0 # HOLD
            
            print(f"MLService: Real prediction generated: {prediction} with confidence {max_probability:.2f}")
            return prediction