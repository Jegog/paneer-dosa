import MeCab
import fitz
import re

#---------------------------------------------------------------------------------------------------
#除外文字列を記載したテキストファイルを読み込み
def load_exclusion_list(file_path):
    exclusion_list = []
    try:
        with open(file_path, 'r') as file:
            exclusion_list = [line.strip() for line in file]
    except FileNotFoundError:
        pass
    return exclusion_list
#---------------------------------------------------------------------------------------------------
#形態素解析の前に、無駄な記号やヘッダ・フッタ等の文言をテキストから除外
def noise_eliminator(text):

    replaced_text = text

    #exclusion_list処理前に処理する必要のあるもの
    #【特例処理】除外処理前に、文頭のこれら記号は「箇条書き」とみなし、続く文言を一文として扱う
    replaced_text = re.sub(r'[■□▪▫▲△▶▷▸▹▼▽◆◇●〇]', '。\n', replaced_text)
    #replaced_text = re.sub(r'[〇●◇◆□■▶△▲▽▼▫▪▹▶▸]', '', replaced_text)#上記以外は除去

    exclusion_list = []    
    exclusion_file1 = "userdic/exclusion_phrases1.txt"  # 各企業の除外フレーズを記載したリスト
    exclusion_file2 = "userdic/exclusion_phrases2.txt"  # 各企業の除外フレーズを記載したリスト2（pageinfoから都度取り込み）
    exclusion_file3 = "userdic/exclusion_codes.txt"  # その他記号・年月日・URL等を除外するためのリスト
    exclusion_list = load_exclusion_list(exclusion_file1) + load_exclusion_list(exclusion_file2)+ load_exclusion_list(exclusion_file3)

    for pattern in exclusion_list:
        replaced_text = re.sub(pattern, ' ', replaced_text)

    return replaced_text
#---------------------------------------------------------------------------------------------------
#形態素解析関数（入力：テキスト、出力：リスト）
def mecab_tokenizer(text):

    path1 = "-Ochasen -d /usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd"
    path2 = " -u /work_dir/userdic/user.dic"
    mecab = MeCab.Tagger(path1+path2)
   
    parsed_lines = mecab.parse(text).split("\n")[:-2]    #[:-2]で文末の'EOS',''の取り込みを抑制
    
    #形態素の取得（リスト形式）
    
    token_list = [l.split("\t")[2] for l in parsed_lines]#原形を取得
    #token_list = [l.split('\t')[0] for l in parsed_lines]#表層形を確認したい場合
    
    
    #--------------------------------------------
    #品詞区分による絞り込み：Chasenの品詞区分を個別に指定する場合
    #品詞区分の取得（リスト形式）
    pos = [l.split('\t')[3] for l in parsed_lines]

    #抽出する品詞区分の定義（完全一致で指定）
    target_pos = ['名詞-一般',
                  '名詞-固有名詞-一般',
                  '名詞-固有名詞-人名-一般',
                  '名詞-固有名詞-人名-姓',
                  '名詞-固有名詞-人名-名',
                  '名詞-固有名詞-組織',
                  '名詞-固有名詞-地域-一般',
                  '名詞-固有名詞-地域-国',
                  '名詞-代名詞-一般',
                  '名詞-代名詞-縮約',
                  '名詞-副詞可能',
                  '名詞-サ変接続',
                  '名詞-形容動詞語幹',
                  '名詞-ナイ形容詞語幹'
                 ]
    #--------------------------------------------
    #形態素と品詞区分のリストをペアにしてタプルリスト化、該当する品詞区分の形態素のみリストに出力
    token_list = [t for t, p in zip(token_list, pos) if p in target_pos]
    
    #--------------------------------------------
    #stopwordsの処理
    stopwords = []
    #stopwordsファイルを読み込み
    with open("userdic/stopwords.txt","r") as f:
        stopwords1 = f.read().split("\n")
    stopwords.extend(stopwords1)

    # 元の順序を保持しつつ、stopwordの重複を除去（# Python 3.7以降）
    from collections import OrderedDict
    stopwords = list(OrderedDict.fromkeys(stopwords))
    
    # stopwordsを除去
    token_list = [t for t in token_list if t  not in stopwords]

    #--------------------------------------------
    # ひらがなのみの形態素を除外
    kana_re = re.compile("^[ぁ-ゖ]+$")
    token_list = [t for t in token_list if not kana_re.match(t)]

    # アルファベット1文字のみの形態素を除外
    alphabet_re = re.compile("^[a-zA-Z]$")
    token_list = [t for t in token_list if not alphabet_re.match(t)]

    #Neolondの辞書の出力結果を補正
    replacement_dict = {}
    with open("userdic/dic_correction.txt","r") as fc:
        correction_list = fc.read()
    for line in correction_list.split("\n"):
        old, new = line.split("\t")
        replacement_dict[old] = new
    #辞書出力を置換マッピングを使って更新
    token_list = [replacement_dict.get(item, item) for item in token_list]
    
    return token_list