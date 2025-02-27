import os
import re
import nltk
import string
import sparknlp
import numpy as np
import pandas as pd
import transformers
import seaborn as sns
import tensorflow as tf
from sparknlp.base import *
import plotly.express as px
from tqdm.notebook import tqdm
from pyspark.ml import Pipeline
import matplotlib.pyplot as plt
from sparknlp.annotator import *
from nltk.corpus import stopwords
import pyspark.sql.functions as F
from keras.models import Sequential
from sklearn.metrics import f1_score
from geopy.geocoders import Nominatim
from pyspark.sql.functions import col
from transformers import BertTokenizer
from nltk.tokenize import word_tokenize
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tokenizers import BertWordPieceTokenizer
from keras.preprocessing.text import Tokenizer
from tensorflow.keras.layers import Dense, Input
from geopy.extra.rate_limiter import RateLimiter
from sparknlp.pretrained import PretrainedPipeline
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from tensorflow.keras.callbacks import ModelCheckpoint
from keras.preprocessing.sequence import pad_sequences
from keras.callbacks import ModelCheckpoint, ReduceLROnPlateau
from sklearn.metrics import classification_report, accuracy_score
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics import (precision_score, recall_score, f1_score, classification_report, accuracy_score)
from keras.layers import (LSTM, Embedding, BatchNormalization, Dense, TimeDistributed, Dropout, Bidirectional, Flatten, GlobalMaxPool1D)

import dash
from dash import html
from dash import dcc
from dash import callback_context
from dash.dependencies import Input, Output
from plotly.tools import mpl_to_plotly


app = dash.Dash(__name__)
server = app.server

data = pd.read_csv('train.csv')

duplicated_data = data['text'].duplicated().sum()

data = data.drop_duplicates(subset=['text'], keep='first')

data['location'].replace('', np.nan, inplace=True)
data = data.dropna(subset=['location'])

def clean_data(text):
    text = text.lower()
    text = re.sub(r'http[s]?:\/\/.*[\r\n]*', '', text)
    text = re.sub(r'[^A-Za-z0-9 ]+', '', text)
    text = ' '.join(text.split())
    return text

def clean_data_locations(text):
    text = str(text)
    text = re.sub(r'http[s]?:\/\/.*[\r\n]*', '', text)
    text = re.sub(r'[^A-Za-z0-9 ]+', '', text)
    text = " ".join(text.split())
    return text

def remove_emojis(text):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE
    )

    return emoji_pattern.sub(r'', text)

data['text'] = data['text'].apply(clean_data)

data['text'] = data['text'].apply(remove_emojis)

data['location'] = data['location'].apply(clean_data_locations)

data['location'] = data['location'].apply(remove_emojis)

data['location'].replace('', np.nan, inplace=True)
data = data.dropna(subset=['location'])

