# MACHINE LEARNING APPLICATION
# Streamlit + Scikit-Learn
import io
import pickle
import warnings
import numpy as np
import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer, SimpleImputer
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

# Regression
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR

# Classification
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC

# Metrics
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
)

warnings.filterwarnings("ignore")


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Machine Learning Application",
    page_icon="🤖",
    layout="wide",
)


# ============================================================
# TITLE
# ============================================================

st.title("🤖 Machine Learning Application")

st.markdown(
    """
    ### Welcome! 👋

    This application allows you to:

    - Upload your own dataset
    - Use an example dataset
    - Explore your data
    - Select features and target
    - Automatically detect Regression or Classification
    - Preprocess numerical and categorical data
    - Train multiple Scikit-Learn models
    - Compare model performance
    - View confusion matrix and ROC curve
    - Download the best trained model
    - Make predictions
    """
)


# ============================================================
# LOAD EXAMPLE DATASETS
# ============================================================

@st.cache_data
def load_example_dataset(dataset_name):

    if dataset_name == "Titanic":
        return sns.load_dataset("titanic")

    elif dataset_name == "Tips":
        return sns.load_dataset("tips")

    elif dataset_name == "Iris":
        return sns.load_dataset("iris")

    return None

# LOAD UPLOADED FILE

@st.cache_data
def load_uploaded_file(file_bytes, file_name):

    extension = file_name.lower().split(".")[-1]

    buffer = io.BytesIO(file_bytes)

    if extension == "csv":
        return pd.read_csv(buffer)

    elif extension in ["xlsx", "xls"]:
        return pd.read_excel(buffer)

    elif extension == "tsv":
        return pd.read_csv(buffer, sep="\t")

    elif extension == "json":
        return pd.read_json(buffer)

    else:
        raise ValueError(
            "Unsupported file format. "
            "Use CSV, XLSX, XLS, TSV or JSON."
        )

# SIDEBAR

st.sidebar.header("📂 Data Source")
data_source = st.sidebar.radio(
    "Choose data source:",
    [
        "Use Example Dataset",
        "Upload Your Dataset",
    ],
)

# LOAD DATA

df = None
if data_source == "Use Example Dataset":
    dataset_name = st.sidebar.selectbox(
        "Select Example Dataset",
        [
            "Titanic",
            "Tips",
            "Iris",
        ],
    )
    try:

        df = load_example_dataset(dataset_name)

        if df is not None:

            st.sidebar.success(
                f"{dataset_name} dataset loaded."
            )

    except Exception as e:

        st.error(
            "Could not load the example dataset."
        )

        st.error(
            f"Details: {e}"
        )

else:

    uploaded_file = st.sidebar.file_uploader(
        "Upload your dataset",
        type=[
            "csv",
            "xlsx",
            "xls",
            "tsv",
            "json",
        ],
    )

    if uploaded_file is not None:

        try:

            df = load_uploaded_file(
                uploaded_file.getvalue(),
                uploaded_file.name,
            )

            st.sidebar.success(
                "Dataset uploaded successfully!"
            )

        except Exception as e:

            st.error(
                f"Error reading file: {e}"
            )

# STOP IF NO DATA

if df is None:

    st.info(
        "👈 Select an example dataset or upload your dataset "
        "from the sidebar."
    )

    st.stop()

# CLEAN DATA

df = df.copy()

df.columns = df.columns.astype(str).str.strip()

# Remove completely empty columns
df = df.dropna(axis=1, how="all")

# Remove completely empty rows
df = df.dropna(axis=0, how="all").reset_index(drop=True)


if df.empty:

    st.error(
        "The dataset is empty after removing empty rows and columns."
    )

    st.stop()

# DATASET INFORMATION

st.header("📊 Dataset Information")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Rows",
        df.shape[0],
    )

with col2:
    st.metric(
        "Columns",
        df.shape[1],
    )

with col3:
    st.metric(
        "Missing Values",
        int(df.isnull().sum().sum()),
    )

# DATA HEAD

st.subheader("🔹 Data Head")

st.dataframe(
    df.head(),
    use_container_width=True,
)

# DATA SHAPE

st.subheader("🔹 Data Shape")

