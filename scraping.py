import requests
import re
import time
import os

# 条件
year = 2020  # 2020/12/31以前
minimum = 3000  # 3000戦以上
sctype = 'c'  # 段位戦
playernum = 4  # 四麻
playerlevel = 3  # 鳳凰卓
playlength = 2  # 東南戦
kuitanari = 1  # クイタンあり
akaari = 1  # 赤あり

# プレーヤー名
playerName = []
playerUni = []
with open('Tenhou/Research/log/players.csv', encoding='utf-8') as f:
    playerName = f.read().splitlines()
for i in range(len(playerName)):
    playerUni.append(str(playerName[i].encode('unicode_escape')))
    playerUni[i] = playerUni[i][2:-1].replace('\\\\u', '\\u')

# 席順を判定
def judgeTw(tw, rank):
    for i in range(4):
        try:
            if (tw >> (i << 1)) & 3 == rank - 1:
                return i
                break
        except:
            return ''

# スクレイピング
def getUrls(playerNum, sctype, playernum, playerlevel, playlength, kuitanari, akaari):
    # 情報を取得
    res = requests.get('https://nodocchi.moe/api/listuser.php?name=' + playerName[playerNum]).text
    # time.sleep(10)
    # リストを作成
    res = res.replace('{\"list\":[{\"', '')
    res = re.sub('}],\"name\":\".*]]}', '', res)
    info = res.split('},{\"')
    for i in range(len(info)):
        info[i] = re.split('\"[:,]\"', info[i])
    # 情報を抽出
    log = []
    for i in range(len(info)):
        tmp = ['', '', '', '', '', '', '', '', '']
        for j in range(len(info[i])):
            if info[i][j] == 'sctype':  # 対戦タイプ
                tmp[0] = info[i][j+1]
            if info[i][j] == 'playernum':  # 人数
                tmp[1] = int(info[i][j+1])
            if info[i][j] == 'playerlevel':  # 卓
                tmp[2] = int(info[i][j+1])
            if info[i][j] == 'playlength':  # 長さ
                tmp[3] = int(info[i][j+1])
            if info[i][j] == 'kuitanari':  # クイタン
                tmp[4] = int(info[i][j+1])
            if info[i][j] == 'akaari':  # 赤
                tmp[5] = int(info[i][j+1])
            if info[i][j] == playerUni[playerNum]:  # 順位
                try:
                    tmp[6] = int(info[i][j-1][-1:])
                except:
                    pass
            if info[i][j] == 'url':  # 牌譜url
                try:
                    tmp[7] = str(info[i][j+1].replace('\\', '').replace('\"','').replace('http:', 'https:').replace('/3/', '/0/'))
                except:
                    pass
            if info[i][j] == 'tw':  # 席順
                try:
                    tmp[8] = int(info[i][j+1].replace('\"', ''))
                except:
                    pass
        log.append(tmp)
    # 牌譜urlを抽出
    paifu = []
    for i in range(len(log)):
        if log[i][0] == sctype and log[i][1] == playernum and log[i][2] == playerlevel and log[i][3] == playlength and log[i][4] == kuitanari and log[i][5] == akaari:
            tw = log[i][8]
            rank = log[i][6]
            paifu.append(log[i][7] + '&tw=' + str(judgeTw(tw, rank)))
    return paifu

# 出力
def output(paifu, minimum, year):
    array = []
    for i in range(len(paifu)):
        if int(paifu[i][26:30]) <= year:
            array.append(paifu[i])
    paifu = array
    if len(paifu) >= minimum:
        if not os.path.exists('Tenhou/Research/log/鳳凰卓/' + str(playerName[playerNum])):
            os.makedirs('C:/Users/isoko/Documents/Tenhou/Research/log/鳳凰卓/' + str(playerName[playerNum]))
        try:
            with open('Tenhou/Research/log/鳳凰卓/' + str(playerName[playerNum]) + '/' + str(playerName[playerNum]) + '.csv', 'w', newline='', encoding='utf_8') as g:
                g.writelines('\n'.join(paifu))
        except:
            pass

# 実行
for playerNum in range(len(playerName)):
    paifu = getUrls(playerNum, sctype, playernum, playerlevel, playlength, kuitanari, akaari)
    output(paifu, minimum, year)
print('done')