data['location'] = data['location'].replace({
    "uk": "UK",
    "US": "USA",
    "England": "UK",
    "london": "London",
    "London.": "London",
    "London UK": "London",
    "United Kingdom": "UK",
    "United States": "USA",
    "London, UK": "London",
    "London England": "London",
    "London, England": "London",
    "City of London London": "London",
    "Manchester England": "Manchester",
    "Manchester UK": "Manchester",
    "Atlanta, GA": "Atlanta",
    "NEW YORK": "New York",
    "New York City": "New York",
    "New York USA": "New York",
    "NYC": "New York",
    "NY": "New York",
    "New Your": "New York",
    "new york ny": "New York",
    "New York NY": "New York",
    "New York ATL": "New York",
    "New York, NY": "New York",
    "New York NYC": "New York",
    "New York 2099": "New York",
    "New York New York": "New York",
    "New York Worldwide": "New York",
    "New York United States": "New York",
    "nyc": "New York",
    "new york": "New York",
    "NYC New York": "New York",
    "New Jersey DR": "New Jersey",
    "New Jersey USA": "New Jersey",
    "New York City NY": "New York",
    "New JerseyNew York": "New York",
    "New Jersey usually": "New Jersey",
    "New York / Worldwide": "New York",
    "San Francisco, CA": "San Francisco",
    "San Francisco CA": "San Francisco",
    "California, USA": "California",
    "California USA": "California",
    "California, United States": "California",
    "California United States": "California",
    "CA": "California",
    "Chicago, IL": "Chicago",
    "Chicago IL": "Chicago",
    "Chicago Illinois": "Chicago",
    "Los Angeles, CA": "Los Angeles",
    "Los Angeles CA": "Los Angeles",
    "L.A.": "Los Angeles",
    "Los Angeles New York": "Los Angeles",
    "Everywhere": "Worldwide",
    "Earth": "Worldwide",
    "Washington, DC": "Washington",
    "Washington DC": "Washington",
    "Washington DC NATIVE": "Washington",
    "Washington state": "Washington",
    "Washington State": "Washington",
    "Washington USA": "Washington",
    "WASHINGTONDC": "Washington",
    "WashingtonState Seattle": "Washington",
    "Western Washington": "Washington",
    "Washington DC area": "Washington",
    "Washington DC 20009": "Washington",
    "washington dc": "Washington",
    "Washington, D.C.": "Washington",
    "Florida, USA": "Florida",
    "Florida USA": "Florida",
    "Miami, FL": "Miami",
    "Miami Florida": "Miami",
    "Dallas, TX": "Dallas",
    "Dallas TX": "Dallas",
    "Austin, Texas": "Austin",
    "Austin Texas": "Austin",
    "Austin TX": "Austin",
    "Houston TX": "Houston",
    "Arlington TX": "Arlington",
    "Atlanta GA": "Atlanta",
    "Atlanta Georgia": "Atlanta",
    "San Diego CA": "San Diego",
    "Seattle WA": "Seattle",
    "Seattle Washington": "Seattle",
    "SEATTLE WA USA": "Seattle",
    "WashingtonState Seattle": "Seattle",
    "seattle wa": "Seattle",
    "Boston MA": "Boston",
    "Denver CO": "Denver",
    "Pennsylvania USA": "Pennsylvania",
    "Brooklyn NY": "Brooklyn",
    "Brooklyn New York": "Brooklyn",
    "New York Brooklyn": "Brooklyn",
    "New York Connecticut": "Connecticut",
    "Portland OR": "Portland",
    "Portland Oregon": "Portland",
    "Orlando FL": "Orlando",
    "Tampa FL": "Tampa",
    "Texas USA": "Texas",
    "indiana": "Indiana",
    "Indiana USA": "Indiana",
    "Indianapolis IN": "Indiana",
    "canada": "Canada",
    "Berlin Germany": "Berlin",
    "Las Vegas Nevada": "Las Vegas",
    "Massachusetts USA": "Massachusetts",
    "Georgia USA": "Georgia",
    "ARGENTINA": "Argentina",
    "china": "China",
    "india": "India",
    "INDIA": "India",
    "Bangalore INDIA": "Bangalore",
    "Bangalore India": "Bangalore",
    "Bangalore City India": "Bangalore",
    "italy": "Italy",
    "anzioitaly": "Italy",
    "ITALY": "Italy",
    "Rome Italy": "Rome",
    "CasertaRoma Italy": "Caserta",
    "Manhattan NY": "Manhattan",
    "Mumbai India": "Mumbai",
    "Mumbai india": "Mumbai",
    "Stockholm Sweden": "Stockholm",
    "Virginia USA": "Virginia",
    "Auckland New Zealand": "Auckland",
    "Buenos Aires Argentina": "Buenos Aires",
    "Lagos Nigeria": "Lagos",
    "nigeria": "Nigeria",
    "NIGERIA": "Nigeria",
    "Nigeria Global": "Nigeria",
    "Nigeria WORLDWIDE": "Nigeria",
    "Charlotte NC": "Charlotte",
    "Charlotte County Florida": "Charlotte",
    "Nashville TN": "Nashville",
    "Sacramento CA": "Sacramento",
    "Melbourne Australia": "Melbourne",
    "Memphis TN": "Memphis",
    "Calgary Alberta": "Calgary",
    "Calgary AB Canada": "Calgary",
    "Calgary Alberta Canada": "Calgary",
    "Calgary Canada": "Calgary",
    "CalgaryAB Canada": "Calgary",
    "caNADA": "Canada",
    "Canada BC": "Canada",
    "Canada Eh": "Canada",
    "Toronto Canada": "Toronto",
    "Toronto ON Canada": "Toronto",
    "TorontoCitizen of Canada US": "Toronto",
    "Vancouver BC Canda": "Vancouver",
    "Vancouver Canada": "Vancouver",
    "Victoria BC Canada": "Victoria",
    "Victoria Canada": "Victoria",
    "Oklahoma City OK": "Oklahoma",
    "Ontario Canada": "Ontario",
    "Newcastle": "Newcastle Upon Tyne",
    "Newcastle England": "Newcastle Upon Tyne",
    "Newcastle OK": "Newcastle Upon Tyne",
    "Newcastle upon Tyne": "Newcastle Upon Tyne",
    "Newcastle Upon Tyne England": "Newcastle Upon Tyne",
    "NewcastleuponTyne UK": "Newcastle Upon Tyne",
    "The Netherlands": "Netherlands",
    "New Delhi Delhi": "New Delhi",
    "New Delhi India": "New Delhi",
    "New DelhiIndia": "New Delhi",
    "Adelaide Australia": "Adelaide",
    "Adelaide South Australia": "Adelaide",
    "Brisbane Australia": "Brisbane",
    "brisbane australia": "Brisbane",
    "Gold Coast Australia": "Gold Coast",
    "Gold Coast Qld Australia": "Gold Coast",
    "Sydney Australia": "Sydney",
    "sydney australia": "Sydney",
})