st.write(df.shape)

# COLUMN NAMES

st.subheader("🔹 Column Names")

st.write(
    list(df.columns)
)

# DATA DESCRIPTION

st.subheader("🔹 Data Description")

try:

    description = df.describe(
        include="all"
    ).transpose()

    st.dataframe(
        description,
        use_container_width=True,
    )

except Exception as e:

    st.warning(
        f"Could not generate description: {e}"
    )

# DATA TYPES

st.subheader("🔹 Data Information")

info_df = pd.DataFrame(
    {
        "Column": df.columns,
        "Data Type": df.dtypes.astype(str).values,
        "Non-Null Count": df.notnull().sum().values,
        "Null Count": df.isnull().sum().values,
        "Unique Values": [
            df[column].nunique(dropna=True)
            for column in df.columns
        ],
    }
)

st.dataframe(
    info_df,
    use_container_width=True,
)

# FEATURE AND TARGET SELECTION

st.header("🎯 Select Features and Target")

st.info(
    """
    Select your feature columns and target column.

    The application will NOT train any model until you press
    **Run Analysis & Train Models**.
    """
)

available_columns = list(df.columns)


feature_columns = st.multiselect(
    "Select Feature Columns (X)",
    options=available_columns,
)


target_column = st.selectbox(
    "Select Target Column (y)",
    options=[
        "-- Select Target --"
    ] + available_columns,
)

# VALIDATE SELECTION

if len(feature_columns) == 0:

    st.warning(
        "Please select at least one feature column."
    )

    st.stop()


if target_column == "-- Select Target --":

    st.warning(
        "Please select a target column."
    )

    st.stop()


if target_column in feature_columns:

    st.error(
        "The target column cannot also be a feature column."
    )

    st.stop()

# TARGET INFORMATION

target_series = df[target_column]

target_without_missing = target_series.dropna()

unique_values = target_without_missing.nunique()

is_numeric_target = pd.api.types.is_numeric_dtype(
    target_series
)

# DETECT PROBLEM TYPE

if is_numeric_target and unique_values > 10:

    problem_type = "Regression"

else:

    problem_type = "Classification"


st.subheader("🧠 Problem Type")

if problem_type == "Regression":

    st.success(
        "✅ Regression Problem"
    )

    st.write(
        f"Target: **{target_column}**"
    )

    st.write(
        f"Target type: **{target_series.dtype}**"
    )

    st.write(
        f"Unique target values: **{unique_values}**"
    )

    st.info(
        "The target contains continuous numerical values."
    )

else:

    st.success(
        "✅ Classification Problem"
    )

    st.write(
        f"Target: **{target_column}**"
    )

    st.write(
        f"Target type: **{target_series.dtype}**"
    )

    st.write(
        f"Number of classes: **{unique_values}**"
    )

    st.write(
        "**Classes:**"
    )

    st.write(
        list(target_without_missing.unique())
    )

# TRAIN / TEST SPLIT

st.header("✂️ Train/Test Split")

test_size_percent = st.sidebar.slider(
    "Test Size (%)",
    min_value=10,
    max_value=50,
    value=20,
    step=5,
)

test_size = test_size_percent / 100

st.write(
    f"Training data: **{100 - test_size_percent}%**"
)

st.write(
    f"Testing data: **{test_size_percent}%**"
)

# MODEL SELECTION

st.sidebar.header("🤖 Model Selection")

if problem_type == "Regression":

    model_options = [
        "Linear Regression",
        "Decision Tree Regressor",
        "Random Forest Regressor",
        "Support Vector Regressor",
    ]

else:

    model_options = [
        "Logistic Regression",
        "Decision Tree Classifier",
        "Random Forest Classifier",
        "Support Vector Classifier",
    ]


selected_models = st.sidebar.multiselect(
    "Select Models",
    options=model_options,
    default=model_options,
)

# MODEL CREATION

def create_regression_model(model_name):

    if model_name == "Linear Regression":
        return LinearRegression()

    if model_name == "Decision Tree Regressor":
        return DecisionTreeRegressor(
            random_state=42
        )

    if model_name == "Random Forest Regressor":
        return RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            n_jobs=-1,
        )

    if model_name == "Support Vector Regressor":
        return SVR()

    return None


