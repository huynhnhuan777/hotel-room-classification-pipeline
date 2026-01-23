# Hotel Room Classification Project

A machine learning project for classifying hotel rooms into different categories using both traditional ML (Random Forest) and LLM-based approaches (Gemini API).

## 📋 Project Overview

This project implements classification models to categorize hotel rooms into 6 classes:
- **Deluxe** (0)
- **Executive** (1)
- **Luxury** (2)
- **Standard** (3)
- **Suite** (4)
- **Superior** (5)

The classification is based on various features including price, room size, amenities, bed types, and facility counts.

## 🗂️ Project Structure

```
.
├── classify_rooms_gemini.py    # Gemini API-based classification model setup
├── run_ml_model.py             # Random Forest training and prediction
├── train_model_only.py         # Random Forest training only (no predictions)
├── evaluate.py                 # Model evaluation script
├── error_analysis.py           # Error analysis and misclassification patterns
├── gemini_classification_model.json  # Saved Gemini model configuration
├── train.csv                   # Training dataset
├── val.csv                     # Validation dataset
├── train_with_prediction.csv   # Training data with predictions
├── val_with_prediction.csv     # Validation data with predictions
└── val_with_error_analysis.csv # Validation data with error analysis
```

## 🚀 Getting Started

### Step 1: Install Dependencies

**Option 1: Using requirements.txt (Recommended)**
```bash
pip install -r requirements.txt
```

**Option 2: Manual installation**
```bash
pip install pandas scikit-learn joblib numpy
```

For Gemini API (if using `classify_rooms_gemini.py`):
```bash
pip install google-generativeai
```

### Step 2: Prepare Data

Ensure you have the following CSV files in the project directory:
- `train.csv` - Training dataset (required)
- `val.csv` - Validation dataset (required for some scripts)

### Data Format

The CSV files should contain the following features:
- `Final Price`: Normalized final price
- `Max People`: Maximum occupancy (normalized)
- `Area_m2`: Room area in square meters (normalized)
- `price_per_m2`: Price per square meter (normalized)
- `m2_per_person`: Area per person (normalized)
- `num_facilities`: Number of facilities (normalized)
- `has_luxury_keyword`: Binary indicator for luxury keywords
- Bed type indicators: `is_king`, `is_queen`, `is_double`, `is_single`, `is_bunk`, `is_sofa`
- Amenity indicators: `has_wifi`, `has_ac`, `has_breakfast`, `has_tv`, `has_pool`, `has_balcony`, `has_parking`, `has_kitchen`, `has_fridge`
- `room_class`: Target variable (0-5)

## 📝 Scripts Description

### 1. `run_ml_model.py`
**Purpose**: Train Random Forest model and make predictions on both training and validation sets.

**Usage**:
```bash
python run_ml_model.py
```

**What it does**:
- Loads training data from `train.csv`
- Splits data into train/test sets (80/20)
- Trains a Random Forest classifier (300 estimators)
- Evaluates on test set
- Saves model to `room_class_model.pkl`
- Makes predictions on validation set (`val.csv`)
- Saves predictions to `val_with_prediction.csv` and `train_with_prediction.csv`

### 2. `train_model_only.py`
**Purpose**: Train Random Forest model without making predictions on validation data.

**Usage**:
```bash
python train_model_only.py
```

**What it does**:
- Loads training data from `train.csv`
- Splits data into train/test sets (80/20)
- Trains a Random Forest classifier
- Evaluates on test set only
- Saves model to `room_class_model.pkl`

### 3. `classify_rooms_gemini.py`
**Purpose**: Prepare a Gemini API-based classification model using few-shot learning.

**Usage**:
```bash
python classify_rooms_gemini.py
```

**What it does**:
- Loads training data from `train.csv`
- Prepares few-shot examples (up to 50 examples, balanced across classes)
- Builds a prompt template for Gemini API
- Saves model configuration to `gemini_classification_model.json`

**Note**: This script only prepares the model configuration. You'll need to implement the actual API calls separately.

### 4. `evaluate.py`
**Purpose**: Comprehensive evaluation of model predictions.

**Usage**:
```bash
python evaluate.py
```

**What it does**:
- Evaluates predictions on both training and validation sets
- Calculates accuracy, precision, recall, F1-score
- Shows confusion matrix
- Identifies top misclassifications
- Provides accuracy interpretation

**Requirements**: 
- `train_with_prediction.csv` and `val_with_prediction.csv` must exist

### 5. `error_analysis.py`
**Purpose**: Detailed error analysis and misclassification patterns.

**Usage**:
```bash
python error_analysis.py
```

**What it does**:
- Loads predictions from `val_with_prediction.csv`
- Calculates overall accuracy
- Analyzes error patterns by class
- Shows error rate per class
- Saves detailed analysis to `val_with_error_analysis.csv`

## 🔧 Configuration

### Model Parameters

**Random Forest** (in `run_ml_model.py` and `train_model_only.py`):
- `n_estimators`: 300
- `max_depth`: None (unlimited)
- `random_state`: 42
- `n_jobs`: -1 (use all CPU cores)

**Gemini Model** (in `classify_rooms_gemini.py`):
- Model: `models/gemini-flash-latest`
- Max training examples: 50
- Few-shot examples shown: 10

## 📊 Output Files

- `room_class_model.pkl`: Trained Random Forest model (pickle format)
- `gemini_classification_model.json`: Gemini model configuration
- `train_with_prediction.csv`: Training data with predictions
- `val_with_prediction.csv`: Validation data with predictions
- `val_with_error_analysis.csv`: Validation data with error analysis columns

## 🎯 Typical Workflow

### Quick Start (Recommended Order)

1. **Train the model and generate predictions**:
   ```bash
   python run_ml_model.py
   ```
   This will create:
   - `room_class_model.pkl` - Trained model
   - `train_with_prediction.csv` - Training predictions
   - `val_with_prediction.csv` - Validation predictions

2. **Evaluate model performance**:
   ```bash
   python evaluate.py
   ```
   Shows comprehensive metrics for both train and validation sets.

3. **Analyze error patterns**:
   ```bash
   python error_analysis.py
   ```
   Generates detailed error analysis saved to `val_with_error_analysis.csv`.

### Alternative: Train Only (No Predictions)
```bash
python train_model_only.py
```
Use this if you only want to train the model without generating predictions.

### Prepare Gemini Model Configuration
```bash
python classify_rooms_gemini.py
```
Creates `gemini_classification_model.json` for LLM-based classification.

---

## 📖 Detailed Instructions

For Vietnamese instructions, see `HUONG_DAN_CHAY.md`

## 📈 Model Performance

The Random Forest model typically achieves:
- High accuracy on training data
- Good generalization on validation data
- Balanced performance across all room classes

Use `evaluate.py` to see detailed metrics for your specific dataset.

## 🔍 Features Used

The model uses 22 features:
- **Price features**: Final Price, price_per_m2
- **Size features**: Area_m2, m2_per_person, Max People
- **Amenity features**: num_facilities, has_luxury_keyword
- **Bed type features**: is_king, is_queen, is_double, is_single, is_bunk, is_sofa
- **Facility features**: has_wifi, has_ac, has_breakfast, has_tv, has_pool, has_balcony, has_parking, has_kitchen, has_fridge

## 🤝 Contributing

Feel free to submit issues or pull requests for improvements.

## 📄 License

This project is open source and available for educational purposes.

## 🙏 Acknowledgments

- Uses scikit-learn for machine learning
- Uses Google Gemini API for LLM-based classification
- Built with pandas for data manipulation
