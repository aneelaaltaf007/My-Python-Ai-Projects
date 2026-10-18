# Promopt

Hey Chat GPT, act as an application developer expert, in python using streamlit, and bulid a machine learning application using scikit learn with the following the workflow:

1. Greet the user with a welcome message and a belief description of the application.
2. Ask the user if he wants the data or use the example data.
3. if  the user select to upload the data, show the uploader section on the sidebar,upload the dataset in csv,xlsx,tsv or any possible data format.
4. if the user do not want to upload the data then provide a default dataset selection box on the sidebar.this selection box should download the data from sns.load_dataset() function.The datasets should include titanic, tips ,or iris.
5. print the basic data information such as data head, data shape, data description , and data info, and columns names.
6. Ask from the user to select the columns as features and also the columns as target.
7. Identify the problem if the target column is a continous numeric column the print the message that this is a regression problem, otherwise print the message  this is a classification problem.
8. pre-process the data , if the data contains any missing values the fill the missing values with the iteratuva imputer function of scikit-learn, if the features using the standard scaler function of the scikit-learn. if the features are categorical variables the encode the categorical variables using the label encoder function of scikit-learn. please keep in mind to keep the encoder separate for each column as we need to inverse transform the
data at the end.
9. Ask the user to provie the train test split size via slider ,or user input function.
10. Ask the user to select the model from the sidebar, the model should include linear regression, decision tree, random forest and support vector machine and same classes of models for the classification problem.
11. Train the models on the training data and evaluate on the test data.
12. if the problem is a regression problem,use the mean squared error, RMSE,MAE,AUROC curve and r2 score for evaluation, if the problem is a classification problem, use the accuracy score, Precision, recall, f1 score and draw confusion matrix for evaluation.
13. print the evaluation matrix for each model.
14. Highlight the best model based on the evaluation matrix.
15. Ask the user if he wants to download the model , if yes then download the model in the pickle format.
16. Ask the user if he wants to make prediction, if yes then ask the user to provide the input data using slider or uploaded file and make the prediction using the best model.
17. show the prediction to the user.

## Modification/fine tuning of the model
1.Please modify and ask the user to provide the information if the problem is regression and classification, and also do not run anything  until we select the columns and tell the app to run analysis.  please add one button which starts training the ml models. 
2.Please also use cache for data and models to speedup the procedure.