def create_classification_model(model_name):

    if model_name == "Logistic Regression":
        return LogisticRegression(
            max_iter=2000
        )

    if model_name == "Decision Tree Classifier":
        return DecisionTreeClassifier(
            random_state=42
        )

    if model_name == "Random Forest Classifier":
        return RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            n_jobs=-1,
        )

    if model_name == "Support Vector Classifier":
        return SVC(
            probability=True,
            random_state=42,
        )

    return None

# PREPROCESSOR

def create_preprocessor(X):

    numerical_columns = (
        X.select_dtypes(
            include=np.number
        )
        .columns
        .tolist()
    )

    categorical_columns = (
        X.select_dtypes(
            exclude=np.number
        )
        .columns
        .tolist()
    )

    transformers = []

    # Numerical
    if numerical_columns:

        numerical_pipeline = Pipeline(
            steps=[
                (
                    "imputer",
                    IterativeImputer(
                        random_state=42
                    ),
                ),
                (
                    "scaler",
                    StandardScaler(),
                ),
            ]
        )

        transformers.append(
            (
                "numerical",
                numerical_pipeline,
                numerical_columns,
            )
        )

    # Categorical
    if categorical_columns:

        categorical_pipeline = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(
                        strategy="most_frequent"
                    ),
                ),
                (
                    "encoder",
                    OrdinalEncoder(
                        handle_unknown="use_encoded_value",
                        unknown_value=-1,
                    ),
                ),
            ]
        )

        transformers.append(
            (
                "categorical",
                categorical_pipeline,
                categorical_columns,
            )
        )

    if not transformers:

        raise ValueError(
            "No valid feature columns were found."
        )

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop",
    )

# TRAIN MODELS

def train_models(
    X,
    y,
    test_size,
    problem_type,
    selected_models,
):

    # TRAIN / TEST SPLIT

    if problem_type == "Classification":

        class_counts = y.value_counts()

        n_classes = len(class_counts)

        if n_classes < 2:

            raise ValueError(
                "Classification requires at least two classes."
            )

        if class_counts.min() < 2:

            raise ValueError(
                "Every class must have at least 2 samples."
            )

        requested_test_count = int(
            np.ceil(
                len(y) * test_size
            )
        )

        test_count = max(
            requested_test_count,
            n_classes,
        )

        test_count = min(
            test_count,
            len(y) - n_classes,
        )

        if test_count < n_classes:

            raise ValueError(
                "Not enough data for a stratified train/test split."
            )

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_count,
            random_state=42,
            stratify=y,
        )

    else:

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=42,
        )

    trained_models = {}

    results = {}

    # TRAIN EACH MODEL

    for model_name in selected_models:

        try:

            if problem_type == "Regression":

                model = create_regression_model(
                    model_name
                )

            else:

                model = create_classification_model(
                    model_name
                )

            if model is None:
                continue

            preprocessor = create_preprocessor(
                X_train
            )

            pipeline = Pipeline(
                steps=[
                    (
                        "preprocessor",
                        preprocessor,
                    ),
                    (
                        "model",
                        model,
                    ),
                ]
            )

            pipeline.fit(
                X_train,
                y_train,
            )

            y_pred = pipeline.predict(
                X_test
            )

            trained_models[model_name] = pipeline

            # REGRESSION

            if problem_type == "Regression":

                mse = mean_squared_error(
                    y_test,
                    y_pred,
                )

                rmse = np.sqrt(mse)

                mae = mean_absolute_error(
                    y_test,
                    y_pred,
                )

                r2 = r2_score(
                    y_test,
                    y_pred,
                )

                results[model_name] = {
                    "MSE": mse,
                    "RMSE": rmse,
                    "MAE": mae,
                    "R2 Score": r2,
                }

            # CLASSIFICATION

            else:

                accuracy = accuracy_score(
                    y_test,
                    y_pred,
                )

                precision = precision_score(
                    y_test,
                    y_pred,
                    average="weighted",
                    zero_division=0,
                )

                recall = recall_score(
                    y_test,
                    y_pred,
                    average="weighted",
                    zero_division=0,
                )

                f1 = f1_score(
                    y_test,
                    y_pred,
                    average="weighted",
                    zero_division=0,
                )

                roc_auc = np.nan

                try:

                    probabilities = (
                        pipeline.predict_proba(
                            X_test
                        )
                    )

                    if len(
                        pipeline.classes_
                    ) == 2:

                        positive_class = (
                            pipeline.classes_[1]
                        )

                        positive_index = list(
                            pipeline.classes_
                        ).index(
                            positive_class
                        )

                        y_binary = (
                            y_test == positive_class
                        ).astype(int)

                        roc_auc = roc_auc_score(
                            y_binary,
                            probabilities[
                                :,
                                positive_index
                            ],
                        )

                    elif len(
                        pipeline.classes_
                    ) > 2:

                        roc_auc = roc_auc_score(
                            y_test,
                            probabilities,
                            multi_class="ovr",
                            average="weighted",
                        )

                except Exception:

                    roc_auc = np.nan

                results[model_name] = {
                    "Accuracy": accuracy,
                    "Precision": precision,
                    "Recall": recall,
                    "F1 Score": f1,
                    "ROC-AUC": roc_auc,
                }

        except Exception as model_error:

            results[model_name] = {
                "Error": str(model_error)
            }

    return (
        trained_models,
        results,
        X_train,
        X_test,
        y_train,
        y_test,
    )

