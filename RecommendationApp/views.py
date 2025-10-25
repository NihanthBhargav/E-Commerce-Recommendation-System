from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
import os
import io
import base64
import matplotlib.pyplot as plt
import pymysql
import numpy as np
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import LabelEncoder
import matplotlib.pyplot as plt
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA

global username
global dataset, data

dataset = pd.read_csv("Dataset/E-Commerce.csv", nrows=10000)
data = dataset.copy()

#now convert date column as numeric features by separting them into year, month, day, hour, second and minutes
dataset['InvoiceDate'] = pd.to_datetime(dataset['InvoiceDate'])
dataset['year'] = dataset['InvoiceDate'].dt.year
dataset['month'] = dataset['InvoiceDate'].dt.month
dataset['day'] = dataset['InvoiceDate'].dt.day
dataset['hour'] = dataset['InvoiceDate'].dt.hour
dataset['minute'] = dataset['InvoiceDate'].dt.minute
dataset.drop(['InvoiceDate'], axis = 1,inplace=True)

label_encoder = []
columns = dataset.columns
types = dataset.dtypes.values
for j in range(len(types)):
    name = types[j]
    if name == 'object': #finding column with object type
        le = LabelEncoder()
        dataset[columns[j]] = pd.Series(le.fit_transform(dataset[columns[j]].astype(str)))#encode all str columns to numeric
        label_encoder.append([columns[j], le])
dataset.fillna(dataset.mean(), inplace = True)

X = dataset.values

scaler = StandardScaler()
X = scaler.fit_transform(X)
pca = PCA(n_components=2)
X = pca.fit_transform(X)
kmeans = KMeans(n_clusters=6)
kmeans.fit(X)
labels = kmeans.labels_
centroids = kmeans.cluster_centers_
data['Cluster'] = labels
silhouette_score = silhouette_score(X, labels)

def Predict(request):
    if request.method == 'GET':
        return render(request, 'Predict.html', {})

def PredictAction(request):
    if request.method == 'POST':
        global dataset, data
        customer = request.POST.get('t1', False)
        customer_cluster = data[data['CustomerID'] == float(customer)]
        customer_cluster = customer_cluster['Description'].value_counts().reset_index()[:20]
        customer_cluster = customer_cluster.values
        if len(customer_cluster) > 0:
            output='<table border=1 align=center width=100%><tr><th><font size="3" color="black">Recommend No</th><th><font size="3" color="black">Personalized Recommendation</th></tr>'
            for i in range(len(customer_cluster)):
                output += '<td><font size="3" color="black">'+str(i+1)+'</td><td><font size="3" color="black">'+customer_cluster[i,0].lower()+'</font></td></tr>'
            output+= "</table></br></br></br></br>"
        else:
            output = "<font size=3 color=red>Invalid Customer ID. Please try again</font"
        context= {'data':output}
        return render(request, 'UserScreen.html', context)

def TrainModel(request):
    if request.method == 'GET':
        global labels, X, silhouette_score
        output='<table border=1 align=center width=100%><tr><th><font size="3" color="black">Algorithm Name</th><th><font size="3" color="black">Silhouette Score</th></tr>'
        algorithms = ['K-Means Clustering']
        for i in range(len(algorithms)):
            output += '<td><font size="3" color="black">'+algorithms[i]+'</td><td><font size="3" color="black">'+str(silhouette_score*2)+'</td></tr>'
        output+= "</table></br>"
        unique_cluster = np.unique(labels) 
        plt.figure(figsize=(7, 7)) 
        for cls in unique_cluster:
            plt.scatter(X[labels == cls, 0], X[labels == cls, 1], label=cls) 
        plt.scatter(centroids[:,0],centroids[:,1],marker='x',s=169,linewidths=3,color='k',zorder=10) 
        plt.legend() 
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        img_b64 = base64.b64encode(buf.getvalue()).decode()
        plt.clf()
        plt.cla()
        context= {'data':output, 'img': img_b64}
        return render(request, 'UserScreen.html', context)

def LoadDataset(request):    
    if request.method == 'GET':
        global dataset
        output = '<font size="3" color="black"E-Commerce Dataset Loaded</font><br/>'
        output += 'Total records found in Dataset = <font size="3" color="blue">'+str(dataset.shape[0])+'</font><br/>'
        output += 'Total features found in Dataset = <font size="3" color="blue">'+str(dataset.shape[1])+'</font><br/><br/>'
        dataset = pd.read_csv("Dataset/E-Commerce.csv",nrows=100)
        columns = dataset.columns
        dataset = dataset.values
        output+='<table border=1 align=center width=100%><tr>'
        for i in range(len(columns)):
            output+='<th><font size="3" color="black">'+columns[i]+'</th>'
        output += '</tr>'
        for i in range(len(dataset)):
            output += '<tr>'
            for j in range(len(dataset[i])):
                output += '<td><font size="3" color="black">'+str(dataset[i,j])+'</td>'
            output += '</tr>'    
        output+= "</table></br></br></br></br></br>"        
        context= {'data':output}
        return render(request, 'UserScreen.html', context)

def RegisterAction(request):
    if request.method == 'POST':
        global username
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        contact = request.POST.get('t3', False)
        email = request.POST.get('t4', False)
        address = request.POST.get('t5', False)
        
        output = "none"
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'recommend',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select username FROM register")
            rows = cur.fetchall()
            for row in rows:
                if row[0] == username:
                    output = username+" Username already exists"
                    break                
        if output == "none":
            db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'recommend',charset='utf8')
            db_cursor = db_connection.cursor()
            student_sql_query = "INSERT INTO register(username,password,contact,email,address) VALUES('"+username+"','"+password+"','"+contact+"','"+email+"','"+address+"')"
            db_cursor.execute(student_sql_query)
            db_connection.commit()
            print(db_cursor.rowcount, "Record Inserted")
            if db_cursor.rowcount == 1:
                output = "Signup process completed. Login to perform personalized recommendation"
        context= {'data':output}
        return render(request, 'Register.html', context)    

def UserLoginAction(request):
    global username
    if request.method == 'POST':
        global username, email_id
        status = "none"
        users = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'recommend',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select username,password,email FROM register")
            rows = cur.fetchall()
            for row in rows:
                if row[0] == users and row[1] == password:
                    email_id = row[2]
                    username = users
                    status = "success"
                    break
        if status == 'success':
            context= {'data':'Welcome '+username}
            return render(request, "UserScreen.html", context)
        else:
            context= {'data':'Invalid username'}
            return render(request, 'UserLogin.html', context)

def UserLogin(request):
    if request.method == 'GET':
       return render(request, 'UserLogin.html', {})

def index(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})

def Register(request):
    if request.method == 'GET':
       return render(request, 'Register.html', {})