keywords = data['keyword'].value_counts().nlargest()
fig = px.bar(data, x=keywords.tolist(), y=keywords.index)

# LSTM MODEL

test_df = pd.read_csv("test.csv")

stop_words = stopwords.words('english')
more_stopwords = ['u', 'im', 'c']
stop_words = stop_words + more_stopwords

stemmer = nltk.SnowballStemmer("english")

def preprocess_data(text):
    text = clean_text(text)
    text = ' '.join(stemmer.stem(word) for word in text.split(' ') if word not in stop_words)

    return text

def clean_text(text):
    '''Make text lowercase, remove text in square brackets,remove links,remove punctuation
    and remove words containing numbers.'''
    text = str(text).lower()
    text = re.sub('\[.*?\]', '', text)
    text = re.sub('https?://\S+|www\.\S+', '', text)
    text = re.sub('<.*?>+', '', text)
    text = re.sub('[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub('\n', '', text)
    text = re.sub('\w*\d\w*', '', text)
    return text


test_df['text'] = test_df['text'].apply(preprocess_data)

train_tweets = data['text'].values
test_tweets = test_df['text'].values
train_target = data['target'].values


word_tokenizer = Tokenizer()
word_tokenizer.fit_on_texts(train_tweets)

vocab_length = len(word_tokenizer.word_index) + 1


def show_metrics(pred_tag, y_test):
    print("F1-score: ", f1_score(pred_tag, y_test))
    print("Precision: ", precision_score(pred_tag, y_test))
    print("Recall: ", recall_score(pred_tag, y_test))
    print("Acuracy: ", accuracy_score(pred_tag, y_test))
    print("-"*50)
    print(classification_report(pred_tag, y_test))

def embed(corpus):
    return word_tokenizer.texts_to_sequences(corpus)

longest_train = max(train_tweets, key=lambda sentence: len(word_tokenize(sentence)))
length_long_sentence = len(word_tokenize(longest_train))

train_padded_sentences = pad_sequences(
    embed(train_tweets),
    length_long_sentence,
    padding='post'
)

test_padded_sentences = pad_sequences(
    embed(test_tweets),
    length_long_sentence,
    padding='post'
)

embeddings_dictionary = dict()
embedding_dim = 100
file_name = 'glove.6B.100d.txt'

with open(file_name) as fp:
    for line in fp.readlines():
        records = line.split()
        word = records[0]
        vector_dimensions = np.asarray(records[1:], dtype='float32')
        embeddings_dictionary [word] = vector_dimensions


embedding_matrix = np.zeros((vocab_length, embedding_dim))

for word, index in word_tokenizer.word_index.items():
    embedding_vector = embeddings_dictionary.get(word)
    if embedding_vector is not None:
        embedding_matrix[index] = embedding_vector

X_train, X_test, y_train, y_test = train_test_split(
    train_padded_sentences,
    train_target,
    test_size=0.25
)

def glove_lstm():
    model = Sequential()

    model.add(Embedding(
        input_dim=embedding_matrix.shape[0],
        output_dim=embedding_matrix.shape[1],
        weights = [embedding_matrix],
        input_length=length_long_sentence
    ))

    model.add(Bidirectional(LSTM(
        length_long_sentence,
        return_sequences = True,
        recurrent_dropout=0.2
    )))

    model.add(GlobalMaxPool1D())
    model.add(BatchNormalization())
    model.add(Dropout(0.5))
    model.add(Dense(length_long_sentence, activation = "relu"))
    model.add(Dropout(0.5))
    model.add(Dense(length_long_sentence, activation = "relu"))
    model.add(Dropout(0.5))
    model.add(Dense(1, activation = 'sigmoid'))
    model.compile(optimizer='rmsprop', loss='binary_crossentropy', metrics=['accuracy'])

    return model

model = glove_lstm()
model.summary()

model = glove_lstm()

checkpoint = ModelCheckpoint(
    'model.h5',
    monitor = 'val_loss',
    verbose = 1,
    save_best_only = True
)
reduce_lr = ReduceLROnPlateau(
    monitor = 'val_loss',
    factor = 0.2,
    verbose = 1,
    patience = 5,
    min_lr = 0.001
)
history = model.fit(
    X_train,
    y_train,
    epochs = 7,
    batch_size = 32,
    validation_data = (X_test, y_test),
    verbose = 1,
    callbacks = [reduce_lr, checkpoint]
)

preds_lstm = (model.predict(X_test) > 0.5).astype("int32")

# show_metrics(preds, y_test)

f1_lstm_  = f1_score(preds_lstm, y_test)
f1_lstm = f"{f1_lstm_ * 100:.2f}%"
precision_lstm_ = precision_score(preds_lstm, y_test)
precision_lstm = f"{precision_lstm_ * 100:.2f}%"
recall_lstm_ = recall_score(preds_lstm, y_test)
recall_lstm = f"{recall_lstm_ * 100:.2f}%"
accuracy_lstm_ = accuracy_score(preds_lstm, y_test)
accuracy_lstm = f"{accuracy_lstm_ * 100:.2f}%"







# SPARK NLP MODEL
spark = sparknlp.start()

df_train = spark.read.option("header", True).csv("clean_data.csv")

df_train = df_train.na.drop(how="any")
df_train.groupby("target").count().orderBy(col("count"))

document = DocumentAssembler().setInputCol("text").setOutputCol("document")

use = UniversalSentenceEncoder.pretrained().setInputCols(["document"]).setOutputCol("sentence_embeddings")

classsifierdl = ClassifierDLApproach().setInputCols(["sentence_embeddings"]).setOutputCol("class").setLabelColumn("target").setMaxEpochs(10).setEnableOutputLogs(True).setLr(0.004)

nlpPipeline = Pipeline(
    stages = [
        document,
        use,
        classsifierdl
    ]
)

(train_set, test_set) = df_train.randomSplit([0.8, 0.2], seed=100)

use_model = nlpPipeline.fit(train_set)

prediction = use_model.transform(train_set)

df = use_model.transform(train_set).select("target", "document", "class.result").toPandas()
df["result"] = df["result"].apply(lambda x: x[0])
ty = classification_report(df["target"], df["result"])

accuracy_snlp_ = accuracy_score(df["target"], df["result"])
accuracy_snlp = f"{accuracy_snlp_ * 100:.2f}%"

f1_snlp_ = ty[148:152]
f1_snlp = f"{float(f1_snlp_) * 100:.2f}%"

recall_snlp_ = ty[138:142]
recall_snlp = f"{float(recall_snlp_) * 100:.2f}%"

precision_snlp_ = ty[128:132]
precision_snlp = f"{float(precision_snlp_) * 100:.2f}%"










# Logistic Regression MODEL
vectorizer = CountVectorizer(analyzer='word', binary=True, stop_words='english')
vectorizer.fit(data['text'])

x = vectorizer.transform(data['text']).todense()
y = data['target'].values


X_train, X_test, y_train, y_test_lr = train_test_split(x, y, test_size=0.2, random_state=2021)

modelLR = LogisticRegression(C=1.0, random_state=111)
modelLR.fit(X_train, y_train)

y_pred_lr = modelLR.predict(X_test)

# f1score = f1_score(y_test, y_pred_lr)
# print(f"Model Score: {f1score * 100:.2f} %")

f1_lr_  = f1_score(y_pred_lr, y_test_lr)
f1_lr = f"{f1_lr_ * 100:.2f}%"
precision_lr_ = precision_score(y_pred_lr, y_test_lr)
precision_lr = f"{precision_lr_ * 100:.2f}%"
recall_lr_ = recall_score(y_pred_lr, y_test_lr)
recall_lr = f"{recall_lr_ * 100:.2f}%"
accuracy_lr_ = accuracy_score(y_pred_lr, y_test_lr)
accuracy_lr = f"{accuracy_lr_ * 100:.2f}%"





def plot_learning_curves(history, arr):
    fig= plt.figure()
    fig, ax = plt.subplots(1, 2, figsize=(15, 3))
    for idx in range(2):
        ax[idx].plot(history.history[arr[idx][0]])
        ax[idx].plot(history.history[arr[idx][1]])
        # ax[idx].legend([arr[idx][0], arr[idx][1]])
        ax[idx].set_xlabel('A ')
        ax[idx].set_ylabel('B')
        ax[idx].set_title(arr[idx][0] + '(blue)' + ' vs ' + arr[idx][1] + '(orange)')
        ax[idx].legend()
    return fig

lstm_fig_ = plot_learning_curves(history, [['loss', 'val_loss'],['accuracy', 'val_accuracy']])


lstm_fig = mpl_to_plotly(lstm_fig_)


# HTML
app.layout = html.Div(
    [
        html.H1('Disaster tweet classifier'),
        html.I("Enter a tweet to classify as disaster or non-disaster"),
        html.Br(),
        dcc.Input(
            id="inp_tweet",
            type="text",
            placeholder="Enter a tweet...",
            debounce=True,
            style={
                'width': '98.2%',
                'margin-bottom': '15px',
                'padding': '10px',
                'border-radius': '10px',
                'border-style': 'solid',
            }
        ),
        html.Div(id="output"),
        html.Div([
            html.Div([
                html.Div([
                    html.H4("Logistic Regression")
                ],
                    id="output_lr",
                    style={
                        'background': '#6096ba',
                        'font-size': '20px',
                        'text-align': 'center',
                        'border-radius': '20px',
                        'padding-top': '15px',
                        'padding-bottom': '15px',
                    }
                ),
                html.Button('Logistic Regression Metrics', id='btn-nclicks-1', n_clicks=0, style={'background':'#E2FDFF', 'border-style':'solid', 'border-radius':'10px', 'padding-top':'10px', 'padding-bottom':'10px', 'margin-top':'10px', 'border-color': '#6096ba'}),
            ],style = {
                'width': '30%',
                'display': 'flex',
                'flex-direction': 'column',
            }),
            html.Div([
                html.Div([
                    html.H4("LSTM")
                ],
                    id="output_lstm",
                    style={
                        'background': '#6096ba',
                        'font-size': '20px',
                        'text-align': 'center',
                        'border-radius': '20px',
                        'padding-top': '15px',
                        'padding-bottom': '15px',
                    }
                ),
                html.Button('LSTM Metrics', id='btn-nclicks-2', n_clicks=0, style={'background':'#E2FDFF', 'border-style':'solid', 'border-radius':'10px', 'padding-top':'10px', 'padding-bottom':'10px', 'margin-top':'10px', 'border-color': '#6096ba'}),
            ], style = {
                'width': '30%',
                'display': 'flex',
                'flex-direction': 'column',
            }),
            html.Div([
                html.Div([
                    html.H4("SparkNLP")
                ],
                    id="output_sparknlp",
                    style={
                        'background': '#6096ba',
                        'font-size': '20px',
                        'text-align': 'center',
                        'border-radius': '20px',
                        'padding-top': '15px',
                        'padding-bottom': '15px',
                    }
                ),
                html.Button('SparkNLP Metrics', id='btn-nclicks-3', n_clicks=0, style={'background':'#E2FDFF', 'border-style':'solid', 'border-radius':'10px', 'padding-top':'10px', 'padding-bottom':'10px', 'margin-top':'10px', 'border-color': '#6096ba'}),
            ], style = {
                'width': '30%',
                'display': 'flex',
                'flex-direction': 'column',
            }),
        ], style = {
            'display':'flex',
            'justify-content':'space-between'
        }),
        html.Div([
            html.Div(
                id="output_global",
                style={
                    'background': '#6096ba',
                    'width': '50%',
                    'font-size': '20px',
                    'text-align': 'center',
                    'border-radius': '20px',
                    'padding-top': '15px',
                    'padding-bottom': '15px',
                    'margin-top': '15px',
                }
            ),
        ], style = {
            'display':'flex',
            'justify-content':'center'
        }),
        html.Div([
            
            html.Div(id='container-button-timestamp'),
            # dcc.Graph(
            #     id='learning-curves-lstm',
            #     figure=lstm_fig
            # )
        ])
    ]
)
is_visible = False
@app.callback(
    Output('container-button-timestamp', 'children'),
    Input('btn-nclicks-1', 'n_clicks'),
    Input('btn-nclicks-2', 'n_clicks'),
    Input('btn-nclicks-3', 'n_clicks'),
)

def displayClick(nclicks, nclicks2, nclicks3):
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    if 'btn-nclicks-1' in changed_id:
        if nclicks % 2 == 1:
            return html.Div([
                    html.Div([
                        html.Div([
                            html.H4('F1-Score'),
                            html.H5(f1_lr),
                        ],
                            id="test",
                            style={
                                'background': '#6096ba',
                                'width': '20%',
                                'font-size': '20px',
                                'text-align': 'center',
                                'border-radius': '20px',
                                'padding-top': '5px',
                                'padding-bottom': '5px',
                                'margin-top': '20px',
                            }
                        ),
                        html.Div([
                            html.H4('Precision'),
                            html.H5(precision_lr),
                        ],
                            id="test",
                            style={
                                'background': '#6096ba',
                                'width': '20%',
                                'font-size': '20px',
                                'text-align': 'center',
                                'border-radius': '20px',
                                'padding-top': '5px',
                                'padding-bottom': '5px',
                                'margin-top': '20px',
                                'margin-left': '20px',
                            }
                        ),

                    ], style={
                        'display': 'flex'
                    }),
                    html.Div([
                        html.Div([
                            html.H4('Recall'),
                            html.H5(recall_lr),
                        ],
                            id="test",
                            style={
                                'background': '#6096ba',
                                'width': '20%',
                                'font-size': '20px',
                                'text-align': 'center',
                                'border-radius': '20px',
                                'padding-top': '5px',
                                'padding-bottom': '5px',
                                'margin-top': '20px',
                            }
                        ),
                        html.Div([
                            html.H4('Accuracy'),
                            html.H5(accuracy_lr),
                        ],
                            id="test",
                            style={
                                'background': '#6096ba',
                                'width': '20%',
                                'font-size': '20px',
                                'text-align': 'center',
                                'border-radius': '20px',
                                'padding-top': '5px',
                                'padding-bottom': '5px',
                                'margin-top': '20px',
                                'margin-left': '20px',
                            }
                        ),

                    ], style={
                        'display': 'flex',
                    }),
            ], style={
                'display': 'flex',
                'flex-direction': 'column',
                'padding-left': '37%'
            })

        else:
            return html.Div("")
    elif 'btn-nclicks-2' in changed_id:
        if nclicks2 % 2 == 1:        
            return html.Div([
                html.Div([
                    html.Div([
                        html.Div([
                            html.H4('F1-Score'),
                            html.H5(f1_lstm),
                        ],
                            id="test",
                            style={
                                'background': '#6096ba',
                                'width': '20%',
                                'font-size': '20px',
                                'text-align': 'center',
                                'border-radius': '20px',
                                'padding-top': '5px',
                                'padding-bottom': '5px',
                                'margin-top': '20px',
                            }
                        ),
                        html.Div([
                            html.H4('Precision'),
                            html.H5(precision_lstm),
                        ],
                            id="test",
                            style={
                                'background': '#6096ba',
                                'width': '20%',
                                'font-size': '20px',
                                'text-align': 'center',
                                'border-radius': '20px',
                                'padding-top': '5px',
                                'padding-bottom': '5px',
                                'margin-top': '20px',
                                'margin-left': '20px',
                            }
                        ),

                    ], style={
                        'display': 'flex'
                    }),
                    html.Div([
                        html.Div([
                            html.H4('Recall'),
                            html.H5(recall_lstm),
                        ],
                            id="test",
                            style={
                                'background': '#6096ba',
                                'width': '20%',
                                'font-size': '20px',
                                'text-align': 'center',
                                'border-radius': '20px',
                                'padding-top': '5px',
                                'padding-bottom': '5px',
                                'margin-top': '20px',
                            }
                        ),
                        html.Div([
                            html.H4('Accuracy'),
                            html.H5(accuracy_lstm),
                        ],
                            id="test",
                            style={
                                'background': '#6096ba',
                                'width': '20%',
                                'font-size': '20px',
                                'text-align': 'center',
                                'border-radius': '20px',
                                'padding-top': '5px',
                                'padding-bottom': '5px',
                                'margin-top': '20px',
                                'margin-left': '20px',
                            }
                        ),

                    ], style={
                        'display': 'flex',
                    }),
            ], style={
                'display': 'flex',
                'flex-direction': 'column',
                'padding-left': '37%'
            }),
            html.Div([
                dcc.Graph(
                    id='learning-curves-lstm',
                    figure=lstm_fig,
                    style={
                        'margin-left': '5%'
                    }
                )
            ])
            ])
    elif 'btn-nclicks-3' in changed_id:
        if nclicks3 % 2 == 1:
            return html.Div([
                    html.Div([
                        html.Div([
                            html.H4('F1-Score'),
                            html.H5(f1_snlp),
                        ],
                            id="test",
                            style={
                                'background': '#6096ba',
                                'width': '20%',
                                'font-size': '20px',
                                'text-align': 'center',
                                'border-radius': '20px',
                                'padding-top': '5px',
                                'padding-bottom': '5px',
                                'margin-top': '20px',
                            }
                        ),
                        html.Div([
                            html.H4('Precision'),
                            html.H5(precision_snlp),
                        ],
                            id="test",
                            style={
                                'background': '#6096ba',
                                'width': '20%',
                                'font-size': '20px',
                                'text-align': 'center',
                                'border-radius': '20px',
                                'padding-top': '5px',
                                'padding-bottom': '5px',
                                'margin-top': '20px',
                                'margin-left': '20px',
                            }
                        ),

                    ], style={
                        'display': 'flex'
                    }),
                    html.Div([
                        html.Div([
                            html.H4('Recall'),
                            html.H5(recall_snlp),
                        ],
                            id="test",
                            style={
                                'background': '#6096ba',
                                'width': '20%',
                                'font-size': '20px',
                                'text-align': 'center',
                                'border-radius': '20px',
                                'padding-top': '5px',
                                'padding-bottom': '5px',
                                'margin-top': '20px',
                            }
                        ),
                        html.Div([
                            html.H4('Accuracy'),
                            html.H5(accuracy_snlp),
                        ],
                            id="test",
                            style={
                                'background': '#6096ba',
                                'width': '20%',
                                'font-size': '20px',
                                'text-align': 'center',
                                'border-radius': '20px',
                                'padding-top': '5px',
                                'padding-bottom': '5px',
                                'margin-top': '20px',
                                'margin-left': '20px',
                            }
                        ),

                    ], style={
                        'display': 'flex',
                    }),
            ], style={
                'display': 'flex',
                'flex-direction': 'column',
                'padding-left': '37%'
            })

        else:
            # msg = 'None of the buttons have been clicked yet'
            return html.Div("")
    else:
        # msg = 'None of the buttons have been clicked yet'
        return html.Div("")
    return html.Div("")


def calculate(input):
    print(input)
    pred_lr = -1
    pred_lstm = -1
    pred_sparkNLP = -1
    global_pred = ""

    if input:
        # Logistic Regression
        val_lr = vectorizer.transform([input]).todense()
        pred_lr_list = modelLR.predict(val_lr)

        if len(pred_lr_list) > 0:
            pred_lr = pred_lr_list[0]

        # LSTM
        lstm_format = pad_sequences(embed([input]), length_long_sentence, padding='post')
        pred_lstm = (model.predict(lstm_format) > 0.5 ).astype("int32")
        pred_lstm = int(pred_lstm[0][0])

        # SparkNLP
        spark_columns = ["id", "text"]
        spark_data = [("0", input)]
        rdd = spark.sparkContext.parallelize(spark_data)
        l = spark.createDataFrame(rdd).toDF(*spark_columns)
        spark_prediction = use_model.transform(l)
        predSp = spark_prediction.select("class.result").collect()
        pred_sparkNLP = int(re.sub(r'[^0-9 ]+', '', str(predSp[0])))

        global_pred = (pred_lr + pred_lstm + pred_sparkNLP) / 3
        global_pred = "Disaster" if global_pred >= 0.5 else "Non-disaster"

    return pred_lr, pred_lstm, pred_sparkNLP, global_pred


@app.callback(
    Output("output_lr", "children"),
    Output("output_lstm", "children"),
    Output("output_sparknlp", "children"),
    Output("output_global", "children"),
    Input("inp_tweet", "value"),
)

def update_output(input):
    pred_lr, pred_lstm, pred_sparkNLP, global_pred = calculate(input)

    return (
        'Logistic Regression: \n {}'.format(str(pred_lr)),
        'LSTM: \n {}'.format(str(pred_lstm)),
        'SparkNLP: \n {}'.format(str(pred_sparkNLP)),
        'Global: \n {}'.format(global_pred)
    )


@app.callback(
    Output("output_lr", "style"),
    Input("inp_tweet", "value"),
)

def set_output_lr_style(input):
    pred_lr, pred_lstm, pred_sparkNLP, global_pred = calculate(input)

    response = {
        'background': '#6096ba',
        # 'width': '30%',
        'font-size': '20px',
        'text-align': 'center',
        'border-radius': '20px',
        'padding-top': '15px',
        'padding-bottom': '15px',
    }

    if pred_lr == 0:
        response['background'] = '#55B56A'
        return response
    elif pred_lr == 1:
        response['background'] = '#FF5757'
        return response
    else:
        return response


@app.callback(
    Output("output_lstm", "style"),
    Input("inp_tweet", "value"),
)

def set_output_lstm_style(input):
    pred_lr, pred_lstm, pred_sparkNLP, global_pred = calculate(input)

    response = {
        'background': '#6096ba',
        # 'width': '30%',
        'font-size': '20px',
        'text-align': 'center',
        'border-radius': '20px',
        'padding-top': '15px',
        'padding-bottom': '15px',
    }

    if pred_lstm == 0:
        response['background'] = '#55B56A'
        return response
    elif pred_lstm == 1:
        response['background'] = '#FF5757'
        return response
    else:
        return response

@app.callback(
    Output("output_sparknlp", "style"),
    Input("inp_tweet", "value"),
)

def set_output_sparknlp_style(input):
    pred_lr, pred_lstm, pred_sparkNLP, global_pred = calculate(input)

    response = {
        'background': '#6096ba',
        # 'width': '30%',
        'font-size': '20px',
        'text-align': 'center',
        'border-radius': '20px',
        'padding-top': '15px',
        'padding-bottom': '15px',
    }

    if pred_sparkNLP == 0:
        response['background'] = '#55B56A'
        return response
    elif pred_sparkNLP == 1:
        response['background'] = '#FF5757'
        return response
    else:
        return response


@app.callback(
    Output("output_global", "style"),
    Input("inp_tweet", "value"),
)

def set_output_global_style(input):
    pred_lr, pred_lstm, pred_sparkNLP, global_pred = calculate(input)

    response = {
        'background': '#6096ba',
        'width': '50%',
        'font-size': '20px',
        'text-align': 'center',
        'border-radius': '20px',
        'padding-top': '15px',
        'padding-bottom': '15px',
        'margin-top': '15px',
    }

    if global_pred == "Non-disaster":
        response['background'] = '#55B56A'
        return response
    elif global_pred == "Disaster":
        response['background'] = '#FF5757'
        return response
    else:
        return response


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=False)