# TRAINING BUTTON

st.header("🚀 Model Training")

if len(selected_models) == 0:

    st.warning(
        "Please select at least one model from the sidebar."
    )

else:

    run_training = st.button(
        "🚀 Run Analysis & Train Models",
        type="primary",
        use_container_width=True,
    )

    if run_training:

        # X AND Y

        X = df[
            feature_columns
        ].copy()

        y = df[
            target_column
        ].copy()

        # REMOVE MISSING TARGETS

        valid_target = y.notna()

        X = X.loc[
            valid_target
        ].reset_index(drop=True)

        y = y.loc[
            valid_target
        ].reset_index(drop=True)

        # BASIC VALIDATION

        if len(X) < 10:

            st.error(
                "The dataset must contain at least 10 valid rows."
            )

            st.stop()

        if X.shape[1] == 0:

            st.error(
                "Please select at least one feature."
            )

            st.stop()

        if problem_type == "Classification":

            class_counts = y.value_counts()

            if y.nunique() < 2:

                st.error(
                    "Classification requires at least two classes."
                )

                st.stop()

            if class_counts.min() < 2:

                st.error(
                    "Every class must contain at least 2 samples."
                )

                st.stop()

        # TRAIN

        with st.spinner(
            "Training Machine Learning models..."
        ):

            try:

                (
                    trained_models,
                    results,
                    X_train,
                    X_test,
                    y_train,
                    y_test,
                ) = train_models(
                    X,
                    y,
                    test_size,
                    problem_type,
                    tuple(selected_models),
                )

            except Exception as e:

                st.error(
                    f"Training failed: {e}"
                )

                st.stop()

        # REMOVE MODELS THAT FAILED

        successful_results = {
            name: values
            for name, values in results.items()
            if "Error" not in values
        }

        if not successful_results:

            st.error(
                "None of the selected models could be trained."
            )

            for name, values in results.items():

                if "Error" in values:

                    st.error(
                        f"{name}: {values['Error']}"
                    )

            st.stop()

        trained_models = {
            name: model
            for name, model in trained_models.items()
            if name in successful_results
        }

        results = successful_results

        # SAVE SESSION STATE

        st.session_state["feature_columns"] = (
            feature_columns
        )

        st.session_state["target_column"] = (
            target_column
        )

        st.session_state["problem_type"] = (
            problem_type
        )

        st.session_state["test_size"] = (
            test_size
        )

        st.session_state["trained_models"] = (
            trained_models
        )

        st.session_state["results"] = (
            results
        )

        st.session_state["X_test"] = (
            X_test
        )

        st.session_state["y_test"] = (
            y_test
        )

        # BEST MODEL

        if problem_type == "Regression":

            best_model_name = max(
                results,
                key=lambda name:
                results[name]["R2 Score"],
            )

        else:

            best_model_name = max(
                results,
                key=lambda name:
                results[name]["F1 Score"],
            )

        st.session_state["best_model_name"] = (
            best_model_name
        )

        st.success(
            "🎉 Models trained successfully!"
        )

        st.rerun()

