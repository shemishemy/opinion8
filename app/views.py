# app/views.py

from django.shortcuts import render, get_object_or_404
from .models import FileUpload
from django_pandas.io import pd
from django.http import HttpResponseRedirect
from .forms import UploadFileForm
import openpyxl
"""from somewhere import handle_uploaded_file"""

from janome.tokenizer import Tokenizer
import re
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numexpr
import json
from requests_oauthlib import OAuth1Session
from collections import Counter

def index(request):
    """
    トップページ
    """
    file_obj = FileUpload.objects.all()
    context = {
            'file_obj': file_obj,
    }
    return render(request, 'app/index.html', context)

def detail(request, pk):
    """
    詳細ページ
    """
    file_value = get_object_or_404(FileUpload, id=pk)
    df = pd.read_csv(file_value.upload_dir.path, index_col=0)
    context = {
            'file_value': file_value,
            'df': df,
    }
    return render(request, 'app/detail.html', context)

"""def upload(request):
    if request.method == 'POST':
        f = UploadFileForm(request.POST)
    else:
        f = UploadFileForm()
    return render(request, 'app/upload.html', {'form1': f})"""

with open('app/Japanese.txt', 'r', encoding = 'utf-8') as f:
    stopwords = [w.strip() for w in f] #改行記号の除去
    stopwords = set(stopwords)         #集合に変換

def clean_hashtag(text):
    cleaned_text = re.sub(r'( #[a-zA-Z]+)+$', '', text)         #文末のハッシュタグを消す
    cleaned_text = re.sub(r'#([a-zA-Z]+)', r'\1', cleaned_text) #文中のハッシュタグの'#'を消す
    return cleaned_text

def clean_space(text): #空白、改行を消す
    cleaned_text = re.sub(' ', '', text)
    cleaned_text = re.sub('　', '', cleaned_text)
    cleaned_text = re.sub('\n', '', cleaned_text)
    return cleaned_text

def clean_url(text): #URLを消す
    cleaned_text = re.sub(r'(https?|ftp)(:\/\/[-_.!~*\'()a-zA-Z0-9;\/?:\@&=+\$,%#]+)', '', text)
    return cleaned_text

def clean_name(text): #IDを消す
    cleaned_text = re.sub(r'@[a-zA-Z0-9_]+', '', text)
    return cleaned_text

def normalize_number(text): #数字を0にする
    replaced_text = re.sub(r'\d+', '0', text)
    return replaced_text

def upload(request):
    context = {}
    if request.method == 'POST' and request.FILES.get('csv'):
        csv = request.FILES.get('csv', "r")
        #csvの読み込み
        df = pd.read_csv(csv)
        df_s = df.sort_values(["Place", "About"])

        df_dict = {}
        text_list = {}
        i_opinion_list = {}
        r_urls = {}
        
        t = Tokenizer(wakati = 'true')
        for name, group in df_s.groupby('Place'):
            df_dict[name] = group
            text_list[name] = []
            opinion_list = []
            o_opinion_list = []
            r_url = {}
            #abc = []
            for text in df_dict[name].How:
                #text_list[name].append(text)
            #for text in text_list[name]:
                text = str(text)
                o_opinion_list.append(text)
                text = clean_hashtag(text)
                text = clean_space(text)
                text = clean_url(text)
                text = clean_name(text)
                text = normalize_number(text)
                text.lower() #小文字化
                words = ''
                for token in t.tokenize(text):
                    if not token in stopwords:
                        words = words + token + ' '
                        #abc.append(token)
                opinion_list.append(words)
            #print(opinion_list)

            #ツイッター
            char = request.POST['char']
            tweet_list = [] #ここにデータを準備
            url_list = []
            # OAuth認証部分
            CK      = '5FAj5as2hzq6M8cgNNuy8SDvf'
            CS      = 'N3YAcLIftOXMZ1NuIkjHyc0XlTAKgDfUFTlhLay4Xl3ysLZlng'
            AT      = '1309382412036521984-SX7mZKjxr6fRotxjI7WPmkojPG5oFW'
            ATS     = 'VHmtGtdEOWZ08YgeL5BqrFzcxJDeWMxl1mubcZulSblbO'
            twitter = OAuth1Session(CK, CS, AT, ATS)
            # Twitter Endpoint(検索結果を取得する)
            url = 'https://api.twitter.com/1.1/tweets/search/fullarchive/development.json'
            # Enedpointへ渡すパラメーター
            keyword = char + ' ' + name
            #print(keyword)
            params ={
                    'query' : keyword ,  # 検索キーワード
                    'maxResults': 100 ,   # 取得するtweet数
                    #'fromDate' : 202101311500 ,
                    #'toDate' : 202102011500
                    }
            req = twitter.get(url, params = params)

            if req.status_code == 200:
                res = json.loads(req.text)
                for line in res['results']:
                    url_list.append('https://twitter.com/'+line['user']['screen_name']+'/status/'+line['id_str'])
                    text = line['text']
                    text = clean_hashtag(text)
                    text = clean_space(text)
                    text = clean_url(text)
                    text = clean_name(text)
                    text = normalize_number(text)
                    text.lower() #小文字化
                    #print(line['text'])
                    #print('*******************************************')
                    words = ''
                    for token in t.tokenize(text):
                        if not token in stopwords:
                            words = words + token + ' '
                            #abc.append(token)
                    tweet_list.append(words)
            else:
                print("Failed: %d" % req.status_code)
            #print(tweet_list)

            #fdist = Counter(abc)
            #print(fdist.most_common(n=30))

            word_list = opinion_list + tweet_list
            vectorizer = TfidfVectorizer()
            word_vec = vectorizer.fit_transform(word_list)
            df_vec = pd.DataFrame(word_vec.toarray())
            opinion_vec = df_vec.iloc[:len(opinion_list),:]
            tweet_vec = df_vec.iloc[len(opinion_list):,:]

            word_list = opinion_list + tweet_list
            #print(tweet_list)
            vectorizer = TfidfVectorizer()
            word_vec = vectorizer.fit_transform(word_list)
            df_vec = pd.DataFrame(word_vec.toarray())
            opinion_vec = df_vec.iloc[:len(opinion_list),:]
            tweet_vec = df_vec.iloc[len(opinion_list):,:]

            cosim = pd.DataFrame(cosine_similarity(opinion_vec,tweet_vec))
            print(cosim)
    
            counters = []
            for index in cosim.index:
        
                counter = 0
                for column in cosim.columns:
            
                    if cosim.at[index, column] > 0.05:
                        counter += 1
                counters.append(counter)
            print(counters)
            counters_i = [i for i, v in enumerate(counters) if v == max(counters)]
            print(counters_i)
            i_opinion_list[name] = []
            for i in counters_i:
                i_opinion_list[name].append(o_opinion_list[i])
                r_tweets = (sorted(cosim.T[i].items(), key=lambda x: x[1], reverse=True)[:2])
            for opinion in i_opinion_list[name]:
                r_url[opinion] = []
                for j in r_tweets:
                    r_url[opinion].append(url_list[j[0]])
            r_urls[name] = []
            r_urls[name].append(r_url)
            print(i_opinion_list)
        context = {'df':df_s, 'i_opinion_list':i_opinion_list, 'r_urls':r_urls}

    return render(request, 'app/upload.html', context)