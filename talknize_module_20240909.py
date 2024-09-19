#Mecabによる形態素解析器と除外文字列（形態素解析前）、置換文字列（形態素解析後）の処理
import MeCab
import fitz
import re
from collections import OrderedDict

#--------------------------------------------------------------------------------------
#形態素解析モジュール
#--------------------------------------------------------------------------------------
def mecab_tokenizer(text):

    #辞書の定義
    path_dic1 = "-Ochasen -d /usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd"
    path_dic2 = " -u /work_dir/userdic/user.dic"

    path_stopwords = "userdic/stopwords.txt"
    path_dic_correction = "userdic/dic_correction.txt"
    
    #除外要素の定義
    #stopwordsの処理
    stopwords = []
    #stopwordsファイルを読み込み
    with open(path_stopwords,"r") as fs:
        stopwords1 = fs.read().split("\n")
    stopwords.extend(stopwords1)
    stopwords = list(OrderedDict.fromkeys(stopwords))# 元の順序を保持しつつ、重複を除去（# Python 3.7以降）

    #Neolondの辞書に対する補正要素
    replacement_dict = {}
    with open(path_dic_correction,"r") as fc:
        correction_list = fc.read()
    for line in correction_list.split("\n"):
        old, new = line.split("\t")
        replacement_dict[old] = new

    #ひらがなのみの要素
    kana_re = re.compile("^[ぁ-ゖ]+$")
    # アルファベット1文字のみの要素
    alphabet_re = re.compile("^[a-zA-Z]$")

    #形態素解析器の適用
    mecab = MeCab.Tagger(path_dic1 + path_dic2)
    parsed_lines = mecab.parse(text).split("\n")[:-2]    #[:-2]で文末の'EOS',''の取り込みを抑制
	# textの文末に'EOS'と''があるかをチェック
    #if text.endswith('EOS\n'):#or text.endswith('\n'):
	#    parsed_lines = mecab.parse(text).split("\n")[:-2] 
    #else:
    #    parsed_lines = mecab.parse(text).split("\n") 

    
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
                  '名詞-数',#LESJ2024では除外＃
                  '名詞-ナイ形容詞語幹'
                 ]
    #--------------------------------------------
    #該当する品詞区分の形態素のみリストに出力:形態素と品詞区分のリストをペアでタプルリスト化、該当する品詞区分の形態素のみリストに出力
    token_list = [t for t, p in zip(token_list, pos) if p in target_pos]
    
    #Neolondの辞書の出力結果を補正
    token_list = [replacement_dict.get(item, item) for item in token_list]

    # stopwordsを除去
    #token_list = [t for t in token_list if t  not in stopwords]
    # ひらがなのみの形態素を除外
    #token_list = [t for t in token_list if not kana_re.match(t)]
    # アルファベット1文字のみの形態素を除外
    #token_list = [t for t in token_list if not alphabet_re.match(t)]
    
    return token_list

#----------------------------------------------------------------------
#テキストファイルの各行に記載された文字列を、処理用文字列として整形・リスト化
# テキストの前処理に利用
def text_to_list(file_path):

    # 空のリストを作成
    return_list = []
    try:
        # 指定されたファイルを読み込み、各行をリストに追加
        with open(file_path, 'r') as file:
            # ファイル内の各行をループし、行末の改行や余分な空白を除去してリストに格納
            return_list = [line.strip() for line in file]
    # ファイルが存在しない場合は例外を無視する
    except FileNotFoundError:
        pass
    # リストを返す
    return return_list

#----------------------------------------------------------------------
#形態素解析前のテキストデータ処理
#形態素解析の前に、無駄な記号やヘッダ・フッタ等の文言をテキストから除外
def pre_tk(text):

    replaced_text = text

    #exclusion_list処理前に処理する必要のあるもの
    #【特例処理】除外処理前に、文頭のこれら記号は「箇条書き」とみなし、続く文言を一文として扱う
    replaced_text = re.sub(r'[■□▪▫▲△▶▷▸▹▼▽◆◇●〇]', '。\n', replaced_text)
    #replaced_text = re.sub(r'[〇●◇◆□■▶△▲▽▼▫▪▹▶▸]', '', replaced_text)#上記以外は除去

    exclusion_list = []    
    exclusion_file1 = "userdic/exclusion_phrases1.txt"  # 各企業の除外フレーズを記載したリスト
    exclusion_file2 = "userdic/exclusion_phrases2.txt"  # 各企業の除外フレーズを記載したリスト2（pageinfoから都度取り込み）
    exclusion_file3 = "userdic/exclusion_codes.txt"  # その他記号・年月日・URL等を除外するためのリスト
    exclusion_list = text_to_list(exclusion_file1) + text_to_list(exclusion_file2)+ text_to_list(exclusion_file3)

    for pattern in exclusion_list:
        replaced_text = re.sub(pattern, ' ', replaced_text)

    return replaced_text