# DISPLAY RESULTS

if "results" in st.session_state:

    results = st.session_state["results"]

    problem_type_saved = (
        st.session_state["problem_type"]
    )

    st.header("📊 Model Evaluation")

    results_df = pd.DataFrame(
        results
    ).T

    st.dataframe(
        results_df,
        use_container_width=True,
    )

    # BEST MODEL

    best_model_name = (
        st.session_state["best_model_name"]
    )

    st.subheader("🏆 Best Model")

    st.success(
        f"Best Model: **{best_model_name}**"
    )

    # CLASSIFICATION VISUALIZATIONS

    if problem_type_saved == "Classification":

        trained_models = (
            st.session_state["trained_models"]
        )

        X_test = (
            st.session_state["X_test"]
        )

        y_test = (
            st.session_state["y_test"]
        )

        best_model = trained_models[
            best_model_name
        ]

        y_pred = best_model.predict(
            X_test
        )

        # CONFUSION MATRIX

        st.header("🔲 Confusion Matrix")

        cm = confusion_matrix(
            y_test,
            y_pred,
        )

        fig, ax = plt.subplots(
            figsize=(7, 5)
        )

        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            ax=ax,
        )

        ax.set_xlabel(
            "Predicted"
        )

        ax.set_ylabel(
            "Actual"
        )

        ax.set_title(
            f"Confusion Matrix - {best_model_name}"
        )

        st.pyplot(fig)

        plt.close(fig)

        # ROC CURVE

        st.header("📈 ROC Curve")

        try:

            probabilities = (
                best_model.predict_proba(
                    X_test
                )
            )

            classes = best_model.classes_

            if len(classes) == 2:

                positive_class = classes[1]

                positive_index = list(
                    classes
                ).index(
                    positive_class
                )

                y_test_binary = (
                    y_test == positive_class
                ).astype(int)

                positive_probabilities = (
                    probabilities[
                        :,
                        positive_index
                    ]
                )

                fpr, tpr, _ = roc_curve(
                    y_test_binary,
                    positive_probabilities,
                )

                auc_value = roc_auc_score(
                    y_test_binary,
                    positive_probabilities,
                )

                fig, ax = plt.subplots(
                    figsize=(7, 5)
                )

                ax.plot(
                    fpr,
                    tpr,
                    label=f"AUC = {auc_value:.4f}",
                )

                ax.plot(
                    [0, 1],
                    [0, 1],
                    linestyle="--",
                )

                ax.set_xlabel(
                    "False Positive Rate"
                )

                ax.set_ylabel(
                    "True Positive Rate"
                )

                ax.set_title(
                    f"ROC Curve - {best_model_name}"
                )

                ax.legend()

                st.pyplot(fig)

                plt.close(fig)

            else:

                st.info(
                    "ROC curve visualization is displayed "
                    "for binary classification."
                )

        except Exception as e:

            st.info(
                f"ROC curve could not be generated: {e}"
            )

# DOWNLOAD MODEL

if "trained_models" in st.session_state:

    st.header("💾 Download Best Model")

    trained_models = (
        st.session_state["trained_models"]
    )

    best_model_name = (
        st.session_state["best_model_name"]
    )

    best_model = trained_models[
        best_model_name
    ]

    st.write(
        f"Selected model: **{best_model_name}**"
    )

    model_bytes = pickle.dumps(
        best_model
    )

    st.download_button(
        label="⬇️ Download Model (.pkl)",
        data=model_bytes,
        file_name="best_ml_model.pkl",
        mime="application/octet-stream",
        use_container_width=True,
    )

# PREDICTION

if "trained_models" in st.session_state:

    st.header("🔮 Make Prediction")

    make_prediction = st.checkbox(
        "I want to make a prediction"
    )

    if make_prediction:

        trained_models = (
            st.session_state["trained_models"]
        )

        best_model_name = (
            st.session_state["best_model_name"]
        )

        best_model = trained_models[
            best_model_name
        ]

        selected_features = (
            st.session_state["feature_columns"]
        )

        prediction_method = st.radio(
            "Choose prediction input method:",
            [
                "Enter values manually",
                "Upload prediction file",
            ],
        )
        # MANUAL INPUT

        if prediction_method == "Enter values manually":

            input_data = {}

            st.write(
                "Enter values for the selected features:"
            )

            for column in selected_features:

                column_data = df[column]

                # NUMERIC

                if pd.api.types.is_numeric_dtype(
                    column_data
                ):

                    clean_values = pd.to_numeric(
                        column_data,
                        errors="coerce",
                    ).dropna()

                    if len(clean_values) > 0:

                        min_value = float(
                            clean_values.min()
                        )

                        max_value = float(
                            clean_values.max()
                        )

                        mean_value = float(
                            clean_values.mean()
                        )

                    else:

                        min_value = 0.0
                        max_value = 100.0
                        mean_value = 0.0

                    if min_value == max_value:

                        input_data[column] = (
                            st.number_input(
                                column,
                                value=mean_value,
                            )
                        )

                    else:

                        input_data[column] = (
                            st.number_input(
                                column,
                                min_value=min_value,
                                max_value=max_value,
                                value=mean_value,
                            )
                        )
                # CATEGORICAL
                else:

                    categories = (
                        column_data
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    )

                    if categories:

                        input_data[column] = (
                            st.selectbox(
                                column,
                                categories,
                            )
                        )

                    else:

                        input_data[column] = (
                            st.text_input(
                                column
                            )
                        )

            # PREDICT
            if st.button(
                "🔮 Predict",
                type="primary",
            ):

                try:

                    prediction_df = pd.DataFrame(
                        [input_data],
                        columns=selected_features,
                    )

                    prediction = (
                        best_model.predict(
                            prediction_df
                        )
                    )

                    st.subheader(
                        "🎯 Prediction Result"
                    )

                    st.success(
                        f"Prediction: **{prediction[0]}**"
                    )

                except Exception as e:

                    st.error(
                        f"Prediction failed: {e}"
                    )

        # UPLOAD PREDICTION FILE

        else:

            prediction_file = st.file_uploader(
                "Upload prediction data",
                type=[
                    "csv",
                    "xlsx",
                    "xls",
                    "tsv",
                    "json",
                ],
                key="prediction_file",
            )

            if prediction_file is not None:

                try:

                    prediction_df = load_uploaded_file(
                        prediction_file.getvalue(),
                        prediction_file.name,
                    )

                    st.subheader(
                        "Prediction Data"
                    )

                    st.dataframe(
                        prediction_df.head(),
                        use_container_width=True,
                    )

                    missing_features = [
                        column
                        for column in selected_features
                        if column not in prediction_df.columns
                    ]

                    if missing_features:

                        st.error(
                            "Missing feature columns: "
                            f"{missing_features}"
                        )

                    else:

                        prediction_input = (
                            prediction_df[
                                selected_features
                            ].copy()
                        )

                        if st.button(
                            "🔮 Predict Uploaded Data",
                            type="primary",
                        ):

                            try:

                                predictions = (
                                    best_model.predict(
                                        prediction_input
                                    )
                                )

                                result_df = (
                                    prediction_df.copy()
                                )

                                result_df[
                                    "Prediction"
                                ] = predictions

                                st.subheader(
                                    "🎯 Prediction Results"
                                )

                                st.dataframe(
                                    result_df,
                                    use_container_width=True,
                                )

                                csv_data = (
                                    result_df.to_csv(
                                        index=False
                                    )
                                )

                                st.download_button(
                                    "⬇️ Download Predictions",
                                    data=csv_data,
                                    file_name="predictions.csv",
                                    mime="text/csv",
                                )

                            except Exception as e:

                                st.error(
                                    f"Prediction failed: {e}"
                                )

                except Exception as e:

                    st.error(
                        f"Could not read prediction file: {e}"
                    )

# FOOTER

st.markdown("---")

st.caption(
    "🤖 Machine Learning Application | "
    "Built with Streamlit + Scikit-Learn"
)
